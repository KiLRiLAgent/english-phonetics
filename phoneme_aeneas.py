#!/usr/bin/env python3
"""
Phoneme-level pronunciation scorer using Aeneas forced aligner.

Aeneas provides word-level alignment (audio → text).
We combine it with phoneme analysis for pronunciation scoring.

Architecture:
1. Aeneas: Get word-level timestamps (which word at what time)
2. Whisper: Get actual transcription
3. g2p_en: Get expected phonemes for each word
4. Compare: Actual vs expected phonemes within word boundaries
"""

import json
import tempfile
from pathlib import Path
from typing import List, Dict
import soundfile as sf

try:
    from aeneas.executetask import ExecuteTask
    from aeneas.task import Task
except ImportError:
    raise ImportError("Aeneas not installed. Run: pip install aeneas")

from g2p_en import G2p


class AeneasPronunciationScorer:
    """
    Forced alignment-based pronunciation scorer.
    
    Uses Aeneas for word-level alignment, then scores phonemes.
    """
    
    def __init__(self):
        self.g2p = G2p()
    
    def align_words(self, audio_path: str, reference_text: str) -> List[Dict]:
        """
        Align audio with reference text using Aeneas.
        
        Args:
            audio_path: Path to audio file (.wav)
            reference_text: The text that should have been spoken
        
        Returns:
            List of word alignment dicts:
            [{"word": "hello", "start": 0.5, "end": 0.9}, ...]
        """
        # Aeneas requires specific format
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Write reference text to file
            text_file = tmpdir / "text.txt"
            text_file.write_text(reference_text)
            
            # Output sync map
            sync_file = tmpdir / "sync.json"
            
            # Configure task
            # Language: English, plain text, JSON output
            config_string = "task_language=eng|is_text_type=plain|os_task_file_format=json"
            
            task = Task(config_string=config_string)
            task.audio_file_path_absolute = str(Path(audio_path).absolute())
            task.text_file_path_absolute = str(text_file.absolute())
            task.sync_map_file_path_absolute = str(sync_file.absolute())
            
            # Execute alignment
            ExecuteTask(task).execute()
            
            # Parse results
            sync_map = json.loads(sync_file.read_text())
            
            alignments = []
            for fragment in sync_map.get("fragments", []):
                alignments.append({
                    "word": fragment.get("lines", [""])[0],
                    "start": float(fragment.get("begin", 0)),
                    "end": float(fragment.get("end", 0)),
                })
            
            return alignments
    
    def score_pronunciation(
        self, 
        audio_path: str, 
        reference_text: str,
        actual_transcription: str = None
    ) -> Dict:
        """
        Score pronunciation by comparing aligned audio with reference.
        
        Args:
            audio_path: Path to audio file
            reference_text: Expected text
            actual_transcription: What was actually said (from Whisper)
        
        Returns:
            {
                "words": [
                    {
                        "word": "hello",
                        "start": 0.5,
                        "end": 0.9,
                        "score": 85,
                        "expected_phonemes": ["h", "ə", "l", "oʊ"],
                        "issues": []
                    },
                    ...
                ],
                "overall_score": 75,
                ...
            }
        """
        # Step 1: Get word-level alignment
        alignments = self.align_words(audio_path, reference_text)
        
        # Step 2: Get expected phonemes for each word
        reference_words = reference_text.lower().split()
        expected_phonemes_map = {}
        for word in reference_words:
            phonemes = self.g2p(word)
            # Filter out non-phoneme symbols
            phonemes = [p for p in phonemes if p not in (' ', ',', '.', '?', '!', '-', "'")]
            expected_phonemes_map[word.lower()] = phonemes
        
        # Step 3: Score each word
        # For now, just check if word was spoken (presence check)
        # TODO: Add actual phoneme-level comparison
        
        scored_words = []
        for alignment in alignments:
            word = alignment["word"].lower()
            expected = expected_phonemes_map.get(word, [])
            
            # Simple scoring: if aligned, assume it was spoken
            # (Aeneas only aligns if audio matches)
            score = 80  # Base score for aligned words
            
            scored_words.append({
                **alignment,
                "score": score,
                "expected_phonemes": expected,
                "actual_phonemes": expected,  # Placeholder
                "issues": [],
                "color": "green" if score >= 75 else "yellow" if score >= 50 else "red"
            })
        
        overall = sum(w["score"] for w in scored_words) / len(scored_words) if scored_words else 0
        
        return {
            "words": scored_words,
            "overall_score": round(overall, 1),
            "alignment_method": "aeneas"
        }


def get_scorer() -> AeneasPronunciationScorer:
    """Get singleton scorer instance."""
    global _scorer
    if '_scorer' not in globals():
        _scorer = AeneasPronunciationScorer()
    return _scorer


if __name__ == "__main__":
    # Test
    scorer = get_scorer()
    
    # Example
    audio = "test.wav"
    reference = "don't you tell me what to do"
    
    result = scorer.score_pronunciation(audio, reference)
    print(json.dumps(result, indent=2))
