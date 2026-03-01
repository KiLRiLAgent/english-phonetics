#!/usr/bin/env python3
"""
Phoneme-level pronunciation scorer using Gentle forced aligner + g2p_en.

Compares actual phonemes (from Gentle/Kaldi) with expected phonemes (from g2p_en)
to detect specific pronunciation errors (th-stopping, vowel reduction, etc.).
"""

import json
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from g2p_en import G2p

# Gentle to IPA mapping (Gentle uses ARPABET-like notation)
GENTLE_TO_IPA = {
    # Vowels
    'aa': 'ɑ', 'ae': 'æ', 'ah': 'ʌ', 'ao': 'ɔ', 'aw': 'aʊ',
    'ax': 'ə', 'ay': 'aɪ', 'eh': 'ɛ', 'er': 'ɝ', 'ey': 'eɪ',
    'ih': 'ɪ', 'iy': 'i', 'ow': 'oʊ', 'oy': 'ɔɪ', 'uh': 'ʊ', 'uw': 'u',
    # Consonants
    'b': 'b', 'ch': 'tʃ', 'd': 'd', 'dh': 'ð', 'f': 'f', 'g': 'ɡ',
    'hh': 'h', 'jh': 'dʒ', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n',
    'ng': 'ŋ', 'p': 'p', 'r': 'ɹ', 's': 's', 'sh': 'ʃ', 't': 't',
    'th': 'θ', 'v': 'v', 'w': 'w', 'y': 'j', 'z': 'z', 'zh': 'ʒ'
}

# Common phoneme substitutions (actual → expected)
SUBSTITUTIONS = {
    ('t', 'th'): 'th-stopping (/θ/ → /t/)',
    ('d', 'dh'): '/ð/ → /d/ substitution',
    ('s', 'z'): 'devoicing (/z/ → /s/)',
    ('z', 's'): 'voicing (/s/ → /z/)',
    ('v', 'w'): '/w/ → /v/ substitution',
    ('w', 'v'): '/v/ → /w/ substitution',
    ('r', 'l'): 'r/l confusion',
    ('l', 'r'): 'l/r confusion',
    ('f', 'th'): '/θ/ → /f/ substitution',
    ('v', 'dh'): '/ð/ → /v/ substitution'
}


def normalize_phone(phone: str) -> str:
    """Remove stress markers and position suffixes from phonemes."""
    # Gentle: phone_B (begin), phone_I (internal), phone_E (end)
    base = phone.split('_')[0].lower()
    # Remove stress markers (0, 1, 2)
    base = ''.join(c for c in base if not c.isdigit())
    return base


def compare_phonemes(actual_phones: List[str], expected_phonemes: List[str]) -> Tuple[float, List[str]]:
    """
    Compare actual (Gentle) vs expected (g2p) phonemes.
    
    Returns:
        (score 0-100, list of issues)
    """
    # Normalize both lists (remove stress, position markers)
    actual = [normalize_phone(p) for p in actual_phones]
    expected = [''.join(c for c in p.lower() if not c.isdigit()) 
                for p in expected_phonemes if p not in ['<', '>']]
    
    if not expected:
        return 100.0, []
    
    # Calculate similarity
    matches = sum(1 for a, e in zip(actual, expected) if a == e)
    total = max(len(actual), len(expected))
    
    if total == 0:
        return 100.0, []
    
    similarity = (matches / total) * 100
    
    # Detect specific substitutions
    issues = []
    for i, (a, e) in enumerate(zip(actual, expected)):
        if a != e:
            sub_key = (a, e)
            if sub_key in SUBSTITUTIONS:
                issues.append(SUBSTITUTIONS[sub_key])
            else:
                # Generic mismatch
                a_ipa = GENTLE_TO_IPA.get(a, a)
                e_ipa = GENTLE_TO_IPA.get(e, e)
                issues.append(f"/{e_ipa}/ → /{a_ipa}/")
    
    return similarity, issues


