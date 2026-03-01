#!/usr/bin/env python3
"""
Phoneme-level GOP Scorer v2
Improvements over v1:
- DTW alignment instead of SequenceMatcher
- Per-word phoneme breakdown
- GOP scoring using wav2vec2 log probabilities
- Visual color-coded report
"""

import json
import sys
import re
import numpy as np
import torch
import torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from g2p_en import G2p
from fastdtw import fastdtw

# ── Mappings ──────────────────────────────────────────────────────────────

ARPABET_TO_IPA = {
    'AA': 'ɑ', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔ', 'AW': 'aʊ',
    'AY': 'aɪ', 'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð',
    'EH': 'ɛ', 'ER': 'ɝ', 'EY': 'eɪ', 'F': 'f', 'G': 'ɡ',
    'HH': 'h', 'IH': 'ɪ', 'IY': 'iː', 'JH': 'dʒ', 'K': 'k',
    'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ', 'OW': 'oʊ',
    'OY': 'ɔɪ', 'P': 'p', 'R': 'ɹ', 'S': 's', 'SH': 'ʃ',
    'T': 't', 'TH': 'θ', 'UH': 'ʊ', 'UW': 'uː', 'V': 'v',
    'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ',
}

NORMALIZE_MAP = {
    'ɑː': 'ɑ', 'ɒ': 'ɑ', 'ɔː': 'ɔ',
    'ɐ': 'ʌ', 'ə': 'ʌ',
    'ɝ': 'ɝ', 'ɜː': 'ɝ', 'ɜ': 'ɝ', 'ɚ': 'ɝ',
    'e': 'ɛ', 'i': 'ɪ', 'u': 'ʊ',
    'aw': 'aʊ', 'aj': 'aɪ', 'ej': 'eɪ',
    'ow': 'oʊ', 'o': 'oʊ', 'oj': 'ɔɪ',
    'r': 'ɹ', 'ɾ': 'ɹ', 'g': 'ɡ',
    'ʧ': 'tʃ', 'ʤ': 'dʒ',
}

# Phoneme similarity groups for DTW distance
VOWELS = set('ɑæʌɔɛɪʊəɝ')
DIPHTHONGS = {'aʊ', 'aɪ', 'eɪ', 'oʊ', 'ɔɪ', 'iː', 'uː'}
VOICED_STOPS = set('bdɡ')
UNVOICED_STOPS = set('ptk')
FRICATIVES_VOICED = {'v', 'ð', 'z', 'ʒ'}
FRICATIVES_UNVOICED = {'f', 'θ', 's', 'ʃ'}
NASALS = {'m', 'n', 'ŋ'}
APPROXIMANTS = {'l', 'ɹ', 'w', 'j'}

PHONEME_NAMES = {
    'θ': 'th (thin)', 'ð': 'th (this)', 'ʃ': 'sh', 'ʒ': 'zh',
    'tʃ': 'ch', 'dʒ': 'j', 'ŋ': 'ng', 'ɹ': 'r',
    'ɑ': 'ah', 'æ': 'a', 'ʌ': 'uh', 'ɔ': 'aw',
    'aʊ': 'ow', 'aɪ': 'eye', 'ɛ': 'eh', 'ɝ': 'er',
    'eɪ': 'ay', 'ɪ': 'ih', 'iː': 'ee', 'oʊ': 'oh',
    'ɔɪ': 'oy', 'ʊ': 'oo', 'uː': 'oo-long', 'ɡ': 'g',
}


def normalize_phoneme(ph: str) -> str:
    if ph in NORMALIZE_MAP:
        return NORMALIZE_MAP[ph]
    return ph


def _get_group(ph: str):
    if ph in DIPHTHONGS:
        return 'diphthong'
    if len(ph) == 1 and ph in VOWELS:
        return 'vowel'
    if ph in VOICED_STOPS:
        return 'voiced_stop'
    if ph in UNVOICED_STOPS:
        return 'unvoiced_stop'
    if ph in FRICATIVES_VOICED:
        return 'voiced_fric'
    if ph in FRICATIVES_UNVOICED:
        return 'unvoiced_fric'
    if ph in NASALS:
        return 'nasal'
    if ph in APPROXIMANTS:
        return 'approx'
    return 'other'


