#!/usr/bin/env python3
"""
Phoneme-level GOP (Goodness of Pronunciation) scoring.
Uses Wav2Vec2 for phoneme recognition + g2p_en for expected phonemes.
Compares actual vs expected phonemes per word.
"""

import re
import numpy as np
import torch
import soundfile as sf
from g2p_en import G2p
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

# ARPAbet → IPA mapping (CMU/g2p_en → IPA used by wav2vec2)
ARPA_TO_IPA = {
    'AA': 'ɑː', 'AE': 'æ', 'AH': 'ʌ', 'AO': 'ɔː', 'AW': 'aʊ',
    'AX': 'ə', 'AY': 'aɪ', 'B': 'b', 'CH': 'tʃ', 'D': 'd',
    'DH': 'ð', 'EH': 'ɛ', 'ER': 'ɚ', 'EY': 'eɪ', 'F': 'f',
    'G': 'ɡ', 'HH': 'h', 'IH': 'ɪ', 'IY': 'iː', 'JH': 'dʒ',
    'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ',
    'OW': 'oʊ', 'OY': 'ɔɪ', 'P': 'p', 'R': 'ɹ', 'S': 's',
    'SH': 'ʃ', 'T': 't', 'TH': 'θ', 'UH': 'ʊ', 'UW': 'uː',
    'V': 'v', 'W': 'w', 'Y': 'j', 'Z': 'z', 'ZH': 'ʒ',
}

# Common acceptable substitutions (not penalized as heavily)
# Maps (expected, actual) → penalty multiplier (0=no penalty, 1=full penalty)
ACCEPTABLE_SUBS = {
    # Vowel reductions (very common, acceptable)
    ('ʌ', 'ə'): 0.1, ('ə', 'ʌ'): 0.1,
    ('ɪ', 'ə'): 0.2, ('ə', 'ɪ'): 0.2,
    ('ɑː', 'ɑ'): 0.0, ('ɑ', 'ɑː'): 0.0,
    ('ɔː', 'ɔ'): 0.0, ('ɔ', 'ɔː'): 0.0,
    ('iː', 'i'): 0.0, ('i', 'iː'): 0.0,
    ('uː', 'u'): 0.0, ('u', 'uː'): 0.0,
    # Flapping (American English - t→ɾ between vowels)
    ('t', 'ɾ'): 0.1, ('d', 'ɾ'): 0.1,
    # R variants
    ('ɹ', 'r'): 0.0, ('r', 'ɹ'): 0.0,
    ('ɚ', 'ɹ'): 0.1, ('ɚ', 'ər'): 0.0,
}

# Phoneme similarity groups (for partial credit)
SIMILAR_GROUPS = [
    {'t', 'd'},  # voicing pair
    {'p', 'b'},
    {'k', 'ɡ'},
    {'f', 'v'},
    {'s', 'z'},
    {'ʃ', 'ʒ'},
    {'θ', 'ð'},
    {'tʃ', 'dʒ'},
    {'ɪ', 'iː', 'i'},
    {'ʊ', 'uː', 'u'},
    {'ɛ', 'eɪ'},
    {'ɔ', 'oʊ', 'ɔː'},
    {'ɑ', 'ɑː', 'ʌ'},
]

# Build similarity lookup
_SIM_LOOKUP = {}
for group in SIMILAR_GROUPS:
    for p in group:
        _SIM_LOOKUP[p] = group


def phoneme_similarity(expected: str, actual: str) -> float:
    """Score similarity between two IPA phonemes. 1.0=identical, 0.0=completely different."""
    if expected == actual:
        return 1.0

    # Check acceptable substitutions
    key = (expected, actual)
    if key in ACCEPTABLE_SUBS:
        return 1.0 - ACCEPTABLE_SUBS[key]

    # Check if in same similarity group (partial credit)
    if expected in _SIM_LOOKUP and actual in _SIM_LOOKUP.get(expected, set()):
        return 0.4  # Similar but wrong (e.g. t→d)

    return 0.0  # Completely different


def arpa_to_ipa(arpa_phonemes: list) -> list:
    """Convert ARPAbet phonemes to IPA."""
    result = []
    for p in arpa_phonemes:
        # Strip stress markers (0,1,2)
        base = re.sub(r'[0-9]', '', p)
        if base in ARPA_TO_IPA:
            result.append(ARPA_TO_IPA[base])
        elif p.strip():
            # Skip spaces and punctuation
            if p.strip() not in (' ', ',', '.', '?', '!', '-', "'"):
                result.append(p.lower())
    return result


