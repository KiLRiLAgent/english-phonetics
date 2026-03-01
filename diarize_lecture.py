#!/usr/bin/env python3
"""Speaker diarization for lecture transcripts.

Identifies speakers in an MP3 file and maps them to word-level timestamps.
Uses pyannote/speaker-diarization-3.1 (same model as analyzer_diarization.py).

Usage:
    python diarize_lecture.py
    python diarize_lecture.py path/to/audio.mp3
"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TRANSCRIPTIONS_DIR = Path("transcriptions")


def load_diarization_pipeline():
    """Load pyannote speaker diarization pipeline."""
    from pyannote.audio import Pipeline

    hf_token = os.getenv("HUGGINGFACE_TOKEN")
    if not hf_token:
        print("HUGGINGFACE_TOKEN not found in .env!")
        print("See GET_HUGGINGFACE_TOKEN.md for instructions.")
        sys.exit(1)

    print("Loading speaker diarization pipeline...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token
    )
    print("Diarization pipeline loaded")
    return pipeline


def diarize_speakers(pipeline, audio_path: str):
    """Run diarization on audio file. Returns speaker segments."""
    print(f"Running diarization on: {audio_path}")
    diarization = pipeline(audio_path)

    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speaker_id = int(speaker.split('_')[-1]) if '_' in speaker else 0
        segments.append({
            "speaker": speaker_id,
            "start": round(turn.start, 2),
            "end": round(turn.end, 2)
        })

    unique_speakers = sorted(set(s['speaker'] for s in segments))
    print(f"Found {len(unique_speakers)} speaker(s): {unique_speakers}")
    return segments, unique_speakers


def map_speakers_to_words(flat_words, speaker_segments):
    """Map speaker labels to words using midpoint matching."""
    words_with_speakers = []
    for w in flat_words:
        mid_time = (w['start'] + w['end']) / 2
        speaker = 0

        for seg in speaker_segments:
            if seg['start'] <= mid_time <= seg['end']:
                speaker = seg['speaker']
                break

        words_with_speakers.append({
            "word": w["word"],
            "start": w["start"],
            "end": w["end"],
            "speaker": speaker
        })

    return words_with_speakers


def compute_speaker_stats(speaker_segments, unique_speakers):
    """Compute speaking time and segment count per speaker."""
    stats = {}
    for sid in unique_speakers:
        segs = [s for s in speaker_segments if s['speaker'] == sid]
        total_time = sum(s['end'] - s['start'] for s in segs)
        stats[sid] = {
            "id": sid,
            "total_time": round(total_time, 2),
            "segments_count": len(segs),
            "label": f"Speaker {sid + 1}"
        }
    return [stats[sid] for sid in sorted(stats)]


def find_audio_and_words():
    """Find the latest MP3 and corresponding flat words file."""
    mp3_files = list(TRANSCRIPTIONS_DIR.glob("*.mp3"))
    if not mp3_files:
        print("No MP3 files found in transcriptions/")
        sys.exit(1)

    audio_file = max(mp3_files, key=lambda p: p.stat().st_mtime)

    # Find matching flat words file
    flat_files = list(TRANSCRIPTIONS_DIR.glob("*_words_flat.json"))
    if not flat_files:
        print("No *_words_flat.json found in transcriptions/")
        sys.exit(1)

    flat_file = max(flat_files, key=lambda p: p.stat().st_mtime)

    return audio_file, flat_file


def main():
    # Determine audio file
    if len(sys.argv) > 1:
        audio_file = Path(sys.argv[1])
        if not audio_file.exists():
            print(f"File not found: {audio_file}")
            sys.exit(1)
        # Find flat words in transcriptions dir
        flat_files = list(TRANSCRIPTIONS_DIR.glob("*_words_flat.json"))
        if not flat_files:
            print("No *_words_flat.json found in transcriptions/")
            sys.exit(1)
        flat_file = max(flat_files, key=lambda p: p.stat().st_mtime)
    else:
        audio_file, flat_file = find_audio_and_words()

    print(f"Audio: {audio_file.name}")
    print(f"Words: {flat_file.name}")

    # Load flat words
    with open(flat_file, 'r', encoding='utf-8') as f:
        flat_words = json.load(f)
    print(f"Loaded {len(flat_words)} words")

    # Run diarization
    pipeline = load_diarization_pipeline()
    speaker_segments, unique_speakers = diarize_speakers(pipeline, str(audio_file))

    # Map speakers to words
    words_with_speakers = map_speakers_to_words(flat_words, speaker_segments)

    # Compute stats
    speaker_stats = compute_speaker_stats(speaker_segments, unique_speakers)

    # Build result
    result = {
        "speakers_count": len(unique_speakers),
        "speaker_segments": speaker_segments,
        "speaker_stats": speaker_stats,
        "words_with_speakers": words_with_speakers
    }

    # Derive output filename from flat words file
    stem = flat_file.name.replace("_words_flat.json", "")
    output_file = TRANSCRIPTIONS_DIR / f"{stem}_diarization.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: {output_file}")
    print(f"\nSpeaker stats:")
    for s in speaker_stats:
        mins = int(s['total_time'] // 60)
        secs = int(s['total_time'] % 60)
        print(f"  {s['label']}: {mins}m {secs}s ({s['segments_count']} segments)")


if __name__ == '__main__':
    main()
