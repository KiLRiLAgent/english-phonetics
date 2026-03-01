#!/usr/bin/env python3
"""
Gentle-based forced aligner for pronunciation analysis.
Replaces Wav2Vec2 approach with Kaldi-backed Gentle (via Docker).
"""

import requests
import json
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
from g2p_en import G2p

GENTLE_URL = "http://localhost:8765"

# Initialize G2P for expected phonemes
g2p = G2p()

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
    ('l', 'r'): 'l/r confusion'
}


def align_audio(audio_path: str, transcript: str) -> Dict:
    """
    Align audio with transcript using Gentle.
    
    Args:
        audio_path: Path to audio file (wav/mp3)
        transcript: Reference text
    
    Returns:
        Gentle alignment result (JSON dict)
    """
    with open(audio_path, 'rb') as audio_file:
        files = {
            'audio': audio_file,
            'transcript': (None, transcript)
        }
        response = requests.post(
            f"{GENTLE_URL}/transcriptions?async=false",
            files=files
        )
    
    if response.status_code != 200:
        raise Exception(f"Gentle API error: {response.status_code}")
    
    return response.json()


def normalize_phone(phone: str) -> str:
    """Remove stress markers and position suffixes from Gentle phones."""
    # Gentle uses: phone_B (begin), phone_I (internal), phone_E (end)
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
    # Normalize both lists (remove stress markers, position markers)
    actual = [normalize_phone(p) for p in actual_phones]
    # Remove stress markers from g2p output (0, 1, 2) and word boundaries
    expected = [''.join(c for c in p.lower() if not c.isdigit()) 
                for p in expected_phonemes if p not in ['<', '>']]
    
    if not expected:
        return 100.0, []
    
    # Simple comparison (can enhance with edit distance later)
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


def score_pronunciation(alignment: Dict) -> List[Dict]:
    """
    Score each word based on Gentle alignment + phoneme comparison.
    
    Args:
        alignment: Gentle JSON output
    
    Returns:
        List of word scores with details
    """
    words = alignment.get('words', [])
    results = []
    
    for idx, word_data in enumerate(words):
        word = word_data.get('word', '')
        case = word_data.get('case', 'not-found-in-audio')
        
        # Get expected phonemes from g2p
        try:
            expected_phonemes = g2p(word)
        except:
            expected_phonemes = []
        
        # Gentle cases: "success", "not-found-in-audio", "hmm"
        if case == 'success':
            # Extract phoneme data
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
            expected_ipa = ' '.join(GENTLE_TO_IPA.get(p.lower(), p.lower()) 
                                   for p in expected_phonemes if p not in ['<', '>'])
            
            results.append({
                'word': word,
                'score': round(score, 1),
                'color': color,
                'start': start,
                'end': end,
                'phones': phones,
                'actual_ipa': actual_ipa,
                'expected_ipa': expected_ipa,
                'issues': issues
            })
        
        elif case == 'not-found-in-audio':
            # Word not found = major issue
            expected_ipa = ' '.join(GENTLE_TO_IPA.get(p.lower(), p.lower()) 
                                   for p in expected_phonemes if p not in ['<', '>'])
            results.append({
                'word': word,
                'score': 0,
                'color': 'red',
                'start': None,
                'end': None,
                'phones': [],
                'actual_ipa': '(не произнесено)',
                'expected_ipa': expected_ipa,
                'issues': ['Word not found in audio']
            })
        
        else:  # "hmm" or other
            # Partial match
            expected_ipa = ' '.join(GENTLE_TO_IPA.get(p.lower(), p.lower()) 
                                   for p in expected_phonemes if p not in ['<', '>'])
            results.append({
                'word': word,
                'score': 40,
                'color': 'yellow',
                'start': word_data.get('start'),
                'end': word_data.get('end'),
                'phones': word_data.get('phones', []),
                'actual_ipa': '(неуверенно)',
                'expected_ipa': expected_ipa,
                'issues': ['Uncertain alignment']
            })
    
    return results


def analyze_with_gentle(audio_path: str, reference_text: str) -> Dict:
    """
    Full pronunciation analysis using Gentle.
    
    Args:
        audio_path: Path to audio file
        reference_text: Expected transcript
    
    Returns:
        Analysis report compatible with existing UI
    """
    # Get Gentle alignment
    alignment = align_audio(audio_path, reference_text)
    
    # Score each word
    word_scores = score_pronunciation(alignment)
    
    # Calculate overall score
    valid_scores = [w['score'] for w in word_scores if w['score'] is not None]
    overall_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    
    # Build report
    report = {
        'audio_path': audio_path,
        'reference_text': reference_text,
        'overall_score': round(overall_score, 1),
        'word_count': len(word_scores),
        'words': word_scores,
        'gentle_raw': alignment  # Keep raw Gentle output for debugging
    }
    
    return report


if __name__ == '__main__':
    # Test with sample audio
    test_audio = "test_data/russian_accent/russian1.mp3"
    test_text = "Please call Stella."
    
    if Path(test_audio).exists():
        print(f"Analyzing: {test_audio}")
        print(f"Reference: {test_text}\n")
        
        print("Calling Gentle API...")
        result = analyze_with_gentle(test_audio, test_text)
        print("Analysis complete!")
        
        print(f"\nOverall score: {result['overall_score']}/100")
        print(f"\nWord-by-word:")
        for word in result['words']:
            color_emoji = {'green': '🟢', 'yellow': '🟡', 'red': '🔴'}.get(word['color'], '⚪')
            print(f"{color_emoji} {word['word']}: {word['score']}/100")
            print(f"   Actual: {word['actual_ipa']}")
            print(f"   Expected: {word.get('expected_ipa', 'N/A')}")
            if word['issues']:
                print(f"   Issues: {', '.join(word['issues'])}")
    else:
        print(f"Test file not found: {test_audio}")
