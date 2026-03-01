# Aeneas-based Pronunciation Assessment

## What is Aeneas?

Aeneas is a forced alignment tool that aligns audio with text.

**Key difference from MFA:**
- **MFA:** Phoneme-level alignment (very detailed)
- **Aeneas:** Word-level alignment (simpler, faster)

## How it works:

1. **Input:**
   - Audio file (.wav)
   - Reference text (what should be spoken)

2. **Output:**
   - Word-level timestamps: `{"word": "hello", "start": 0.5, "end": 0.9}`

3. **Scoring:**
   - If Aeneas can align a word → it was pronounced correctly (green)
   - If Aeneas skips/misaligns → pronunciation error (red/yellow)

## Limitations:

❌ **Not phoneme-level** — can't tell you "/θ/ → /t/" substitution  
✅ **Word-level** — can tell "you said 'da' instead of 'the'"  
✅ **Reliable** — based on proven DTW (Dynamic Time Warping) algorithm  

## Use cases:

Perfect for:
- ✅ Checking if student read the correct text
- ✅ Detecting skipped/wrong words
- ✅ Measuring reading fluency (words per minute)

Not good for:
- ❌ Fine-grained phoneme analysis ("you said /t/ instead of /θ/")
- ❌ Accent detection
- ❌ Subtle pronunciation errors

## Integration plan:

### MVP (Phase 1): Word-level only

```python
# Teacher provides reference text
reference = "The quick brown fox jumps"

# Student records audio
audio = "student_recording.wav"

# Aeneas aligns
alignment = aeneas.align(audio, reference)
# → [
#     {"word": "the", "start": 0.0, "end": 0.3, "aligned": True},
#     {"word": "quick", "start": 0.3, "end": 0.6, "aligned": True},
#     {"word": "brown", "start": 0.6, "end": 0.9, "aligned": False},  # Student mispronounced
#     ...
# ]

# Score: aligned words = green, not aligned = red
```

### Future (Phase 2): Add phoneme-level

If Aeneas works well, we can later add:
- Extract aligned word audio segments
- Use phoneme recognizer ONLY on correctly-aligned words
- This reduces false positives (don't analyze garbage audio)

## Installation:

```bash
pip install numpy  # Required first
pip install aeneas
```

## Next steps:

1. ✅ Install Aeneas
2. ⏳ Test alignment quality
3. ⏳ Integrate into web server
4. ⏳ Evaluate: Is word-level enough, or do we need phoneme-level?

---

**Reality check:**

True phoneme-level assessment requires:
- Expensive: Azure/Google APIs ($$$)
- Complex: MFA/Gentle (Kaldi compilation nightmares)
- Unreliable: Wav2Vec2 (we tried, didn't work)

**Aeneas is a pragmatic middle ground.**
