#!/usr/bin/env python3
"""
English Phonetics & Grammar Analyzer
Analyzes audio for pronunciation quality and grammar errors.
"""

import os
import sys
import json
import argparse
import tempfile
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def transcribe_audio(audio_path: str, model_size: str = "base") -> dict:
    """Transcribe audio using Whisper with word-level timestamps. Only English segments are kept."""
    import whisper
    
    console.print(f"[blue]Loading Whisper model ({model_size})...[/blue]")
    model = whisper.load_model(model_size)
    
    # First pass: detect language
    console.print(f"[blue]Detecting language in {audio_path}...[/blue]")
    audio = whisper.load_audio(audio_path)
    audio_trimmed = whisper.pad_or_trim(audio)
    n_mels = 128 if "large-v3" in model_size or "turbo" in model_size else 80
    mel = whisper.log_mel_spectrogram(audio_trimmed, n_mels=n_mels).to(model.device)
    _, probs = model.detect_language(mel)
    detected_lang = max(probs, key=probs.get)
    en_prob = probs.get("en", 0)
    console.print(f"[blue]Detected language: {detected_lang} (en probability: {en_prob:.1%})[/blue]")
    
    if en_prob < 0.3:
        console.print(f"[yellow]Warning: Audio appears to be {detected_lang}, not English. Skipping non-English content.[/yellow]")
    
    # Transcribe with language=en to force English interpretation
    console.print(f"[blue]Transcribing {audio_path}...[/blue]")
    result = model.transcribe(
        audio_path,
        language="en",
        word_timestamps=True,
    )
    
    # Filter segments: keep only those with high English probability
    # Use Whisper's no_speech_prob and language detection per segment
    filtered_segments = []
    for segment in result.get("segments", []):
        # Skip segments with very high no_speech probability
        if segment.get("no_speech_prob", 0) > 0.7:
            continue
        # Skip segments that look like non-English (gibberish transcription indicators)
        text = segment.get("text", "").strip()
        if not text:
            continue
        # Check if text contains mostly ASCII/English characters
        ascii_ratio = sum(1 for c in text if c.isascii()) / max(len(text), 1)
        if ascii_ratio < 0.8:
            console.print(f"[yellow]Skipping non-English segment: '{text[:50]}...'[/yellow]")
            continue
        filtered_segments.append(segment)
    
    result["segments"] = filtered_segments
    result["text"] = " ".join(s["text"].strip() for s in filtered_segments)
    
    return result


def analyze_grammar(text: str) -> list:
    """Analyze grammar using LanguageTool (local)."""
    import language_tool_python
    
    console.print("[blue]Checking grammar...[/blue]")
    
    # Try local server first, fall back to remote
    try:
        tool = language_tool_python.LanguageTool('en-US')
    except Exception:
        console.print("[yellow]Local LanguageTool not found, using remote...[/yellow]")
        tool = language_tool_python.LanguageToolPublicAPI('en-US')
    
    matches = tool.check(text)
    
    errors = []
    for match in matches:
        errors.append({
            "message": match.message,
            "context": match.context,
            "offset": match.offset,
            "length": getattr(match, 'errorLength', getattr(match, 'error_length', 0)),
            "rule_id": getattr(match, 'ruleId', getattr(match, 'rule_id', '')),
            "category": match.category,
            "replacements": match.replacements[:3] if match.replacements else [],
            "severity": _classify_severity(match),
        })
    
    tool.close()
    return errors


def _classify_severity(match) -> str:
    """Classify grammar error severity."""
    critical_categories = ["GRAMMAR", "TYPOS", "CONFUSED_WORDS"]
    if match.category in critical_categories:
        return "high"
    elif match.category in ["PUNCTUATION", "CASING"]:
        return "medium"
    return "low"


def analyze_pronunciation(audio_path: str, transcript: str) -> dict:
    """
    Analyze pronunciation quality.
    Uses Whisper word confidence + basic phonetic analysis.
    
    For full phoneme-level analysis, MFA needs to be installed separately.
    """
    import whisper
    import numpy as np
    
    model_size = os.getenv("WHISPER_MODEL", "base")
    model = whisper.load_model(model_size)
    
    # Get detailed result with word-level data
    result = model.transcribe(
        audio_path,
        language="en",
        word_timestamps=True,
    )
    
    word_scores = []
    
    for segment in result.get("segments", []):
        for word_info in segment.get("words", []):
            word = word_info.get("word", "").strip()
            probability = word_info.get("probability", 0.0)
            
            # Confidence as proxy for pronunciation clarity
            # Low confidence often means unclear pronunciation
            word_scores.append({
                "word": word,
                "confidence": round(probability, 3),
                "start": round(word_info.get("start", 0), 2),
                "end": round(word_info.get("end", 0), 2),
                "quality": _score_pronunciation(probability),
            })
    
    # Overall metrics
    confidences = [w["confidence"] for w in word_scores]
    avg_confidence = np.mean(confidences) if confidences else 0
    
    # Words that need improvement (low confidence)
    problem_words = [w for w in word_scores if w["confidence"] < 0.7]
    
    return {
        "overall_score": round(float(avg_confidence * 100), 1),
        "total_words": len(word_scores),
        "problem_words_count": len(problem_words),
        "words": word_scores,
        "problem_words": problem_words,
    }


def _score_pronunciation(confidence: float) -> str:
    """Score pronunciation based on Whisper confidence."""
    if confidence >= 0.9:
        return "excellent"
    elif confidence >= 0.75:
        return "good"
    elif confidence >= 0.5:
        return "fair"
    else:
        return "poor"


