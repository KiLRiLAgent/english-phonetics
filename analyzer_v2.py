#!/usr/bin/env python3
"""
English Pronunciation Analyzer v2
Core product: reference comparison + confidence scoring + color-coded HTML report.
"""

import os
import sys
import json
import re
import difflib
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings("ignore")

from rich.console import Console

console = Console()

# Number words → digits mapping (Whisper artifact filter)
NUM_MAP = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20",
}
NUM_REVERSE = {v: k for k, v in NUM_MAP.items()}


def normalize_word(w: str) -> str:
    """Normalize a word for comparison."""
    w = re.sub(r"[^\w]", "", w.lower().strip())
    # Convert digit strings back to words for comparison
    if w in NUM_REVERSE:
        w = NUM_REVERSE[w]
    return w


def word_similarity(a: str, b: str) -> float:
    """Calculate similarity between two words (0-1)."""
    a, b = normalize_word(a), normalize_word(b)
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def transcribe_with_words(audio_path: str, model=None, model_size: str = "base") -> dict:
    """Transcribe audio with word-level timestamps and confidence."""
    import whisper

    if model is None:
        model = whisper.load_model(model_size)

    result = model.transcribe(str(audio_path), language="en", word_timestamps=True)

    words = []
    for seg in result.get("segments", []):
        for wi in seg.get("words", []):
            words.append({
                "word": wi.get("word", "").strip(),
                "start": round(wi.get("start", 0), 3),
                "end": round(wi.get("end", 0), 3),
                "confidence": round(wi.get("probability", 0.0), 3),
            })

    return {
        "text": result.get("text", "").strip(),
        "words": words,
    }


def align_words(ref_text: str, hyp_words: list) -> list:
    """
    Align reference words with hypothesis words using dynamic programming.
    Minimizes edit distance while considering phonetic similarity.
    """
    ref_tokens = re.sub(r"[^\w\s]", "", ref_text.lower()).split()
    hyp_normalized = [normalize_word(w["word"]) for w in hyp_words]

    n = len(ref_tokens)
    m = len(hyp_normalized)

    # DP matrix: cost[i][j] = min cost to align ref[:i] with hyp[:j]
    INF = float('inf')
    cost = [[INF] * (m + 1) for _ in range(n + 1)]
    backtrack = [[None] * (m + 1) for _ in range(n + 1)]

    cost[0][0] = 0
    for i in range(1, n + 1):
        cost[i][0] = i * 1.0  # deletion cost
        backtrack[i][0] = "del"
    for j in range(1, m + 1):
        cost[0][j] = j * 1.0  # insertion cost
        backtrack[0][j] = "ins"

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sim = word_similarity(ref_tokens[i-1], hyp_normalized[j-1])

            # Match/substitute cost: 0 for exact match, scaled by dissimilarity
            if sim == 1.0:
                sub_cost = 0.0
            elif sim >= 0.6:
                sub_cost = 0.3  # similar words — likely pronunciation error
            else:
                sub_cost = 1.0  # very different words

            options = [
                (cost[i-1][j-1] + sub_cost, "match" if sim == 1.0 else "sub"),
                (cost[i-1][j] + 1.0, "del"),   # ref word deleted
                (cost[i][j-1] + 1.0, "ins"),    # extra hyp word
            ]

            best_cost, best_op = min(options, key=lambda x: x[0])
            cost[i][j] = best_cost
            backtrack[i][j] = best_op

    # Traceback
    aligned = []
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and backtrack[i][j] in ("match", "sub"):
            hw = hyp_words[j-1]
            sim = word_similarity(ref_tokens[i-1], hyp_normalized[j-1])
            if sim == 1.0:
                status = "correct"
            else:
                status = "substitution"

            aligned.append({
                "ref_word": ref_tokens[i-1],
                "hyp_word": hw["word"],
                "status": status,
                "confidence": hw["confidence"],
                "start": hw["start"],
                "end": hw["end"],
            })
            i -= 1
            j -= 1
        elif i > 0 and (j == 0 or backtrack[i][j] == "del"):
            # Deletion: ref word not spoken.
            # Try to borrow timing from nearest hyp word
            near_start = hyp_words[j-1]["start"] if j > 0 else (hyp_words[j]["start"] if j < m else None)
            near_end = hyp_words[j-1]["end"] if j > 0 else (hyp_words[j]["end"] if j < m else None)
            aligned.append({
                "ref_word": ref_tokens[i-1],
                "hyp_word": None,
                "status": "deletion",
                "confidence": 0,
                "start": near_start,
                "end": near_end,
            })
            i -= 1
        elif j > 0 and (i == 0 or backtrack[i][j] == "ins"):
            hw = hyp_words[j-1]
            aligned.append({
                "ref_word": None,
                "hyp_word": hw["word"],
                "status": "insertion",
                "confidence": hw["confidence"],
                "start": hw["start"],
                "end": hw["end"],
            })
            j -= 1
        else:
            break

    aligned.reverse()
    return aligned