def phoneme_distance(a: str, b: str) -> float:
    """Distance metric for DTW: 0=same, 0.5=similar class, 1=different."""
    na, nb = normalize_phoneme(a), normalize_phoneme(b)
    if na == nb:
        return 0.0
    ga, gb = _get_group(na), _get_group(nb)
    if ga == gb:
        return 0.3
    # Voiced/unvoiced pairs
    if {ga, gb} == {'voiced_stop', 'unvoiced_stop'}:
        return 0.4
    if {ga, gb} == {'voiced_fric', 'unvoiced_fric'}:
        return 0.4
    # Vowel/diphthong
    if {ga, gb} <= {'vowel', 'diphthong'}:
        return 0.5
    return 1.0


def get_phoneme_name(ph):
    return PHONEME_NAMES.get(ph, ph)


class PhonemeScorer:
    def __init__(self, model_name="facebook/wav2vec2-lv-60-espeak-cv-ft"):
        print(f"Loading wav2vec2 phoneme model: {model_name}")
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
        self.model.eval()
        self.g2p = G2p()
        
        # Build phoneme-to-token-id mapping for GOP
        self.vocab = self.processor.tokenizer.get_vocab()
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        print(f"Models loaded. Vocab size: {len(self.vocab)}")

    def text_to_phonemes(self, text: str) -> list[str]:
        """Convert text to IPA phonemes via g2p-en."""
        arpabet = self.g2p(text)
        ipa = []
        for ph in arpabet:
            clean = ph.rstrip('012')
            if clean in ARPABET_TO_IPA:
                ipa.append(ARPABET_TO_IPA[clean])
        return ipa

    def text_to_word_phonemes(self, text: str) -> list[dict]:
        """Convert text to per-word phoneme lists."""
        words = re.findall(r"[a-zA-Z']+", text)
        result = []
        for word in words:
            arpabet = self.g2p(word)
            ipa = []
            for ph in arpabet:
                clean = ph.rstrip('012')
                if clean in ARPABET_TO_IPA:
                    ipa.append(ARPABET_TO_IPA[clean])
            result.append({'word': word, 'phonemes': ipa})
        return result

    def audio_to_phonemes_with_logits(self, audio_path: str):
        """
        Recognize phonemes from audio.
        Returns: phonemes, confidences, frame_log_probs (T x V), frame_phoneme_ids
        """
        waveform, sr = torchaudio.load(audio_path)
        if sr != 16000:
            waveform = torchaudio.transforms.Resample(sr, 16000)(waveform)
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)

        input_values = self.processor(
            waveform.squeeze().numpy(),
            sampling_rate=16000,
            return_tensors="pt"
        ).input_values

        with torch.no_grad():
            logits = self.model(input_values).logits  # (1, T, V)

        log_probs = torch.log_softmax(logits, dim=-1)[0]  # (T, V)
        probs = torch.softmax(logits, dim=-1)[0]
        predicted_ids = torch.argmax(logits, dim=-1)[0]
        
        blank_id = self.processor.tokenizer.pad_token_id

        # CTC decode with frame tracking
        phonemes = []
        confidences = []
        frame_ranges = []  # (start_frame, end_frame) for each phoneme
        prev_id = -1
        current_start = 0

        for i, token_id in enumerate(predicted_ids):
            tid = token_id.item()
            if tid != prev_id:
                if prev_id != -1 and prev_id != blank_id:
                    token = self.processor.decode([prev_id]).strip()
                    if token and token not in (' ', '|', '<pad>', '<s>', '</s>'):
                        phonemes.append(token)
                        confidences.append(probs[current_start, prev_id].item())
                        frame_ranges.append((current_start, i))
                current_start = i
            prev_id = tid

        # Last token
        if prev_id != -1 and prev_id != blank_id:
            token = self.processor.decode([prev_id]).strip()
            if token and token not in (' ', '|', '<pad>', '<s>', '</s>'):
                phonemes.append(token)
                confidences.append(probs[current_start, prev_id].item())
                frame_ranges.append((current_start, len(predicted_ids)))

        return phonemes, confidences, log_probs.numpy(), frame_ranges

    def compute_gop(self, expected_phoneme: str, frame_range: tuple, log_probs: np.ndarray) -> float:
        """
        Compute GOP score for a phoneme over a frame range.
        GOP = mean log P(expected_phoneme | frames)
        
        We find the best matching token in vocab for the expected phoneme,
        then compute mean log probability over the frame range.
        """
        start, end = frame_range
        if start >= end:
            return -10.0
        
        # Find token id for expected phoneme
        norm_ph = normalize_phoneme(expected_phoneme)
        
        # Search vocab for best match
        best_id = None
        for token_str, token_id in self.vocab.items():
            token_norm = normalize_phoneme(token_str.strip())
            if token_norm == norm_ph or token_str.strip() == expected_phoneme:
                best_id = token_id
                break
        
        if best_id is None:
            # Fallback: find closest by string
            for token_str, token_id in self.vocab.items():
                if expected_phoneme in token_str or token_str.strip() in expected_phoneme:
                    best_id = token_id
                    break
        
        if best_id is None:
            return -5.0  # Unknown phoneme
        
        # Mean log prob over frames
        frame_lps = log_probs[start:end, best_id]
        gop = float(np.mean(frame_lps))
        return gop

    def dtw_align(self, expected: list[str], actual: list[str]):
        """
        Align expected and actual phonemes using DTW.
        Returns list of (exp_idx, act_idx) pairs.
        """
        if not expected or not actual:
            return []
        
        n, m = len(expected), len(actual)
        # Build cost matrix
        cost = np.full((n + 1, m + 1), np.inf)
        cost[0, 0] = 0.0
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                d = phoneme_distance(expected[i-1], actual[j-1])
                cost[i, j] = d + min(cost[i-1, j], cost[i, j-1], cost[i-1, j-1])
        
        # Backtrack
        path = []
        i, j = n, m
        while i > 0 and j > 0:
            path.append((i-1, j-1))
            candidates = [
                (cost[i-1, j-1], i-1, j-1),
                (cost[i-1, j], i-1, j),
                (cost[i, j-1], i, j-1),
            ]
            _, i, j = min(candidates, key=lambda x: x[0])
        path.reverse()
        return path

    def score(self, audio_path: str, reference_text: str) -> dict:
        """Full scoring pipeline with DTW + GOP + per-word breakdown."""
        print("Converting reference text to per-word phonemes...")
        word_phonemes = self.text_to_word_phonemes(reference_text)
        all_expected = []
        for wp in word_phonemes:
            all_expected.extend(wp['phonemes'])
        print(f"Expected phonemes: {len(all_expected)}")

        print("Recognizing phonemes from audio...")
        actual, confidences, log_probs, frame_ranges = self.audio_to_phonemes_with_logits(audio_path)
        print(f"Recognized phonemes: {len(actual)}")

        print("DTW alignment...")
        path = self.dtw_align(all_expected, actual)

        # Build alignment map: for each expected phoneme idx, best actual idx
        exp_to_act = {}
        for ei, ai in path:
            if ei not in exp_to_act:
                exp_to_act[ei] = ai

        # Compute per-phoneme scores
        phoneme_results = []
        for ei, exp_ph in enumerate(all_expected):
            ai = exp_to_act.get(ei)
            if ai is not None and ai < len(actual):
                act_ph = actual[ai]
                dist = phoneme_distance(exp_ph, act_ph)
                conf = confidences[ai] if ai < len(confidences) else 0.0
                gop = self.compute_gop(exp_ph, frame_ranges[ai], log_probs) if ai < len(frame_ranges) else -10.0
                
                # Combined score: 0-100
                match_score = max(0, (1.0 - dist)) * 100
                # Blend: 60% match quality, 40% GOP-based
                gop_norm = max(0, min(100, (gop + 5) * 20))  # map [-5,0] → [0,100]
                combined = 0.6 * match_score + 0.4 * gop_norm
                
                phoneme_results.append({
                    'expected': exp_ph,
                    'actual': act_ph,
                    'distance': round(dist, 2),
                    'confidence': round(conf, 3),
                    'gop': round(gop, 2),
                    'score': round(combined, 1),
                    'match': dist == 0.0,
                })
            else:
                phoneme_results.append({
                    'expected': exp_ph,
                    'actual': '∅',
                    'distance': 1.0,
                    'confidence': 0.0,
                    'gop': -10.0,
                    'score': 0.0,
                    'match': False,
                })

        # Per-word breakdown
        idx = 0
        word_results = []
        for wp in word_phonemes:
            n = len(wp['phonemes'])
            word_prs = phoneme_results[idx:idx + n]
            idx += n
            
            if word_prs:
                word_score = np.mean([p['score'] for p in word_prs])
                matches = sum(1 for p in word_prs if p['match'])
            else:
                word_score = 0
                matches = 0
            
            word_results.append({
                'word': wp['word'],
                'expected_phonemes': wp['phonemes'],
                'actual_phonemes': [p['actual'] for p in word_prs],
                'phoneme_details': word_prs,
                'score': round(float(word_score), 1),
                'matches': matches,
                'total': n,
                'quality': 'good' if word_score >= 70 else 'fair' if word_score >= 40 else 'poor',
            })

        # Overall stats
        total = len(phoneme_results)
        correct = sum(1 for p in phoneme_results if p['match'])
        avg_score = float(np.mean([p['score'] for p in phoneme_results])) if phoneme_results else 0

        # Error patterns
        error_patterns = {}
        for p in phoneme_results:
            if not p['match'] and p['actual'] != '∅':
                key = f"{p['expected']} → {p['actual']}"
                error_patterns[key] = error_patterns.get(key, 0) + 1
        sorted_patterns = sorted(error_patterns.items(), key=lambda x: -x[1])

        return {
            'overall_score': round(avg_score, 1),
            'phoneme_accuracy': round(correct / total * 100, 1) if total else 0,
            'total_expected': total,
            'total_actual': len(actual),
            'correct': correct,
            'error_count': total - correct,
            'word_results': word_results,
            'phoneme_results': phoneme_results,
            'error_patterns': [
                {'pattern': k, 'count': v,
                 'readable': f"{get_phoneme_name(k.split(' → ')[0])} → {get_phoneme_name(k.split(' → ')[1])}"}
                for k, v in sorted_patterns[:20]
            ],
            'reference_text': reference_text,
        }