class GentlePronunciationScorer:
    """
    Forced alignment-based pronunciation scorer using Gentle + g2p_en.
    
    Requires Gentle Docker container:
    docker run -p 8765:8765 lowerquality/gentle
    """
    
    def __init__(self, gentle_url: str = "http://localhost:8765"):
        self.gentle_url = gentle_url
        self.g2p = G2p()
    
    def check_server(self) -> bool:
        """Check if Gentle server is running."""
        try:
            response = requests.get(self.gentle_url, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def align_audio(self, audio_path: str, reference_text: str) -> Dict:
        """
        Align audio with reference text using Gentle.
        
        Args:
            audio_path: Path to audio file (.wav, .mp3)
            reference_text: Expected text
        
        Returns:
            Gentle alignment JSON
        """
        if not self.check_server():
            raise RuntimeError(
                "Gentle server not running. Start with:\n"
                "docker run -p 8765:8765 lowerquality/gentle"
            )
        
        with open(audio_path, 'rb') as audio_file:
            files = {
                'audio': audio_file,
                'transcript': (None, reference_text)
            }
            
            response = requests.post(
                f"{self.gentle_url}/transcriptions?async=false",
                files=files,
                timeout=60
            )
        
        if response.status_code != 200:
            raise RuntimeError(f"Gentle alignment failed: {response.text}")
        
        return response.json()
    
    def score_pronunciation(self, audio_path: str, reference_text: str) -> Dict:
        """
        Score pronunciation by comparing actual vs expected phonemes.
        
        Args:
            audio_path: Path to audio file
            reference_text: Expected text
        
        Returns:
            {
                "words": [
                    {
                        "word": "hello",
                        "score": 85,
                        "color": "green",
                        "start": 0.5,
                        "end": 0.9,
                        "expected_ipa": "h ɛ l oʊ",
                        "actual_ipa": "h ɛ l oʊ",
                        "issues": []
                    },
                    ...
                ],
                "overall_score": 75,
                ...
            }
        """
        # Get alignment from Gentle
        alignment = self.align_audio(audio_path, reference_text)
        
        words_data = alignment.get("words", [])
        scored_words = []
        
        for word_data in words_data:
            word = word_data.get('word', '')
            case = word_data.get('case', 'not-found-in-audio')
            
            # Get expected phonemes from g2p
            try:
                expected_phonemes = self.g2p(word)
            except:
                expected_phonemes = []
            
            # Gentle cases: "success", "not-found-in-audio", "hmm"
            if case == 'success':
                # Successfully aligned
                phones = word_data.get('phones', [])
                start = word_data.get('start', 0)
                end = word_data.get('end', 0)
                
                # Extract actual phonemes
                actual_phones = [p['phone'] for p in phones]
                
                # Compare with expected
                score, issues = compare_phonemes(actual_phones, expected_phonemes)
                
                # Determine color
                if score >= 75:
                    color = 'green'
                elif score >= 50:
                    color = 'yellow'
                else:
                    color = 'red'
                
                # Convert to IPA for display
                actual_ipa = ' '.join(GENTLE_TO_IPA.get(normalize_phone(p), normalize_phone(p)) 
                                     for p in actual_phones)
                expected_ipa = ' '.join(GENTLE_TO_IPA.get(normalize_phone(p), normalize_phone(p)) 
                                       for p in expected_phonemes if p not in ['<', '>'])
                
                scored_words.append({
                    'word': word,
                    'score': round(score, 1),
                    'color': color,
                    'start': start,
                    'end': end,
                    'expected_ipa': expected_ipa,
                    'actual_ipa': actual_ipa,
                    'issues': issues,
                    'aligned': True
                })
            
            elif case == 'not-found-in-audio':
                # Word not found = major error
                expected_ipa = ' '.join(GENTLE_TO_IPA.get(normalize_phone(p), normalize_phone(p)) 
                                       for p in expected_phonemes if p not in ['<', '>'])
                scored_words.append({
                    'word': word,
                    'score': 0,
                    'color': 'red',
                    'start': None,
                    'end': None,
                    'expected_ipa': expected_ipa,
                    'actual_ipa': '(не произнесено)',
                    'issues': ['Word not found in audio'],
                    'aligned': False
                })
            
            else:  # "hmm" or other
                # Uncertain alignment
                expected_ipa = ' '.join(GENTLE_TO_IPA.get(normalize_phone(p), normalize_phone(p)) 
                                       for p in expected_phonemes if p not in ['<', '>'])
                scored_words.append({
                    'word': word,
                    'score': 40,
                    'color': 'yellow',
                    'start': word_data.get('start'),
                    'end': word_data.get('end'),
                    'expected_ipa': expected_ipa,
                    'actual_ipa': '(неуверенно)',
                    'issues': ['Uncertain alignment'],
                    'aligned': False
                })
        
        # Calculate overall score
        valid_scores = [w['score'] for w in scored_words if w.get('aligned', False)]
        overall = sum(valid_scores) / len(valid_scores) if valid_scores else 0
        
        return {
            'words': scored_words,
            'overall_score': round(overall, 1),
            'aligned_words': len(valid_scores),
            'total_words': len(scored_words),
            'alignment_method': 'gentle+g2p',
            'gentle_raw': alignment
        }


def get_scorer() -> GentlePronunciationScorer:
    """Get singleton scorer instance."""
    global _scorer
    if '_scorer' not in globals():
        _scorer = GentlePronunciationScorer()
    return _scorer


if __name__ == "__main__":
    scorer = get_scorer()
    
    if not scorer.check_server():
        print("ERROR: Gentle server not running!")
        print("Start with: docker run -p 8765:8765 lowerquality/gentle")
        exit(1)
    
    # Test
    test_audio = "test_data/russian_accent/russian1.mp3"
    test_text = "Please call Stella."
    
    if Path(test_audio).exists():
        result = scorer.score_pronunciation(test_audio, test_text)
        print(f"Overall score: {result['overall_score']}/100\n")
        for word in result['words']:
            emoji = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}.get(word['color'], '⚪')
            print(f"{emoji} {word['word']}: {word['score']}/100")
            print(f"   Expected: {word['expected_ipa']}")
            print(f"   Actual:   {word['actual_ipa']}")
            if word['issues']:
                print(f"   Issues: {', '.join(word['issues'])}")
