#!/usr/bin/env python3
"""
Phoneme-level GOP (Goodness of Pronunciation) Scorer
Uses wav2vec2 phoneme recognition + g2p for reference phonemes.
Compares expected vs actual phonemes with alignment scoring.
"""

import json
import sys
import numpy as np
import torch
import torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from g2p_en import G2p
from difflib import SequenceMatcher


# Mapping from ARPAbet (g2p-en output) to IPA (wav2vec2 output)
ARPABET_TO_IPA = {
    'AA': 'ɑː', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔː', 'AW': 'aʊ',
    'AY': 'aɪ', 'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð',
    'EH': 'ɛ', 'ER': 'ɝ', 'EY': 'eɪ', 'F': 'f', 'G': 'ɡ',
    'HH': 'h', 'IH': 'ɪ', 'IY': 'iː', 'JH': 'dʒ', 'K': 'k',
    'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ', 'OW': 'oʊ',
    'OY': 'ɔɪ', 'P': 'p', 'R': 'ɹ', 'S': 's', 'SH': 'ʃ',
    'T': 't', 'TH': 'θ', 'UH': 'ʊ', 'UW': 'uː', 'V': 'v',
    'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ',
}

# Simplified IPA grouping for fuzzy matching
IPA_GROUPS = {
    'plosives': set('pbtdkɡ'),
    'fricatives': {'f', 'v', 'θ', 'ð', 's', 'z', 'ʃ', 'ʒ', 'h'},
    'nasals': {'m', 'n', 'ŋ'},
    'approximants': {'l', 'ɹ', 'w', 'j'},
}

# Normalization: map various IPA variants to canonical forms
# This handles differences between g2p-en output and wav2vec2 output
NORMALIZE_MAP = {
    # Vowels
    'ɑː': 'ɑ', 'ɑ': 'ɑ', 'ɒ': 'ɑ',
    'ɔː': 'ɔ', 'ɔ': 'ɔ',
    'æ': 'æ',
    'ʌ': 'ʌ', 'ɐ': 'ʌ',  # wav2vec2 uses ɐ for schwa/ʌ
    'ə': 'ə', 
    'ɝ': 'ɝ', 'ɜː': 'ɝ', 'ɜ': 'ɝ', 'ɚ': 'ɝ',  # r-colored vowels
    'ɛ': 'ɛ', 'e': 'ɛ',
    'ɪ': 'ɪ', 'i': 'ɪ',
    'iː': 'iː', 
    'ʊ': 'ʊ', 'u': 'ʊ',
    'uː': 'uː',
    # Diphthongs
    'aʊ': 'aʊ', 'aw': 'aʊ',
    'aɪ': 'aɪ', 'aj': 'aɪ',
    'eɪ': 'eɪ', 'ej': 'eɪ',
    'oʊ': 'oʊ', 'ow': 'oʊ', 'o': 'oʊ',
    'ɔɪ': 'ɔɪ', 'oj': 'ɔɪ',
    # Consonants (most are the same)
    'ɹ': 'ɹ', 'r': 'ɹ', 'ɾ': 'ɹ',
    'ɡ': 'ɡ', 'g': 'ɡ',
    'tʃ': 'tʃ', 'ʧ': 'tʃ',
    'dʒ': 'dʒ', 'ʤ': 'dʒ',
    'ŋ': 'ŋ',
    'θ': 'θ', 'ð': 'ð',
    'ʃ': 'ʃ', 'ʒ': 'ʒ',
}

def normalize_phoneme(ph: str) -> str:
    """Normalize a phoneme to canonical form."""
    if ph in NORMALIZE_MAP:
        return NORMALIZE_MAP[ph]
    return ph

# Human-readable phoneme names
PHONEME_NAMES = {
    'θ': 'th (thin)', 'ð': 'th (this)', 'ʃ': 'sh', 'ʒ': 'zh',
    'tʃ': 'ch', 'dʒ': 'j', 'ŋ': 'ng', 'ɹ': 'r',
    'ɑː': 'ah', 'æ': 'a', 'ʌ': 'uh', 'ɔː': 'aw',
    'aʊ': 'ow', 'aɪ': 'eye', 'ɛ': 'eh', 'ɝ': 'er',
    'eɪ': 'ay', 'ɪ': 'ih', 'iː': 'ee', 'oʊ': 'oh',
    'ɔɪ': 'oy', 'ʊ': 'oo (book)', 'uː': 'oo (food)',
    'ɡ': 'g',
}


def get_phoneme_name(ph):
    return PHONEME_NAMES.get(ph, ph)