def format_report(result: dict) -> str:
    """Format color-coded visual report."""
    lines = []
    lines.append("=" * 65)
    lines.append("  PHONEME PRONUNCIATION ANALYSIS v2 (DTW + GOP)")
    lines.append("=" * 65)
    lines.append(f"\n📊 Overall Score: {result['overall_score']:.1f}/100")
    lines.append(f"🎯 Phoneme Accuracy: {result['phoneme_accuracy']}%")
    lines.append(f"📝 Expected: {result['total_expected']} | Recognized: {result['total_actual']} | Correct: {result['correct']}")

    # Per-word breakdown with color
    lines.append(f"\n{'─' * 65}")
    lines.append("  PER-WORD BREAKDOWN")
    lines.append(f"{'─' * 65}")

    for wr in result['word_results']:
        # Color indicator
        if wr['quality'] == 'good':
            indicator = '🟢'
        elif wr['quality'] == 'fair':
            indicator = '🟡'
        else:
            indicator = '🔴'

        exp_str = ' '.join(wr['expected_phonemes'])
        act_str = ' '.join(wr['actual_phonemes'])
        lines.append(f"\n{indicator} {wr['word']:20s}  score: {wr['score']:5.1f}  ({wr['matches']}/{wr['total']})")
        lines.append(f"   Expected: {exp_str}")
        lines.append(f"   Actual:   {act_str}")

    # Top errors
    if result['error_patterns']:
        lines.append(f"\n{'─' * 65}")
        lines.append("  TOP ERROR PATTERNS")
        lines.append(f"{'─' * 65}")
        for p in result['error_patterns'][:15]:
            lines.append(f"  {p['readable']:40s} ×{p['count']}")

    return "\n".join(lines)


