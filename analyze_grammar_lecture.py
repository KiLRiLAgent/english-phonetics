#!/usr/bin/env python3
"""Analyze grammar in lecture transcript using OpenAI with chunking and timestamp linking."""

import sys
import os
import json
import re
from pathlib import Path
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TRANSCRIPTIONS_DIR = Path("transcriptions")


def load_transcript():
    """Load _words.json and _words_flat.json from transcriptions/."""
    words_files = list(TRANSCRIPTIONS_DIR.glob("*_words.json"))
    flat_files = list(TRANSCRIPTIONS_DIR.glob("*_words_flat.json"))

    if not words_files:
        print("No *_words.json found in transcriptions/")
        sys.exit(1)
    if not flat_files:
        print("No *_words_flat.json found in transcriptions/")
        sys.exit(1)

    words_file = max(words_files, key=lambda p: p.stat().st_mtime)
    flat_file = max(flat_files, key=lambda p: p.stat().st_mtime)

    print(f"Loading segments from: {words_file.name}")
    print(f"Loading flat words from: {flat_file.name}")

    with open(words_file, 'r', encoding='utf-8') as f:
        words_data = json.load(f)

    with open(flat_file, 'r', encoding='utf-8') as f:
        flat_words = json.load(f)

    # Build full text from segments
    segments = words_data.get("segments", [])
    full_text = " ".join(seg["text"].strip() for seg in segments if seg.get("text"))

    # Derive output stem from words_file name (remove _words.json suffix)
    stem = words_file.name.replace("_words.json", "")

    return full_text, flat_words, stem


def split_into_chunks(text, max_chars=3000):
    """Split text into chunks at sentence boundaries."""
    sentences = re.split(r'(?<=[.?!])\s+', text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(current) + len(sentence) + 1 > max_chars and current:
            chunks.append(current.strip())
            current = sentence
        else:
            current = current + " " + sentence if current else sentence

    if current.strip():
        chunks.append(current.strip())

    return chunks


def analyze_chunk(text, chunk_index, total_chunks):
    """Send a chunk to OpenAI for grammar analysis."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are an English grammar checker for lecture transcripts. Find grammatical errors and suggest improvements. Return JSON format only."
            },
            {
                "role": "user",
                "content": f"""Analyze this English lecture transcript excerpt for grammar errors. Find:
1. Grammar mistakes (tense, agreement, articles, prepositions)
2. Awkward phrasing or unclear sentences
3. Word choice issues

Important: This is spoken language from a lecture, so ignore:
- Filler words (um, uh, like, you know)
- Informal contractions
- Normal speech disfluencies
- Punctuation errors (periods, commas, semicolons — these are added by transcription, not the speaker)

Focus on actual grammar errors that a language learner should correct.

Return ONLY valid JSON:
{{
  "errors": [
    {{
      "text": "exact original text fragment with the error (5-15 words)",
      "type": "grammar|clarity|word-choice",
      "issue": "description of the problem",
      "suggestion": "how to fix it",
      "rule": "RULE_NAME (e.g. ARTICLES, SUBJECT_VERB_AGREEMENT, PREPOSITIONS, TENSE_CONSISTENCY, WORD_ORDER)"
    }}
  ]
}}

Text to analyze (chunk {chunk_index + 1}/{total_chunks}):
{text}"""
            }
        ],
        "temperature": 0.3,
        "max_tokens": 3000
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=90
    )

    result = response.json()

    if 'error' in result:
        print(f"  API error: {result['error']}")
        return []

    content = result['choices'][0]['message']['content']

    try:
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()

        data = json.loads(content)
        return data.get("errors", [])
    except Exception as e:
        print(f"  Failed to parse JSON: {e}")
        print(f"  Response: {content[:200]}")
        return []


def find_timestamp(error_text, flat_words):
    """Find timestamp for error text by matching word sequence in flat_words."""
    # Normalize error text into words
    error_words = re.findall(r"[a-z']+", error_text.lower())
    if not error_words:
        return None

    # Normalize flat words
    normalized = []
    for w in flat_words:
        clean = re.sub(r'[^a-z\']', '', w["word"].lower().strip())
        if clean:
            normalized.append({"clean": clean, "start": w["start"], "end": w["end"]})

    # Sliding window search
    window_size = len(error_words)
    for i in range(len(normalized) - window_size + 1):
        window = [normalized[i + j]["clean"] for j in range(window_size)]
        if window == error_words:
            return {"start": normalized[i]["start"]}

    # Fallback: try matching first 3-4 words
    for match_len in [min(4, len(error_words)), min(3, len(error_words)), min(2, len(error_words))]:
        if match_len < 2:
            break
        prefix = error_words[:match_len]
        for i in range(len(normalized) - match_len + 1):
            window = [normalized[i + j]["clean"] for j in range(match_len)]
            if window == prefix:
                return {"start": normalized[i]["start"]}

    return None


def main():
    if not OPENAI_API_KEY:
        print("OPENAI_API_KEY not set. Check .env file.")
        sys.exit(1)

    full_text, flat_words, stem = load_transcript()
    print(f"Full text: {len(full_text)} chars, {len(flat_words)} words")

    # Split into chunks
    chunks = split_into_chunks(full_text, max_chars=3000)
    print(f"Split into {len(chunks)} chunks")

    # Analyze each chunk
    all_errors = []
    for i, chunk in enumerate(chunks):
        print(f"\nAnalyzing chunk {i + 1}/{len(chunks)} ({len(chunk)} chars)...")
        errors = analyze_chunk(chunk, i, len(chunks))
        print(f"  Found {len(errors)} errors")
        all_errors.extend(errors)

    # Filter out punctuation errors (irrelevant for speech analysis)
    SKIP_RULES = {"PUNCTUATION"}
    all_errors = [e for e in all_errors if e.get("rule") not in SKIP_RULES]

    print(f"\nTotal errors found: {len(all_errors)}")

    # Link timestamps
    linked = 0
    for error in all_errors:
        ts = find_timestamp(error.get("text", ""), flat_words)
        if ts:
            error["timestamp"] = ts
            linked += 1
        else:
            error["timestamp"] = {"start": 0}

    print(f"Timestamps linked: {linked}/{len(all_errors)}")

    # Build summary
    summary = {
        "total_errors": len(all_errors),
        "grammar": sum(1 for e in all_errors if e.get("type") == "grammar"),
        "clarity": sum(1 for e in all_errors if e.get("type") == "clarity"),
        "word_choice": sum(1 for e in all_errors if e.get("type") == "word-choice"),
    }

    result = {
        "errors": all_errors,
        "summary": summary
    }

    # Save as the format expected by grammar viewer
    output_file = TRANSCRIPTIONS_DIR / f"{stem}.grammar.full.words.filtered.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: {output_file}")
    print(f"\nSummary:")
    print(f"  Total: {summary['total_errors']}")
    print(f"  Grammar: {summary['grammar']}")
    print(f"  Clarity: {summary['clarity']}")
    print(f"  Word choice: {summary['word_choice']}")

    # Show sample errors
    print(f"\nSample errors:")
    for i, err in enumerate(all_errors[:5], 1):
        ts = err.get("timestamp", {}).get("start", "?")
        print(f"\n  {i}. [{err.get('type')}] @ {ts}s: {err.get('text')}")
        print(f"     Issue: {err.get('issue')}")
        print(f"     Fix: {err.get('suggestion')}")


if __name__ == '__main__':
    main()
