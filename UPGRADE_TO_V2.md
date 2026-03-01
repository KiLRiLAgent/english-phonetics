# Upgrade to v2 (Speaker Diarization + Timestamps)

## What's New in v2?

### 🎯 Core Features
1. **Speaker Diarization** — detects who speaks when (you vs others)
2. **Timestamps** — every error has a timestamp (MM:SS)
3. **New Report Format**:
   - 📊 Summary (duration, speaking time %)
   - 🔥 Top-3 critical errors (most frequent)
   - 📝 All errors timeline
   - 🎯 Recommendations

### 💡 Use Cases
- **Calls/Meetings** — analyze only YOUR speech, ignore others
- **Practice Sessions** — review errors with timestamps
- **Presentations** — track grammar mistakes by time

---

## Installation

### 1. Install Dependencies

```bash
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer
source venv/bin/activate

# Install pyannote.audio for speaker diarization
pip install pyannote.audio python-dotenv

# OR update all dependencies
pip install -r requirements.txt
```

### 2. Get Hugging Face Token (Required for Diarization)

**Why needed:** Speaker diarization uses `pyannote.audio` which requires a free Hugging Face account.

**Steps:**

1. **Create account:** https://huggingface.co/join
2. **Accept license:** https://huggingface.co/pyannote/speaker-diarization-3.1
   - Click: **"Agree and access repository"**
3. **Get token:** https://huggingface.co/settings/tokens
   - Click: **"New token"**
   - Name: `openclaw-diarization`
   - Type: **Read**
   - Copy the token (starts with `hf_...`)
4. **Save to `.env`:**

```bash
echo "HUGGINGFACE_TOKEN=hf_your_token_here" >> .env
```

**Replace `hf_your_token_here` with your actual token!**

5. **Verify:**

```bash
python -c "from pyannote.audio import Pipeline; print('✅ Token works!')"
```

---

## Testing

### Test 1: Command Line (Simple)

```bash
python analyzer_diarization.py
```

Expected output:
```
Loading Whisper model...
✅ Whisper loaded
Loading LanguageTool...
✅ LanguageTool loaded

Analyzing: test_data/kirill_normal.wav

======================================================================
🎯 ENGLISH SPEAKING PRACTICE ANALYSIS
======================================================================

📊 SUMMARY
----------------------------------------------------------------------
Overall Score:      78/100
Duration:           00:05
Your speaking time: 00:05 (100%)
Errors found:       2 grammar, 0 pronunciation

🔥 TOP 3 CRITICAL ERRORS
----------------------------------------------------------------------

1. Subject-verb agreement (occurred 1 time(s))
❌ 00:03 "you goes"
✅ Should be: "you go"
📚 "you" is plural, use base form verb
   Example: ✅ "you go" | ❌ "you goes"
   📕 Cambridge Grammar Unit 5-6

...
```

### Test 2: Web Server

```bash
cd web
python server.py
```

Open: http://localhost:8780

Upload audio → see results with timestamps!

### Test 3: macOS App v2

```bash
cd macos_app
python english_practice_app_v2.py
```

**Features:**
- 🔴 Click "Start Recording" → speak → click "Stop Recording"
- 🔥 See Top-3 errors in notification
- 📊 Full report saved to `~/.english_practice/recordings/`
- 🎯 Toggle "Speaker Diarization" on/off

---

## Multi-Speaker Test

Create a test audio with 2 speakers (you + someone else):

```bash
# Record a call or meeting
# App will ask: "Which speaker is YOU?"
# Enter: 0, 1, or 2 (depending on detection)
```

App analyzes **ONLY your speech**, ignoring others.

---

## Report Format Example

```
======================================================================
🎯 ENGLISH SPEAKING PRACTICE ANALYSIS
======================================================================

📊 SUMMARY
----------------------------------------------------------------------
Overall Score:      78/100
Duration:           15:23
Your speaking time: 08:45 (57%)
Errors found:       12 grammar, 5 pronunciation

🔥 TOP 3 CRITICAL ERRORS
----------------------------------------------------------------------

1. Subject-verb agreement (occurred 4 times)
❌ 03:42 "So we goes to the meeting tomorrow"
✅ Should be: "So we go to the meeting tomorrow"
📚 Cambridge Grammar Unit 5-6: Present Simple with "we/they"

2. Past participle (occurred 3 times)
❌ 07:15 "I have went there before"
✅ Should be: "I have gone there before"
📚 Cambridge Grammar Unit 14: Present Perfect

3. Article usage (occurred 2 times)
❌ 11:30 "We need a information about this"
✅ Should be: "We need information about this"
📚 Cambridge Grammar Unit 68: Uncountable nouns

📝 ALL ERRORS (TIMELINE)
----------------------------------------------------------------------
03:42 | Grammar | "we goes" → "we go"
05:18 | Pronunciation | "project" (WER: 15%)
07:15 | Grammar | "have went" → "have gone"
09:03 | Grammar | "She don't" → "She doesn't"
11:30 | Grammar | "a information" → "information"
...

🎯 RECOMMENDATIONS
----------------------------------------------------------------------
- Review subject-verb agreement (4 errors)
- Practice Present Perfect (3 errors)
- Work on article usage with uncountable nouns
```

---

## Troubleshooting

### "HUGGINGFACE_TOKEN not found"

**Solution:** Follow step 2 above — add token to `.env`

### "Speaker diarization failed"

**Solution:** Diarization is optional. App will continue without it (single-speaker mode).

### "pyaudio not found"

**Solution for macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Alternative (no compilation):**
```bash
pip install sounddevice soundfile
```
Then replace `pyaudio` with `sounddevice` in app code.

---

## Build DMG (macOS App)

```bash
cd macos_app
source ../venv/bin/activate

# Update setup.py to use v2
# (Replace english_practice_app.py with english_practice_app_v2.py)

./build_dmg.sh
```

Output: `English_Practice_2.0.dmg`

---

## What's Next?

- [ ] Auto-detect call start (FaceTime/Zoom)
- [ ] Hotkey support (Cmd+Shift+R)
- [ ] Export to PDF
- [ ] Progress tracking
- [ ] Web dashboard

---

**Questions?** Check:
- `GET_HUGGINGFACE_TOKEN.md` — Token setup
- `README_MVP.md` — Product vision
- `TESTING_GUIDE.md` — Full testing guide
