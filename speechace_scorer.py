#!/usr/bin/env python3
"""
Speechace API integration for pronunciation assessment.

API Docs: https://www.speechace.com/api/
Free Tier: 1000 calls/month
"""

import os
import requests
from pathlib import Path
from typing import Dict, List


class SpeechaceScorer:
    """
    Pronunciation assessment using Speechace API.
    
    Provides:
    - Word-level pronunciation scores (0-100)
    - Phoneme-level scores
    - Specific error detection (th-stopping, substitutions, etc.)
    - Fluency metrics
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize scorer with API key.
        
        Args:
            api_key: Speechace API key. If None, reads from SPEECHACE_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("SPEECHACE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Speechace API key required. Set SPEECHACE_API_KEY env var or pass api_key parameter.\n"
                "Get free key at: https://www.speechace.com/api/"
            )
        
        self.base_url = "https://api.speechace.co/api/scoring/speech/score"
    
    def score_pronunciation(self, audio_path: str, reference_text: str) -> Dict:
        """
        Score pronunciation of audio against reference text.
        
        Args:
            audio_path: Path to audio file (WAV, MP3, OGG)
            reference_text: Expected text
        
        Returns:
            {
                "overall_score": 85.5,
                "words": [
                    {
                        "word": "hello",
                        "score": 90,
                        "start": 0.5,
                        "end": 0.9,
                        "phonemes": [
                            {"phone": "HH", "score": 95, "expected": "HH"},
                            {"phone": "AH", "score": 85, "expected": "AH"},
                            ...
                        ],
                        "issues": ["vowel reduction"]
                    },
                    ...
                ],
                "fluency": {
                    "duration": 3.5,
                    "words_per_min": 120,
                    "avg_pause": 0.3
                }
            }
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Prepare request
        with open(audio_path, 'rb') as audio_file:
            files = {
                'audio_file': (audio_path.name, audio_file, 'audio/wav')
            }
            
            data = {
                'key': self.api_key,
                'text': reference_text,
                'dialect': 'en-us',  # US English
                'user_id': 'test_user',  # Optional user tracking
                
                # Scoring options
                'include_fluency': 1,
                'include_intonation': 0,
                'include_ielts_subscores': 0,
                'include_unknown_words': 1,
                
                # Detailed feedback
                'include_word_syllable_scores': 1,
                'include_phoneme_scores': 1,
                'include_word_timings': 1,
                'include_phoneme_timings': 1,
                'include_word_syllable_boundaries': 1,
            }
            
            response = requests.post(
                self.base_url,
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            raise RuntimeError(f"Speechace API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # Check for API errors
        if result.get('status') == 'error':
            raise RuntimeError(f"Speechace error: {result.get('text', 'Unknown error')}")
        
        # Parse response
        return self._parse_response(result)
    
    def _parse_response(self, api_result: Dict) -> Dict:
        """Convert Speechace API response to our standard format."""
        
        # Overall quality score (0-100)
        overall_score = api_result.get('quality_score', 0)
        
        # Parse word-level data
        words = []
        word_score_list = api_result.get('word_score_list', [])
        
        for word_data in word_score_list:
            word_text = word_data.get('word', '')
            word_score = word_data.get('quality_score', 0)
            
            # Get timing
            start_time = word_data.get('start_offset', 0) / 1000.0  # ms → s
            end_time = word_data.get('end_offset', 0) / 1000.0
            
            # Parse phoneme-level scores
            phonemes = []
            syllable_score_list = word_data.get('syllable_score_list', [])
            
            for syllable in syllable_score_list:
                phone_score_list = syllable.get('phone_score_list', [])
                for phone_data in phone_score_list:
                    phonemes.append({
                        'phone': phone_data.get('phone', ''),
                        'score': phone_data.get('quality_score', 0),
                        'expected': phone_data.get('phone', ''),  # Speechace doesn't separate expected/actual
                        'sound_most_like': phone_data.get('sound_most_like', ''),
                    })
            
            # Detect issues
            issues = []
            if word_score < 50:
                issues.append('poor pronunciation')
            
            # Check for phoneme substitutions
            for phone in phonemes:
                if phone['sound_most_like'] and phone['sound_most_like'] != phone['phone']:
                    issues.append(f"/{phone['phone']}/ → /{phone['sound_most_like']}/")
            
            # Color coding
            if word_score >= 75:
                color = 'green'
            elif word_score >= 50:
                color = 'yellow'
            else:
                color = 'red'
            
            words.append({
                'word': word_text,
                'score': word_score,
                'color': color,
                'start': start_time,
                'end': end_time,
                'phonemes': phonemes,
                'issues': issues,
                'aligned': True
            })
        
        # Fluency metrics
        fluency_score = api_result.get('fluency', {})
        duration = api_result.get('total_duration_ms', 0) / 1000.0
        
        fluency = {
            'duration': round(duration, 1),
            'words_per_min': fluency_score.get('wpm', 0),
            'avg_pause': fluency_score.get('avg_pause_len', 0),
            'fluency_score': fluency_score.get('overall', 0)
        }
        
        return {
            'overall_score': round(overall_score, 1),
            'words': words,
            'total_words': len(words),
            'aligned_words': len(words),
            'fluency': fluency,
            'alignment_method': 'speechace',
            'api_raw': api_result  # Keep raw response for debugging
        }


def get_scorer() -> SpeechaceScorer:
    """Get singleton scorer instance."""
    global _scorer
    if '_scorer' not in globals():
        _scorer = SpeechaceScorer()
    return _scorer


if __name__ == "__main__":
    # Test
    import sys
    
    if not os.getenv("SPEECHACE_API_KEY"):
        print("❌ SPEECHACE_API_KEY not set!")
        print("\nGet free API key at: https://www.speechace.com/api/")
        print("Then: export SPEECHACE_API_KEY='your_key_here'")
        sys.exit(1)
    
    scorer = get_scorer()
    
    # Test on Russian accent audio
    test_audio = "test_data/russian_accent/russian1.mp3"
    test_text = "Please call Stella."
    
    if Path(test_audio).exists():
        print(f"Testing: {test_audio}")
        print(f"Reference: {test_text}\n")
        
        result = scorer.score_pronunciation(test_audio, test_text)
        
        print(f"Overall score: {result['overall_score']}/100\n")
        
        for word in result['words']:
            emoji = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}.get(word['color'], '⚪')
            print(f"{emoji} {word['word']:15s} {word['score']:5.1f}/100")
            if word['issues']:
                print(f"   Issues: {', '.join(word['issues'])}")
        
        print(f"\nFluency: {result['fluency']['words_per_min']} WPM")
    else:
        print(f"Test file not found: {test_audio}")
