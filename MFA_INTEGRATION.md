# MFA Integration Plan

## What is Montreal Forced Aligner?

MFA is a phoneme-level forced alignment tool used for:
- Speech recognition research
- Pronunciation assessment
- Creating training data for TTS/ASR

## How it works:

1. **Input:**
   - Audio file (.wav)
   - Reference transcript (text)
   
2. **Process:**
   - Uses acoustic model to recognize phonemes
   - Uses G2P (grapheme-to-phoneme) to get expected phonemes
   - Aligns actual audio with expected phonemes using Hidden Markov Models
   
3. **Output:**
   - TextGrid file (Praat format) with phoneme boundaries
   - Each phoneme has start/end timestamp
   - Can extract phoneme durations, quality scores

## Installation:

```bash
pip install montreal-forced-aligner
```

## Required models:

1. **Acoustic model** (English): `english_us_arpa`
2. **G2P model** (text→phonemes): `english_us_arpa`
3. **Dictionary**: built-in

Download with:
```bash
mfa model download acoustic english_us_arpa
mfa model download g2p english_us_arpa
```

## Integration plan:

### 1. Create `phoneme_mfa.py`

```python
from montreal_forced_aligner import align

def align_pronunciation(audio_path, reference_text):
    # Align audio with text
    # Returns phoneme-level timestamps
    pass

def score_pronunciation(alignment, expected_phonemes):
    # Compare actual vs expected
    # Return per-phoneme scores
    pass
```

### 2. Update `web/server.py`

Replace Wav2Vec2 scorer with MFA scorer.

### 3. Test with sample audio

Verify alignment quality before production.

## Key differences from Wav2Vec2:

| Feature | Wav2Vec2 | MFA |
|---------|----------|-----|
| Reference text | Optional | **Required** |
| Accuracy | Low (50-70%) | High (90-95%) |
| Speed | Fast (~1s) | Slower (~3-5s) |
| Setup | Easy | Complex |
| Production-ready | No | Yes |

## Next steps:

1. ✅ Install MFA
2. ⏳ Download models
3. ⏳ Create phoneme_mfa.py
4. ⏳ Test alignment
5. ⏳ Integrate into web server