def score_word(alignment: dict) -> dict:
    """
    Score a word: combine alignment status + confidence.
    Returns color (green/yellow/red) and score 0-100.
    """
    status = alignment["status"]
    conf = alignment["confidence"]

    if status == "correct":
        if conf >= 0.85:
            return {"score": 100, "color": "green", "level": "excellent"}
        elif conf >= 0.65:
            return {"score": 70, "color": "yellow", "level": "acceptable"}
        else:
            return {"score": 40, "color": "red", "level": "unclear"}
    elif status == "substitution":
        return {"score": 10, "color": "red", "level": "wrong_word"}
    elif status == "deletion":
        return {"score": 0, "color": "red", "level": "skipped"}
    elif status == "insertion":
        return {"score": 30, "color": "yellow", "level": "extra_word"}

    return {"score": 50, "color": "yellow", "level": "unknown"}


def extract_audio_segment(audio_path: str, start: float, end: float, output_path: str):
    """Extract audio segment using soundfile."""
    import soundfile as sf
    import numpy as np

    data, sr = sf.read(audio_path)
    start_sample = int(start * sr)
    end_sample = int(end * sr)

    # Add small padding
    pad = int(0.1 * sr)
    start_sample = max(0, start_sample - pad)
    end_sample = min(len(data), end_sample + pad)

    segment = data[start_sample:end_sample]
    sf.write(output_path, segment, sr)


