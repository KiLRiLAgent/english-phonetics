# English Speaking Practice — macOS App

## 🎯 What is this?

**Menu bar app** for practicing English speaking during calls/presentations.

**Features:**
- ✅ Lives in menu bar (doesn't clutter Dock)
- ✅ One-click recording
- ✅ Grammar analysis with Cambridge Grammar references
- ✅ Fluency metrics (WPM, pauses)
- ✅ Pronunciation feedback (word-level)
- ✅ Saves detailed reports

---

## 🚀 Quick Start

### For Users (Download DMG)

1. **Download** `English_Practice_1.0.dmg`
2. **Open** the DMG
3. **Drag** app to Applications folder
4. **Launch** from Applications
5. **Allow** microphone permission when prompted
6. **Click** 🎤 icon in menu bar → "Start Recording"

### For Developers (Build from Source)

```bash
cd macos_app
source ../venv/bin/activate

# Test in development mode
python english_practice_app.py

# Build .app + .dmg
./build_dmg.sh
```

---

## 📱 How to Use

### During a Call/Presentation:

1. **Before starting:** Click 🎤 → "Start Recording"
2. **Speak normally** during your call/presentation
3. **After finishing:** Click 🎤 → "Stop Recording"
4. **Wait ~20 seconds** — analyzing...
5. **Get notification** with your score!
6. **Click "Last Analysis"** for detailed grammar feedback

### Example Workflow:

```
1. You: [Click 🎤 → Start Recording]
2. You: [Present in English for 5 minutes]
3. You: [Click 🎤 → Stop Recording]
4. App: "Analyzing your speech..."
5. App: 🎉 Score: 88/100
        Grammar: 90/100 (2 errors)
        Fluency: 135 WPM
6. You: [Click "Last Analysis" for details]
7. App: Shows grammar errors with Cambridge explanations
```

---

## 📊 What You Get

### Notification (Quick Summary)
```
✅ Score: 88/100
Grammar: 90/100 (2 errors)
Fluency: 135 WPM
```

### Detailed Report (Click "Last Analysis")
```
You said: "I goes to the store yesterday..."

Overall Score: 88/100

❌ Grammar Error #1: The pronoun 'I' must be used with...
   Incorrect: 'goes'
   ✏️  Correct: go
   
   📖 Cambridge Grammar:
   └─ Subject-Verb Agreement: I/You/We/They + base form
      💡 Use the base form of the verb (without -s)
      📕 English Grammar in Use (Intermediate)
      📚 Unit 5-6 (Present Simple)
      🎯 Level: Elementary

FLUENCY:
  WPM: 135 (good!)
  Duration: 5.2s
  Pauses: 2
```

### Saved Text Report
Location: `~/.english_practice/recordings/recording_20260215_143052.txt`

Full analysis + Cambridge references for later review!

---

## ⚙️ Settings

### Recordings Folder
`~/.english_practice/recordings/`

Contains:
- `.wav` files (your recordings)
- `.txt` files (detailed reports)

### Microphone Permission
System Preferences → Security & Privacy → Microphone → Enable "English Practice"

---

## 🎯 Use Cases

1. **Practice before important presentation**
   - Record yourself presenting
   - Get grammar + fluency feedback
   - Fix errors before the real thing

2. **During work calls** (post-analysis)
   - Record your English calls
   - Review what you said after
   - Track improvement over time

3. **Daily practice**
   - Speak 1-2 minutes in English daily
   - Track your progress
   - Build confidence

---

## 🔮 Roadmap (Future Versions)

### v1.1
- [ ] Global hotkey (Cmd+Shift+R)
- [ ] Progress indicator during analysis
- [ ] Dark mode icon

### v2.0
- [ ] Real-time analysis (during call)
- [ ] Auto-detect Zoom/FaceTime calls
- [ ] Export to PDF
- [ ] Progress tracking over time

### v3.0
- [ ] Voice feedback (TTS)
- [ ] Practice exercises
- [ ] Integration with Cambridge textbook exercises

---

## 💡 Tips

1. **Speak clearly** — better recognition
2. **2-5 minute recordings** — optimal length
3. **Review Cambridge units** — learn the rules
4. **Track progress** — record daily

---

## 🐛 Troubleshooting

### App doesn't open
```bash
# Remove quarantine flag
xattr -cr "/Applications/English Practice.app"
```

### No microphone access
System Preferences → Security & Privacy → Microphone → Enable

### Analysis is slow
First run downloads Whisper model (~500 MB). Subsequent runs are faster!

### Can't find menu bar icon
Look for 🎤 in top-right corner of screen (near clock).

---

## 📚 Learn More

- **Cambridge Grammar in Use** — Blue book (Intermediate)
- **Essential Grammar in Use** — Red book (Elementary)
- Web UI version: http://localhost:8780/ (if web server running)

---

**Built with ❤️ for English learners**