def format_telegram_report(result: dict) -> str:
    """Compact report for Telegram."""
    lines = []
    lines.append("📊 *Phoneme Analysis v2 (DTW+GOP)*")
    lines.append(f"Score: *{result['overall_score']:.1f}/100* | Accuracy: *{result['phoneme_accuracy']}%*")
    lines.append(f"Phonemes: {result['correct']}/{result['total_expected']} correct\n")

    # Words grouped by quality
    poor = [w for w in result['word_results'] if w['quality'] == 'poor']
    fair = [w for w in result['word_results'] if w['quality'] == 'fair']
    good = [w for w in result['word_results'] if w['quality'] == 'good']

    lines.append(f"🟢 Good ({len(good)}): {', '.join(w['word'] for w in good[:20])}")
    if len(good) > 20:
        lines.append(f"   ...and {len(good)-20} more")
    lines.append(f"🟡 Fair ({len(fair)}): {', '.join(w['word'] for w in fair[:15])}")
    lines.append(f"🔴 Poor ({len(poor)}): {', '.join(w['word'] for w in poor[:15])}")

    # Worst words detail
    worst = sorted(result['word_results'], key=lambda w: w['score'])[:10]
    lines.append(f"\n*Top 10 worst words:*")
    for w in worst:
        exp = ' '.join(w['expected_phonemes'])
        act = ' '.join(w['actual_phonemes'])
        lines.append(f"🔴 *{w['word']}* ({w['score']:.0f})")
        lines.append(f"  exp: {exp}")
        lines.append(f"  got: {act}")

    # Error patterns
    if result['error_patterns']:
        lines.append(f"\n*Top error patterns:*")
        for p in result['error_patterns'][:10]:
            lines.append(f"  {p['readable']} ×{p['count']}")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phoneme scorer v2")
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