class PhonemeScorer:
    def __init__(self, model_name="facebook/wav2vec2-lv-60-espeak-cv-ft"):
        print(f"Loading wav2vec2 phoneme model: {model_name}")
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
        self.model.eval()
        self.g2p = G2p()
        print("Models loaded.")

    def text_to_phonemes(self, text: str) -> list[str]:
        """Convert text to expected IPA phonemes via g2p-en (ARPAbet) → IPA."""
        arpabet = self.g2p(text)
        ipa_phonemes = []
        for ph in arpabet:
            # Strip stress markers (0,1,2)
            clean = ph.rstrip('012')
            if clean in ARPABET_TO_IPA:
                ipa_phonemes.append(ARPABET_TO_IPA[clean])
            # skip spaces and punctuation
        return ipa_phonemes

    def audio_to_phonemes(self, audio_path: str) -> tuple[list[str], list[float]]:
        """Recognize phonemes from audio using wav2vec2. Returns (phonemes, confidence_scores)."""
        waveform, sr = torchaudio.load(audio_path)
        # Resample to 16kHz if needed
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            waveform = resampler(waveform)
        # Mono
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        input_values = self.processor(
            waveform.squeeze().numpy(), 
            sampling_rate=16000, 
            return_tensors="pt"
        ).input_values

        with torch.no_grad():
            logits = self.model(input_values).logits

        # Get probabilities
        probs = torch.softmax(logits, dim=-1)
        predicted_ids = torch.argmax(logits, dim=-1)[0]
        
        # Decode with CTC (collapse repeats, remove blanks)
        phonemes = []
        confidences = []
        prev_id = -1
        blank_id = self.processor.tokenizer.pad_token_id
        
        for i, token_id in enumerate(predicted_ids):
            tid = token_id.item()
            if tid != prev_id and tid != blank_id:
                token = self.processor.decode([tid]).strip()
                if token and token not in (' ', '|', '<pad>', '<s>', '</s>'):
                    phonemes.append(token)
                    confidences.append(probs[0, i, tid].item())
            prev_id = tid

        return phonemes, confidences

    def align_and_score(self, expected: list[str], actual: list[str], 
                        actual_conf: list[str]) -> dict:
        """Align expected vs actual phonemes and compute scores."""
        # Normalize both lists for comparison
        norm_expected = [normalize_phoneme(p) for p in expected]
        norm_actual = [normalize_phoneme(p) for p in actual]
        
        # Use SequenceMatcher for alignment on normalized forms
        matcher = SequenceMatcher(None, norm_expected, norm_actual)
        
        alignments = []
        errors = []
        correct = 0
        total = len(expected)
        
        for op, i1, i2, j1, j2 in matcher.get_opcodes():
            if op == 'equal':
                for k in range(i2 - i1):
                    ei = i1 + k
                    ai = j1 + k
                    conf = actual_conf[ai] if ai < len(actual_conf) else 0.5
                    alignments.append({
                        'expected': expected[ei],
                        'actual': actual[ai],
                        'status': 'correct',
                        'confidence': round(conf, 3),
                    })
                    correct += 1
            elif op == 'replace':
                for k in range(max(i2 - i1, j2 - j1)):
                    ei = i1 + k if (i1 + k) < i2 else None
                    ai = j1 + k if (j1 + k) < j2 else None
                    exp_ph = expected[ei] if ei is not None else '∅'
                    act_ph = actual[ai] if ai is not None else '∅'
                    exp_norm = normalize_phoneme(exp_ph) if exp_ph != '∅' else '∅'
                    act_norm = normalize_phoneme(act_ph) if act_ph != '∅' else '∅'
                    conf = actual_conf[ai] if ai is not None and ai < len(actual_conf) else 0.0
                    
                    # Check if they match after normalization
                    if exp_norm == act_norm and exp_norm != '∅':
                        alignments.append({
                            'expected': exp_ph,
                            'actual': act_ph,
                            'status': 'correct',
                            'confidence': round(conf, 3),
                        })
                        correct += 1
                    else:
                        alignments.append({
                            'expected': exp_ph,
                            'actual': act_ph,
                            'status': 'substitution',
                            'confidence': round(conf, 3),
                        })
                        if exp_ph != '∅':
                            errors.append({
                                'type': 'substitution',
                                'expected': exp_ph,
                                'expected_name': get_phoneme_name(exp_ph),
                                'actual': act_ph,
                                'actual_name': get_phoneme_name(act_ph),
                                'description': f'"{get_phoneme_name(exp_ph)}" → "{get_phoneme_name(act_ph)}"',
                            })
            elif op == 'delete':
                for k in range(i2 - i1):
                    ei = i1 + k
                    alignments.append({
                        'expected': expected[ei],
                        'actual': '∅',
                        'status': 'deletion',
                        'confidence': 0.0,
                    })
                    errors.append({
                        'type': 'deletion',
                        'expected': expected[ei],
                        'expected_name': get_phoneme_name(expected[ei]),
                        'actual': '∅',
                        'actual_name': 'missing',
                        'description': f'"{get_phoneme_name(expected[ei])}" was dropped',
                    })
            elif op == 'insert':
                for k in range(j2 - j1):
                    ai = j1 + k
                    conf = actual_conf[ai] if ai < len(actual_conf) else 0.5
                    alignments.append({
                        'expected': '∅',
                        'actual': actual[ai],
                        'status': 'insertion',
                        'confidence': round(conf, 3),
                    })
                    errors.append({
                        'type': 'insertion',
                        'expected': '∅',
                        'expected_name': 'nothing',
                        'actual': actual[ai],
                        'actual_name': get_phoneme_name(actual[ai]),
                        'description': f'extra "{get_phoneme_name(actual[ai])}" inserted',
                    })
        
        # Compute overall score
        accuracy = correct / total * 100 if total > 0 else 0
        
        # Count error patterns (common L1 interference)
        error_patterns = {}
        for e in errors:
            if e['type'] == 'substitution':
                key = f"{e['expected']} → {e['actual']}"
                error_patterns[key] = error_patterns.get(key, 0) + 1
        
        # Sort by frequency
        sorted_patterns = sorted(error_patterns.items(), key=lambda x: -x[1])
        
        return {
            'overall_score': round(accuracy, 1),
            'total_expected': total,
            'total_actual': len(actual),
            'correct': correct,
            'error_count': len(errors),
            'error_rate': round(len(errors) / total * 100, 1) if total > 0 else 0,
            'errors': errors,
            'error_patterns': [
                {'pattern': k, 'count': v, 
                 'readable': f"{get_phoneme_name(k.split(' → ')[0])} → {get_phoneme_name(k.split(' → ')[1])}"}
                for k, v in sorted_patterns
            ],
            'alignments': alignments,
        }

    def score(self, audio_path: str, reference_text: str) -> dict:
        """Full scoring pipeline."""
        print("Converting reference text to phonemes...")
        expected = self.text_to_phonemes(reference_text)
        print(f"Expected phonemes ({len(expected)}): {' '.join(expected[:30])}...")
        
        print("Recognizing phonemes from audio...")
        actual, confidences = self.audio_to_phonemes(audio_path)
        print(f"Recognized phonemes ({len(actual)}): {' '.join(actual[:30])}...")
        
        print("Aligning and scoring...")
        result = self.align_and_score(expected, actual, confidences)
        result['expected_phonemes'] = expected
        result['actual_phonemes'] = actual
        result['reference_text'] = reference_text
        
        return result


