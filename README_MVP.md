# English Speaking Practice Tool — MVP

**Product Positioning:** Grammar + Fluency + Basic Pronunciation Analysis

## 🎯 Key Features

### 1. **Grammar Analysis** ⭐ Main Focus
- ✅ Real-time grammar checking (LanguageTool)
- ✅ Error categorization (Grammar, Style, Spelling)
- ✅ Suggestions & corrections
- ✅ Severity levels (Error/Warning)
- ✅ Speech-optimized (filters punctuation/typography errors)

### 2. **Fluency Metrics**
- ✅ WPM (Words Per Minute) calculation
- ✅ Pause detection & analysis
- ✅ Speech duration tracking
- ✅ Optimal speed feedback (120-150 WPM recommended)

### 3. **Pronunciation (Basic)**
- ✅ Word Error Rate (WER) calculation
- ✅ Mispronounced words highlighting
- ✅ Whisper-based speech recognition
- ⚠️ **NOT phoneme-level scoring** (honest limitation)

## 🏗️ Architecture

```
Audio Input
    ↓
Whisper (Speech-to-Text)
    ↓
┌──────────────┬──────────────┬──────────────┐
│   Grammar    │   Fluency    │Pronunciation │
│(LanguageTool)│  (WPM, etc)  │     (WER)    │
└──────────────┴──────────────┴──────────────┘
    ↓
Overall Score (0-100)
    - Grammar: 40%
    - Pronunciation: 35%
    - Fluency: 25%
```

## 📊 Scoring System

### Overall Score Formula
```python
Overall = (
    Grammar_Score × 0.40 +
    Pronunciation_Score × 0.35 +
    Fluency_Score × 0.25
)
```

### Grammar Score
- 100 points baseline
- -10 points per grammar error
- -5 points per style warning

### Pronunciation Score
- Based on Word Error Rate (WER)
- Score = 100 - (WER × 100)
- Example: WER 5% → Score 95

### Fluency Score
- Optimal: 120-150 WPM → 100 points
- Good: 100-120 or 150-180 WPM → 80 points
- Acceptable: 80-100 or 180-200 WPM → 60 points
- Slow/Fast: <80 or >200 WPM → 40 points

## 🚀 Quick Start

### Installation
```bash
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start web server
python web/server.py
```

### Web UI
Open: http://localhost:8780/

### Command Line
```python
from analyzer_mvp import EnglishPracticeAnalyzer

analyzer = EnglishPracticeAnalyzer()
result = analyzer.analyze(
    audio_path="my_audio.wav",
    reference_text="The quick brown fox jumps over the lazy dog"
)

print(f"Overall Score: {result['overall_score']}/100")
print(f"Grammar Errors: {result['grammar']['total_errors']}")
print(f"WPM: {result['fluency']['wpm']}")
```

## 📝 Example Output

```json
{
  "overall_score": 90,
  "transcript": "Don't you tell me what to do?",
  "grammar": {
    "score": 100,
    "total_errors": 0,
    "errors": []
  },
  "fluency": {
    "wpm": 105,
    "duration": 4.0,
    "pause_count": 0
  },
  "pronunciation": {
    "word_accuracy": 85.7,
    "wer": 0.143,
    "mispronounced_words": ["do"]
  }
}
```

## ✅ What We Promise

✅ **Grammar correctness** — production-quality LanguageTool  
✅ **Fluency analysis** — WPM, pauses, duration  
✅ **Word-level accuracy** — which words were mispronounced  
✅ **Honest limitations** — no false phoneme-level claims

## ❌ What We DON'T Promise

❌ Phoneme-level pronunciation scoring  
❌ Accent detection  
❌ Prosody/intonation analysis  
❌ Native-level pronunciation comparison

## 🎯 Target Users

- **English learners** practicing speaking
- **Grammar-focused students** (writing → speaking)
- **Business English** professionals
- **Teachers** checking student recordings

## 💰 Business Model

### Freemium
- **Free:** 10 analyses/day
- **Pro ($9.99/mo):** Unlimited analyses + detailed reports
- **Enterprise:** Custom pricing for schools/companies

### Alternative: Pay-per-use
- $0.10 per analysis
- Bulk packages: 100 for $5, 1000 for $40

## 🔮 Future Improvements (NOT MVP)

1. **Better Pronunciation** (if needed):
   - Azure Pronunciation Assessment API ($1/1000)
   - Or: invest time in Kaldi + GOPT

2. **Advanced Grammar**:
   - Context-aware suggestions
   - Learning path recommendations
   - Common mistake patterns

3. **Fluency Enhancements**:
   - Hesitation detection ("um", "uh")
   - Filler word analysis
   - Natural rhythm scoring

## 📚 Tech Stack

- **Speech Recognition:** OpenAI Whisper (open-source)
- **Grammar:** LanguageTool (open-source)
- **Web:** Python HTTP server
- **Frontend:** Vanilla JS + HTML/CSS
- **Cost:** $0 (100% free & open-source)

## 🏆 Competitive Advantage

vs **Speechace/EF/Duolingo:**
- ✅ **Honest** — we don't promise what we can't deliver
- ✅ **Grammar-first** — unique positioning
- ✅ **Transparent** — users know what they're getting
- ✅ **Free/cheap** — no $40/month subscriptions

vs **Simple speech-to-text tools:**
- ✅ Grammar checking (they don't have)
- ✅ Fluency metrics (they don't have)
- ✅ Scoring system (they don't have)

## 📊 Success Metrics

- User satisfaction > 4.5/5
- Grammar error detection accuracy > 90%
- WER < 10% on clear audio
- Fluency metrics match human judgment

---

**Built with honesty. No bullshit. Just helpful.** 🎯