class PhonemeScorer:
    """Phoneme-level pronunciation scorer using Wav2Vec2."""

    def __init__(self, device: str = None):
        self.device = device or ('cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu')
        print(f"[PhonemeScorer] Loading Wav2Vec2 phoneme model on {self.device}...")
        model_name = "facebook/wav2vec2-lv-60-espeak-cv-ft"
        self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(model_name).to(self.device)
        self.model.eval()
        self.g2p = G2p()

        # Build reverse vocab for decoding with scores
        self.vocab = self.processor.tokenizer.get_vocab()
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        self.pad_id = self.processor.tokenizer.pad_token_id
        self.blank_id = self.vocab.get('<pad>', 0)
        print("[PhonemeScorer] Ready!")

    def recognize_phonemes(self, audio: np.ndarray, sr: int = 16000) -> list:
        """
        Recognize phonemes from audio.
        Returns list of dicts: [{"phoneme": "t", "score": 0.95}, ...]
        """
        if len(audio) < 100:
            return []

        # Ensure 16kHz
        if sr != 16000:
            import torchaudio
            audio_t = torch.tensor(audio, dtype=torch.float32).unsqueeze(0)
            audio_t = torchaudio.functional.resample(audio_t, sr, 16000)
            audio = audio_t.squeeze(0).numpy()
            sr = 16000

        inputs = self.processor(audio, sampling_rate=sr, return_tensors="pt", padding=True)
        input_values = inputs.input_values.to(self.device)

        with torch.no_grad():
            logits = self.model(input_values).logits

        # Get probabilities
        log_probs = torch.nn.functional.log_softmax(logits, dim=-1)
        pred_ids = torch.argmax(logits, dim=-1)[0]

        # CTC decode with scores
        phonemes = []
        prev_id = -1
        for i, pid in enumerate(pred_ids):
            pid = pid.item()
            if pid == self.blank_id or pid == prev_id:
                prev_id = pid
                continue
            token = self.id_to_token.get(pid, '')
            if token and token not in ('<pad>', '<s>', '</s>', '<unk>'):
                score = torch.exp(log_probs[0, i, pid]).item()
                phonemes.append({"phoneme": token, "score": round(score, 3)})
            prev_id = pid

        return phonemes

    def get_expected_phonemes(self, word: str) -> list:
        """Get expected IPA phonemes for a word."""
        # Clean word
        clean = re.sub(r"[^\w']", "", word.lower())
        if not clean:
            return []
        arpa = self.g2p(clean)
        return arpa_to_ipa(arpa)

    def score_word(self, audio: np.ndarray, sr: int, word: str) -> dict:
        """
        Score pronunciation of a single word.
        Returns: {
            "expected_phonemes": [...],
            "actual_phonemes": [...],
            "phoneme_scores": [...],
            "word_score": 0-100,
            "color": "green"/"yellow"/"red",
            "issues": [...]
        }
        """
        expected = self.get_expected_phonemes(word)
        if not expected:
            return {"word_score": 50, "color": "yellow", "expected_phonemes": [],
                    "actual_phonemes": [], "phoneme_scores": [], "issues": []}

        actual_raw = self.recognize_phonemes(audio, sr)
        actual = [p["phoneme"] for p in actual_raw]
        actual_scores = [p["score"] for p in actual_raw]

        # Align expected vs actual using DP
        phoneme_scores, issues = self._align_and_score(expected, actual, actual_scores)

        # Word score = weighted average of phoneme scores
        if phoneme_scores:
            word_score = float(np.mean(phoneme_scores) * 100)
        else:
            word_score = 0.0

        # Color thresholds
        if word_score >= 75:
            color = "green"
        elif word_score >= 50:
            color = "yellow"
        else:
            color = "red"

        return {
            "expected_phonemes": expected,
            "actual_phonemes": actual,
            "phoneme_scores": [round(s, 2) for s in phoneme_scores],
            "word_score": round(word_score, 1),
            "color": color,
            "issues": issues,
        }

    def _align_and_score(self, expected: list, actual: list, actual_scores: list) -> tuple:
        """
        Align expected and actual phonemes, return per-expected-phoneme scores and issues.
        """
        n = len(expected)
        m = len(actual)

        if m == 0:
            return [0.0] * n, [f"Missing: {' '.join(expected)}"]

        # DP alignment
        INF = float('inf')
        cost = [[INF] * (m + 1) for _ in range(n + 1)]
        bt = [[None] * (m + 1) for _ in range(n + 1)]

        cost[0][0] = 0
        for i in range(1, n + 1):
            cost[i][0] = i * 1.0
            bt[i][0] = 'del'
        for j in range(1, m + 1):
            cost[0][j] = j * 0.5  # insertion is less costly
            bt[0][j] = 'ins'

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                sim = phoneme_similarity(expected[i-1], actual[j-1])
                sub_cost = 1.0 - sim
                options = [
                    (cost[i-1][j-1] + sub_cost, 'match'),
                    (cost[i-1][j] + 1.0, 'del'),
                    (cost[i][j-1] + 0.5, 'ins'),
                ]
                best_cost, best_op = min(options, key=lambda x: x[0])
                cost[i][j] = best_cost
                bt[i][j] = best_op

        # Traceback
        alignment = []
        i, j = n, m
        while i > 0 or j > 0:
            if i > 0 and j > 0 and bt[i][j] == 'match':
                alignment.append(('match', i-1, j-1))
                i -= 1; j -= 1
            elif i > 0 and (j == 0 or bt[i][j] == 'del'):
                alignment.append(('del', i-1, None))
                i -= 1
            elif j > 0:
                alignment.append(('ins', None, j-1))
                j -= 1
            else:
                break
        alignment.reverse()

        # Score each expected phoneme
        scores = [0.0] * n
        issues = []

        for op, ei, aj in alignment:
            if op == 'match' and ei is not None and aj is not None:
                sim = phoneme_similarity(expected[ei], actual[aj])
                # Combine similarity with recognition confidence
                conf = actual_scores[aj] if aj < len(actual_scores) else 0.5
                scores[ei] = sim * (0.7 + 0.3 * conf)  # sim matters more than confidence

                if sim < 0.5:
                    issues.append(f"/{expected[ei]}/ → /{actual[aj]}/ (substitution)")
                elif sim < 1.0 and sim >= 0.4:
                    issues.append(f"/{expected[ei]}/ ≈ /{actual[aj]}/")
            elif op == 'del' and ei is not None:
                scores[ei] = 0.0
                issues.append(f"/{expected[ei]}/ missing")

        return scores, issues

    def score_utterance(self, audio_path: str, words: list) -> list:
        """
        Score all words in an utterance.
        words: list of {"word": str, "start": float, "end": float, ...}
        Returns: list of score dicts (same order as words)
        """
        data, sr = sf.read(audio_path)
        if len(data.shape) > 1:
            data = data[:, 0]  # mono

        results = []
        for i, w in enumerate(words):
            # Smart padding: don't overlap with neighbors
            prev_end = words[i-1]["end"] if i > 0 else 0
            next_start = words[i+1]["start"] if i < len(words)-1 else len(data)/sr
            
            # Add padding, but not into neighbor territory
            pad_start = max(prev_end, w["start"] - 0.02)  # max 20ms before
            pad_end = min(next_start, w["end"] + 0.02)    # max 20ms after
            
            start_sample = max(0, int(pad_start * sr))
            end_sample = min(len(data), int(pad_end * sr))
            segment = data[start_sample:end_sample]

            if len(segment) < 100:
                results.append({
                    "word_score": 0, "color": "red",
                    "expected_phonemes": [], "actual_phonemes": [],
                    "phoneme_scores": [], "issues": ["too short"]
                })
                continue

            score = self.score_word(segment, sr, w["word"])
            results.append(score)

        return results


# Singleton
_scorer = None

def get_scorer() -> PhonemeScorer:
    global _scorer
    if _scorer is None:
        _scorer = PhonemeScorer()
    return _scorer


if __name__ == "__main__":
    import sys
    scorer = get_scorer()

    # Test with g2p
    test_words = ["don't", "tell", "what", "the", "think"]
    for w in test_words:
        expected = scorer.get_expected_phonemes(w)
        print(f"{w}: {expected}")