def generate_report(
    audio_path: str,
    transcript: dict,
    grammar_errors: list,
    pronunciation: dict,
) -> dict:
    """Generate a unified analysis report."""
    
    text = transcript.get("text", "")
    
    # Grammar score (100 - penalties)
    grammar_score = 100
    for err in grammar_errors:
        if err["severity"] == "high":
            grammar_score -= 10
        elif err["severity"] == "medium":
            grammar_score -= 5
        else:
            grammar_score -= 2
    grammar_score = max(0, grammar_score)
    
    # Overall score
    overall = (pronunciation["overall_score"] * 0.6 + grammar_score * 0.4)
    
    report = {
        "audio_file": audio_path,
        "analyzed_at": datetime.now().isoformat(),
        "transcript": text,
        "overall_score": round(overall, 1),
        "pronunciation": {
            "score": pronunciation["overall_score"],
            "total_words": pronunciation["total_words"],
            "problem_words": pronunciation["problem_words_count"],
            "details": pronunciation["problem_words"],
        },
        "grammar": {
            "score": grammar_score,
            "total_errors": len(grammar_errors),
            "errors": grammar_errors,
        },
    }
    
    return report


def display_report(report: dict):
    """Display report in terminal."""
    
    # Overall
    score = report["overall_score"]
    color = "green" if score >= 80 else "yellow" if score >= 60 else "red"
    
    from rich.text import Text as RichText
    score_text = RichText(f"{score}/100", style=f"bold {color}")
    console.print(Panel(score_text, title="Overall Score", border_style=color))
    
    # Transcript
    from rich.text import Text
    console.print(Panel(Text(report["transcript"]), title="Transcript"))
    
    # Pronunciation
    pron = report["pronunciation"]
    console.print(f"\n[bold]Pronunciation: {pron['score']}/100[/bold]")
    console.print(f"Words analyzed: {pron['total_words']}")
    
    if pron["details"]:
        table = Table(title="Problem Words")
        table.add_column("Word")
        table.add_column("Confidence")
        table.add_column("Quality")
        table.add_column("Time")
        
        for w in pron["details"]:
            table.add_row(
                w["word"],
                f"{w['confidence']:.1%}",
                w["quality"],
                f"{w['start']:.1f}s",
            )
        console.print(table)
    else:
        console.print("[green]No pronunciation issues detected![/green]")
    
    # Grammar
    gram = report["grammar"]
    console.print(f"\n[bold]Grammar: {gram['score']}/100[/bold]")
    console.print(f"Errors found: {gram['total_errors']}")
    
    if gram["errors"]:
        table = Table(title="Grammar Issues")
        table.add_column("Issue", style="red")
        table.add_column("Severity")
        table.add_column("Suggestion")
        
        for err in gram["errors"]:
            suggestions = ", ".join(err["replacements"]) if err["replacements"] else "-"
            table.add_row(
                err["message"],
                err["severity"],
                suggestions,
            )
        console.print(table)
    else:
        console.print("[green]No grammar issues detected![/green]")


def main():
    parser = argparse.ArgumentParser(description="Analyze English pronunciation and grammar")
    parser.add_argument("audio", help="Path to audio file (wav, mp3, m4a)")
    parser.add_argument("--model", default=None, help="Whisper model size")
    parser.add_argument("--output", "-o", help="Save JSON report to file")
    parser.add_argument("--reference", "-r", help="Reference text (what they should have said)")
    
    args = parser.parse_args()
    
    if not Path(args.audio).exists():
        console.print(f"[red]File not found: {args.audio}[/red]")
        sys.exit(1)
    
    model_size = args.model or os.getenv("WHISPER_MODEL", "base")
    
    console.print(f"\n[bold blue]English Phonetics & Grammar Analyzer[/bold blue]")
    console.print(f"Audio: {args.audio}")
    console.print(f"Model: {model_size}\n")
    
    # 1. Transcribe
    transcript = transcribe_audio(args.audio, model_size)
    text = transcript.get("text", "").strip()
    console.print("[green]Transcript:[/green]")
    console.print(text + "\n")
    
    # 2. Grammar analysis
    grammar_errors = analyze_grammar(text)
    
    # 3. Pronunciation analysis
    pronunciation = analyze_pronunciation(args.audio, text)
    
    # 3b. Phoneme-level analysis (if reference text provided)
    phoneme_result = None
    if args.reference:
        try:
            from phoneme_scorer_v2 import PhonemeScorer, format_report as format_phoneme_report
            console.print("\n[blue]Running phoneme-level analysis...[/blue]")
            scorer = PhonemeScorer()
            phoneme_result = scorer.score(args.audio, args.reference)
            console.print(format_phoneme_report(phoneme_result))
        except Exception as e:
            console.print(f"[yellow]Phoneme analysis failed: {e}[/yellow]")
    
    # 4. Generate report
    report = generate_report(args.audio, transcript, grammar_errors, pronunciation)
    if phoneme_result:
        report["phoneme_analysis"] = {
            "score": phoneme_result["overall_score"],
            "total_expected": phoneme_result["total_expected"],
            "correct": phoneme_result["correct"],
            "error_count": phoneme_result["error_count"],
            "error_patterns": phoneme_result["error_patterns"][:10],
        }
    
    # 5. Display
    display_report(report)
    
    # 6. Save if requested
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        console.print(f"\n[green]Report saved to {output_path}[/green]")


if __name__ == "__main__":
    main()