def format_report(result: dict) -> str:
    """Format result as human-readable report."""
    lines = []
    lines.append("=" * 60)
    lines.append("PHONEME-LEVEL PRONUNCIATION ANALYSIS")
    lines.append("=" * 60)
    lines.append(f"\nOverall Phoneme Accuracy: {result['overall_score']}%")
    lines.append(f"Expected phonemes: {result['total_expected']}")
    lines.append(f"Recognized phonemes: {result['total_actual']}")
    lines.append(f"Correct: {result['correct']}")
    lines.append(f"Errors: {result['error_count']} ({result['error_rate']}%)")
    
    if result['error_patterns']:
        lines.append(f"\n{'='*60}")
        lines.append("TOP ERROR PATTERNS (most frequent substitutions):")
        lines.append(f"{'='*60}")
        for p in result['error_patterns'][:15]:
            lines.append(f"  {p['readable']}  (×{p['count']})")
    
    # Show some specific errors
    subs = [e for e in result['errors'] if e['type'] == 'substitution']
    dels = [e for e in result['errors'] if e['type'] == 'deletion']
    ins = [e for e in result['errors'] if e['type'] == 'insertion']
    
    lines.append(f"\nSubstitutions: {len(subs)}, Deletions: {len(dels)}, Insertions: {len(ins)}")
    
    if subs:
        lines.append(f"\nSample substitution errors:")
        for e in subs[:20]:
            lines.append(f"  {e['description']}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phoneme-level pronunciation scorer")
    parser.add_argument("audio", help="Audio file path")
    parser.add_argument("--reference", "-r", required=True, help="Reference text")
    parser.add_argument("--output", "-o", help="Save JSON results")
    args = parser.parse_args()
    
    scorer = PhonemeScorer()
    result = scorer.score(args.audio, args.reference)
    
    print(format_report(result))
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {args.output}")
