#!/usr/bin/env python3
"""Transcribe lecture video/audio with word-level timestamps using stable-ts (stabilized Whisper)."""

import sys
import json
import subprocess
from pathlib import Path

import stable_whisper

TRANSCRIPTIONS_DIR = Path(__file__).parent / "transcriptions"


def extract_audio(video_path: Path) -> Path:
    """Extract MP3 audio from video file, or return existing MP3."""
    if video_path.suffix.lower() == ".mp3":
        return video_path

    mp3_path = TRANSCRIPTIONS_DIR / f"{video_path.stem}.mp3"
    if mp3_path.exists():
        print(f"Audio already exists: {mp3_path}")
        return mp3_path

    print(f"Extracting audio to {mp3_path}...")
    subprocess.run(
        ["ffmpeg", "-i", str(video_path), "-vn", "-acodec", "libmp3lame", "-b:a", "192k", str(mp3_path)],
        check=True,
    )
    print(f"Audio extracted: {mp3_path}")
    return mp3_path


def transcribe(audio_path: Path) -> dict:
    """Transcribe audio with stable-ts (stabilized Whisper) for accurate word-level timestamps."""
    print("Loading stable-ts model (large-v3-turbo)...")
    model = stable_whisper.load_model("large-v3-turbo")

    print(f"Transcribing: {audio_path}")
    result = model.transcribe(
        str(audio_path),
        language="en",
        vad=True,
        suppress_silence=True,
        suppress_word_ts=True,
        condition_on_previous_text=True,
        initial_prompt="This is a university lecture on economics and finance.",
    )

    print("Refining word-level timestamps...")
    model.refine(str(audio_path), result)

    return result


def save_results(result, audio_path: Path):
    """Save full JSON and flat words JSON from stable-ts WhisperResult."""
    stem = audio_path.stem  # e.g. "Lecture_01_Igor Lyubimov_21.01"

    # Full transcript JSON (segments + words)
    full_path = TRANSCRIPTIONS_DIR / f"{stem}_words.json"
    result.save_as_json(str(full_path))
    print(f"Full transcript saved: {full_path}")

    # Flat words JSON for UI
    words = []
    for segment in result.segments:
        for w in segment.words:
            words.append({
                "word": w.word,
                "start": round(w.start, 3),
                "end": round(w.end, 3),
            })

    flat_path = TRANSCRIPTIONS_DIR / f"{stem}_words_flat.json"
    with open(flat_path, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=2, ensure_ascii=False)
    print(f"Flat words saved: {flat_path} ({len(words)} words)")

    return full_path, flat_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python transcribe_lecture.py <video_or_audio_path>")
        sys.exit(1)

    source = Path(sys.argv[1])
    if not source.exists():
        print(f"Error: File not found: {source}")
        sys.exit(1)

    TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)

    audio_path = extract_audio(source)
    result = transcribe(audio_path)

    full_path, flat_path = save_results(result, audio_path)

    result_dict = result.to_dict()
    duration = result_dict.get("duration", 0)
    num_segments = len(result.segments)
    num_words = sum(len(s.words) for s in result.segments)
    print(f"\nDuration: {duration:.0f}s | Segments: {num_segments} | Words: {num_words}")
    print(f"Preview: {result.text[:300]}...")


if __name__ == "__main__":
    main()