def generate_html_report(
    audio_path: str,
    reference: str,
    aligned_words: list,
    scored_words: list,
    output_dir: Path,
) -> str:
    """Generate interactive HTML report with color-coded words."""

    audio_name = Path(audio_path).stem

    # Build word spans
    word_spans = []
    for aw, sw in zip(aligned_words, scored_words):
        display_word = aw["ref_word"] or aw["hyp_word"] or "?"
        color = sw["color"]
        level = sw["level"]
        conf = aw["confidence"]
        start = aw.get("start")
        end = aw.get("end")

        css_class = f"word-{color}"
        if aw["status"] == "substitution":
            display_word = aw["ref_word"]
        elif aw["status"] == "deletion":
            css_class += " word-deleted"

        data_attrs = f'data-ref="{aw["ref_word"] or ""}" data-hyp="{aw["hyp_word"] or ""}" '
        data_attrs += f'data-status="{aw["status"]}" data-conf="{conf}" '
        if start is not None:
            data_attrs += f'data-start="{start}" data-end="{end}"'

        word_spans.append(
            f'<span class="word-wrap"><span class="{css_class}" {data_attrs} '
            f'onclick="handleWordClick(this)">{display_word}</span></span>'
        )

    words_html = " ".join(word_spans)

    # Stats
    total = len(scored_words)
    green = sum(1 for s in scored_words if s["color"] == "green")
    yellow = sum(1 for s in scored_words if s["color"] == "yellow")
    red = sum(1 for s in scored_words if s["color"] == "red")
    overall = sum(s["score"] for s in scored_words) / max(total, 1)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pronunciation Report — {audio_name}</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           max-width: 800px; margin: 0 auto; padding: 20px; background: #1a1a2e; color: #eee; }}
    h1 {{ color: #e94560; margin-bottom: 10px; }}
    h2 {{ color: #0f3460; margin: 20px 0 10px; }}
    .score-card {{
        display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap;
    }}
    .score-box {{
        background: #16213e; border-radius: 12px; padding: 20px; flex: 1; min-width: 150px;
        text-align: center;
    }}
    .score-box .number {{ font-size: 36px; font-weight: bold; }}
    .score-box .label {{ font-size: 14px; color: #888; margin-top: 5px; }}
    .score-green .number {{ color: #4ecca3; }}
    .score-yellow .number {{ color: #f0c040; }}
    .score-red .number {{ color: #e94560; }}
    .score-overall .number {{ color: #e94560; font-size: 48px; }}

    .transcript {{
        background: #16213e; border-radius: 12px; padding: 24px;
        margin: 20px 0; line-height: 2.8; font-size: 18px;
        position: relative;
    }}
    .word-wrap {{
        position: relative; display: inline-block;
    }}
    .word-green {{
        background: rgba(78, 204, 163, 0.2); color: #4ecca3;
        padding: 2px 6px; border-radius: 4px; cursor: pointer;
        transition: all 0.2s;
    }}
    .word-yellow {{
        background: rgba(240, 192, 64, 0.2); color: #f0c040;
        padding: 2px 6px; border-radius: 4px; cursor: pointer;
        transition: all 0.2s;
    }}
    .word-red {{
        background: rgba(233, 69, 96, 0.3); color: #e94560;
        padding: 2px 6px; border-radius: 4px; cursor: pointer;
        transition: all 0.2s; text-decoration: underline wavy;
    }}
    .word-deleted {{
        text-decoration: line-through;
        opacity: 0.6;
    }}
    .word-green:hover, .word-yellow:hover, .word-red:hover {{
        transform: scale(1.1); filter: brightness(1.3);
    }}
    .word-active {{
        outline: 2px solid #fff; outline-offset: 2px;
    }}

    /* Popup */
    .popup {{
        display: none; position: absolute; bottom: 100%; left: 50%;
        transform: translateX(-50%); margin-bottom: 10px;
        background: #0f3460; border: 1px solid #4ecca3; border-radius: 12px;
        padding: 16px; min-width: 280px; max-width: 350px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5); z-index: 100;
        font-size: 14px; line-height: 1.6;
    }}
    .popup.active {{ display: block; animation: popIn 0.2s ease-out; }}
    @keyframes popIn {{ from {{ opacity:0; transform: translateX(-50%) translateY(5px); }} to {{ opacity:1; transform: translateX(-50%) translateY(0); }} }}
    .popup::after {{
        content: ''; position: absolute; top: 100%; left: 50%;
        transform: translateX(-50%); border: 8px solid transparent;
        border-top-color: #0f3460;
    }}
    .popup-word {{ font-size: 22px; font-weight: bold; color: #fff; }}
    .popup-phonetic {{ font-size: 16px; color: #4ecca3; margin: 4px 0; font-family: serif; }}
    .popup-you-said {{ color: #e94560; margin: 8px 0 4px; font-size: 13px; }}
    .popup-you-said b {{ color: #f472b6; }}
    .popup-def {{ color: #aaa; font-size: 13px; margin-top: 8px; border-top: 1px solid #1a1a2e; padding-top: 8px; }}
    .popup-buttons {{ display: flex; gap: 8px; margin-top: 10px; }}
    .popup-btn {{
        flex: 1; padding: 8px 12px; border: none; border-radius: 8px;
        cursor: pointer; font-size: 13px; font-weight: bold;
        transition: all 0.2s;
    }}
    .btn-correct {{ background: #4ecca3; color: #0f0f1a; }}
    .btn-correct:hover {{ background: #6fe8c0; }}
    .btn-you {{ background: #e94560; color: #fff; }}
    .btn-you:hover {{ background: #f4607a; }}
    .popup-loading {{ color: #888; font-style: italic; }}
    .popup-close {{
        position: absolute; top: 8px; right: 12px; background: none;
        border: none; color: #666; cursor: pointer; font-size: 18px;
    }}
    .popup-close:hover {{ color: #fff; }}

    .audio-controls {{
        background: #16213e; border-radius: 12px; padding: 16px;
        margin: 20px 0; text-align: center;
    }}
    audio {{ width: 100%; margin-top: 10px; }}

    .reference {{
        background: #0f3460; border-radius: 12px; padding: 16px;
        margin: 20px 0; font-size: 14px; color: #aaa;
    }}
    .reference b {{ color: #ccc; }}

    .legend {{
        display: flex; gap: 20px; margin: 15px 0; font-size: 14px;
    }}
    .legend span {{ display: flex; align-items: center; gap: 5px; }}
    .dot {{ width: 12px; height: 12px; border-radius: 50%; display: inline-block; }}
    .dot-green {{ background: #4ecca3; }}
    .dot-yellow {{ background: #f0c040; }}
    .dot-red {{ background: #e94560; }}
</style>
</head>
<body>

<h1>🎤 Pronunciation Report</h1>
<p style="color:#888">{audio_name} — {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>

<div class="score-card">
    <div class="score-box score-overall">
        <div class="number">{overall:.0f}</div>
        <div class="label">Overall Score</div>
    </div>
    <div class="score-box score-green">
        <div class="number">{green}</div>
        <div class="label">🟢 Good</div>
    </div>
    <div class="score-box score-yellow">
        <div class="number">{yellow}</div>
        <div class="label">🟡 Check</div>
    </div>
    <div class="score-box score-red">
        <div class="number">{red}</div>
        <div class="label">🔴 Error</div>
    </div>
</div>

<div class="legend">
    <span><span class="dot dot-green"></span> Good pronunciation</span>
    <span><span class="dot dot-yellow"></span> Needs practice</span>
    <span><span class="dot dot-red"></span> Pronunciation error</span>
</div>

<div class="audio-controls">
    <b>Full Audio</b>
    <audio id="mainAudio" controls src="{Path(audio_path).name}"></audio>
</div>

<h2 style="color:#e94560">Transcript</h2>
<div class="transcript" id="transcript">
    {words_html}
</div>

<div class="reference">
    <b>Reference text:</b><br>
    {reference}
</div>

<script>
const audio = document.getElementById('mainAudio');
let activeWord = null;
let activePopup = null;

// Dictionary cache
const dictCache = {{}};

async function fetchDict(word) {{
    const w = word.toLowerCase().replace(/[^a-z]/g, '');
    if (!w) return null;
    if (dictCache[w]) return dictCache[w];
    try {{
        const resp = await fetch(`https://api.dictionaryapi.dev/api/v2/entries/en/${{w}}`);
        if (!resp.ok) return null;
        const data = await resp.json();
        dictCache[w] = data[0];
        return data[0];
    }} catch(e) {{ return null; }}
}}

function closePopup() {{
    if (activePopup) {{
        activePopup.classList.remove('active');
        activePopup = null;
    }}
}}

async function showPopup(el) {{
    closePopup();

    const wrap = el.closest('.word-wrap');
    let popup = wrap.querySelector('.popup');
    if (!popup) {{
        popup = document.createElement('div');
        popup.className = 'popup';
        wrap.appendChild(popup);
    }}

    const refWord = el.dataset.ref || el.textContent;
    const hypWord = el.dataset.hyp || '';
    const status = el.dataset.status || '';
    const conf = el.dataset.conf || '';
    const start = parseFloat(el.dataset.start);
    const end = parseFloat(el.dataset.end);

    // Show loading
    popup.innerHTML = `<button class="popup-close" onclick="closePopup()">×</button>
        <div class="popup-word">${{refWord}}</div>
        <div class="popup-loading">Loading dictionary...</div>`;
    popup.classList.add('active');
    activePopup = popup;

    // Fetch dictionary
    const dict = await fetchDict(refWord);

    let phonetic = '';
    let audioUrl = '';
    let definition = '';

    if (dict) {{
        phonetic = dict.phonetic || (dict.phonetics && dict.phonetics.length > 0 ? dict.phonetics[0].text : '') || '';
        // Find audio URL
        if (dict.phonetics) {{
            for (const p of dict.phonetics) {{
                if (p.audio) {{ audioUrl = p.audio; break; }}
            }}
        }}
        // First definition
        if (dict.meanings && dict.meanings.length > 0) {{
            const m = dict.meanings[0];
            const pos = m.partOfSpeech || '';
            const def = m.definitions && m.definitions[0] ? m.definitions[0].definition : '';
            definition = `<i>${{pos}}</i> — ${{def}}`;
        }}
    }}

    let youSaidHtml = '';
    if (status === 'substitution' && hypWord) {{
        youSaidHtml = `<div class="popup-you-said">❌ Вы сказали: <b>"${{hypWord}}"</b> (уверенность: ${{(parseFloat(conf)*100).toFixed(0)}}%)</div>`;
    }} else if (status === 'deletion') {{
        youSaidHtml = `<div class="popup-you-said">⛔ Слово пропущено</div>`;
    }} else if (conf) {{
        youSaidHtml = `<div class="popup-you-said">Уверенность: ${{(parseFloat(conf)*100).toFixed(0)}}%</div>`;
    }}

    let buttonsHtml = '';
    if (audioUrl) {{
        buttonsHtml += `<button class="popup-btn btn-correct" onclick="new Audio('${{audioUrl}}').play()">🔊 Правильно</button>`;
    }}
    if (!isNaN(start)) {{
        buttonsHtml += `<button class="popup-btn btn-you" data-play-start="${{start}}" data-play-end="${{end}}" onclick="playFromBtn(this)">🎤 Как вы сказали</button>`;
    }}

    popup.innerHTML = `
        <button class="popup-close" onclick="closePopup()">×</button>
        <div class="popup-word">${{refWord}}</div>
        ${{phonetic ? `<div class="popup-phonetic">${{phonetic}}</div>` : ''}}
        ${{youSaidHtml}}
        ${{buttonsHtml ? `<div class="popup-buttons">${{buttonsHtml}}</div>` : ''}}
        ${{definition ? `<div class="popup-def">${{definition}}</div>` : ''}}
    `;
}}

function playFromBtn(btn) {{
    const s = parseFloat(btn.dataset.playStart);
    const e = parseFloat(btn.dataset.playEnd);
    if (isNaN(s)) return;
    audio.currentTime = Math.max(0, s - 0.2);
    audio.play();
    const checkEnd = setInterval(() => {{
        if (audio.currentTime >= e + 0.3) {{
            audio.pause();
            clearInterval(checkEnd);
        }}
    }}, 50);
}}

function handleWordClick(el) {{
    showPopup(el);
    playSegment(el);
}}

function playSegment(el) {{
    const start = parseFloat(el.dataset.start);
    const end = parseFloat(el.dataset.end);
    if (isNaN(start)) return;

    if (activeWord) activeWord.classList.remove('word-active');
    el.classList.add('word-active');
    activeWord = el;

    audio.currentTime = Math.max(0, start - 0.2);
    audio.play();

    const checkEnd = setInterval(() => {{
        if (audio.currentTime >= end + 0.3) {{
            audio.pause();
            clearInterval(checkEnd);
        }}
    }}, 50);
}}

// Highlight words during playback
audio.addEventListener('timeupdate', () => {{
    const t = audio.currentTime;
    document.querySelectorAll('[data-start]').forEach(el => {{
        const s = parseFloat(el.dataset.start);
        const e = parseFloat(el.dataset.end);
        if (t >= s && t <= e) {{
            el.style.outline = '2px solid rgba(255,255,255,0.5)';
            el.style.outlineOffset = '2px';
        }} else {{
            el.style.outline = 'none';
        }}
    }});
}});

// Close popup on outside click
document.addEventListener('click', (e) => {{
    if (!e.target.closest('.word-wrap') && !e.target.closest('.popup')) {{
        closePopup();
    }}
}});
</script>
</body>
</html>"""

    output_path = output_dir / f"{audio_name}_report.html"
    with open(output_path, "w") as f:
        f.write(html)

    return str(output_path)


def analyze(audio_path: str, reference: str, model=None, model_size: str = "base", output_dir: str = None) -> dict:
    """Full analysis pipeline."""
    import numpy as np

    audio_path = str(audio_path)
    output_dir = Path(output_dir or Path(audio_path).parent)
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[bold blue]Pronunciation Analyzer v2[/bold blue]")
    console.print(f"Audio: {audio_path}")

    # 1. Transcribe
    console.print("[blue]Transcribing...[/blue]")
    transcript = transcribe_with_words(audio_path, model=model, model_size=model_size)
    console.print(f"[green]Transcript:[/green] {transcript['text']}")

    # 2. Align with reference
    console.print("[blue]Aligning with reference...[/blue]")
    aligned = align_words(reference, transcript["words"])

    # 3. Score each word
    scored = [score_word(a) for a in aligned]

    # 4. Generate HTML report
    console.print("[blue]Generating report...[/blue]")
    # Copy audio next to report for browser access
    import shutil
    audio_copy = output_dir / Path(audio_path).name
    if not audio_copy.exists() or str(audio_copy) != str(Path(audio_path).resolve()):
        shutil.copy2(audio_path, audio_copy)

    html_path = generate_html_report(audio_path, reference, aligned, scored, output_dir)
    console.print(f"[green]Report: {html_path}[/green]")

    # 5. Summary
    total = len(scored)
    green = sum(1 for s in scored if s["color"] == "green")
    yellow = sum(1 for s in scored if s["color"] == "yellow")
    red = sum(1 for s in scored if s["color"] == "red")
    overall = sum(s["score"] for s in scored) / max(total, 1)

    console.print(f"\n[bold]Score: {overall:.0f}/100[/bold]")
    console.print(f"  🟢 {green}  🟡 {yellow}  🔴 {red}")

    # Problem words
    problems = [(a, s) for a, s in zip(aligned, scored) if s["color"] == "red"]
    if problems:
        console.print(f"\n[bold red]Problem words:[/bold red]")
        for a, s in problems:
            if a["status"] == "substitution":
                console.print(f"  ❌ \"{a['ref_word']}\" → heard \"{a['hyp_word']}\" (conf: {a['confidence']:.0%})")
            elif a["status"] == "deletion":
                console.print(f"  ⛔ \"{a['ref_word']}\" — skipped")
            elif a["status"] == "correct":
                console.print(f"  ⚠️ \"{a['ref_word']}\" — unclear (conf: {a['confidence']:.0%})")

    # Save JSON
    report = {
        "audio": audio_path,
        "reference": reference,
        "transcript": transcript["text"],
        "overall_score": round(overall, 1),
        "words_total": total,
        "words_green": green,
        "words_yellow": yellow,
        "words_red": red,
        "aligned_words": aligned,
        "scored_words": scored,
        "analyzed_at": datetime.now().isoformat(),
    }

    json_path = output_dir / f"{Path(audio_path).stem}_report.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pronunciation Analyzer v2")
    parser.add_argument("audio", help="Audio file path")
    parser.add_argument("-r", "--reference", required=True, help="Reference text")
    parser.add_argument("-m", "--model", default="base", help="Whisper model size")
    parser.add_argument("-o", "--output", help="Output directory")
    args = parser.parse_args()

    if not Path(args.audio).exists():
        console.print(f"[red]File not found: {args.audio}[/red]")
        sys.exit(1)

    analyze(args.audio, args.reference, model_size=args.model, output_dir=args.output)


if __name__ == "__main__":
    main()
