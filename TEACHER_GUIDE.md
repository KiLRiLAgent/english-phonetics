# 📚 Teacher's Guide: Call Recording Mode

Quick reference for English teachers using the Call Recording feature.

## Quick Start

### 1. One-Time Setup (15 minutes)

1. **Install BlackHole** (virtual audio device)
   ```bash
   brew install blackhole-2ch
   ```

2. **Create Aggregate Device** (combines mic + system audio)
   - Open **Audio MIDI Setup**
   - Click **"+"** → **"Create Aggregate Device"**
   - Check: ✅ Your Microphone, ✅ BlackHole 2ch
   - Name it: **"Call Recording Device"**

3. **Configure Zoom/Discord/Skype**
   - **Microphone:** Select "Call Recording Device"
   - **Speakers:** Select your normal speakers (or create Multi-Output Device)

4. **Select Device in App**
   - Open **English Practice** menu bar app
   - Click **"🎙️ Select Audio Device"**
   - Choose your Aggregate Device

📖 **Full setup guide:** See `CALL_RECORDING_SETUP.md`

---

## Daily Usage

### Recording a Lesson

1. **Before lesson starts:**
   - Make sure Zoom/Discord is using "Call Recording Device"
   - Open **English Practice** menu bar app

2. **Start recording:**
   - Click **📞 "Start Call Recording"**
   - You'll see: `🔴 Recording 00:00`

3. **During lesson:**
   - Teach as normal
   - Timer updates: `🔴 Recording 15:32`

4. **Stop recording:**
   - Click menu bar icon
   - Click **⏹️ "Stop Call"**
   - Wait for analysis (30-60 seconds)

5. **View results:**
   - Notification shows summary for both speakers
   - Click **📊 "View Reports"** to open folder
   - Open `.txt` file for full report

---

## Understanding Results

### Notification Format

```
🎓 Урок завершён

Ученик (Speaker 1): 3 ошибки (Grammar: 85/100)
Преподаватель (Speaker 0): 1 ошибка (Grammar: 95/100)

→ Смотреть отчёт
```

- **Speaker 0** = Usually the first person to speak (often teacher)
- **Speaker 1** = Second speaker (often student)
- Grammar score: 100 = perfect, 85 = good, <70 = needs work

### Report File Contents

Each recording generates two files:

1. **`call_YYYYMMDD_HHMMSS.wav`** — Audio recording
2. **`call_YYYYMMDD_HHMMSS.txt`** — Analysis report

Report sections:

- **Summary** — Overall duration, speaking time for each speaker
- **Multi-Speaker Analysis** — Breakdown per speaker
- **Top Errors** — Most common mistakes (with timestamps)
- **Timeline** — All errors in order

---

## Tips for Teachers

### Best Practices

✅ **Start recording BEFORE student joins** — Ensures you're captured as Speaker 0  
✅ **Use headphones** — Prevents echo and feedback  
✅ **Test before first lesson** — Record a 30-second test call  
✅ **Check audio levels** — Make sure both you and student are clearly audible  
✅ **Keep recordings organized** — Review and delete old recordings weekly  

### Common Scenarios

**Scenario: One-on-one lesson**
- Perfect! You'll get separate analysis for teacher and student

**Scenario: Group lesson (3+ students)**
- Works, but speaker 1, 2, 3 may be mixed
- Better to use separate breakout rooms for individual practice

**Scenario: Student has poor audio quality**
- Transcription may be inaccurate
- Ask student to use headset microphone
- Check student's speaking time % — should be >30% for practice lessons

---

## Privacy & Data

### What's recorded?

- ✅ Audio from both sides (teacher + student)
- ✅ Transcripts (what was said)
- ✅ Grammar analysis (errors found)

### What's NOT recorded?

- ❌ Video
- ❌ Screen sharing content
- ❌ Chat messages
- ❌ Personal data beyond the conversation

### Data Storage

- **Local only** — All recordings stay on your Mac
- **Location:** `~/.english_practice/call_recordings/`
- **Not uploaded** — No cloud storage (unless you manually copy files)

### Student Consent

⚠️ **Important:** Always inform students before recording!

**Suggested script:**
> "I'm going to record our lesson today for quality purposes. The recording will be analyzed automatically to help track your progress. Is that okay with you?"

### GDPR Compliance

If you're in EU:

- ✅ Get explicit consent before recording
- ✅ Inform students how data is used (analysis only)
- ✅ Allow students to request deletion
- ✅ Don't share recordings without permission

**Delete old recordings:**
```bash
# Delete recordings older than 30 days
find ~/.english_practice/call_recordings/ -name "*.wav" -mtime +30 -delete
```

---

## Troubleshooting

### Problem: Can't hear student during call

**Solution:**
- Make sure Zoom/Discord **Speakers** is set to your normal speakers
- Or create a Multi-Output Device (see `CALL_RECORDING_SETUP.md`)

### Problem: Recording only captures my voice

**Solution:**
- Check that call app **Speakers** is routing through BlackHole
- Create Multi-Output Device: Speakers + BlackHole
- Set call app to use Multi-Output Device for speakers

### Problem: Analysis shows only one speaker

**Solution:**
1. Check if student actually spoke during recording
2. Verify backend has Hugging Face token (diarization requires this)
3. Try again — sometimes students need to speak longer for detection

### Problem: Poor transcription quality

**Solution:**
- Check audio quality — both sides should be clear
- Reduce background noise
- Ask student to speak slower and more clearly
- Use better quality microphone

### Problem: App says "Backend Not Running"

**Solution:**
```bash
# Start backend server
cd ~/dev/4_openclaw/english_phonetics_analyzer/backend
python server.py
```

---

## Advanced Features

### Analyzing Specific Speaker Only

1. Click **"🎤 Quick Practice"** instead of "Call Recording"
2. When prompted, select which speaker to analyze (0, 1, 2, etc.)
3. Only that speaker's errors will be shown

### Reviewing Past Lessons

1. Click **📊 "View Reports"**
2. Open `.txt` file to see full analysis
3. Compare student progress over time (grammar scores)

### Exporting Reports

Reports are plain text files — you can:

- Email to students
- Copy to shared folders
- Import into Excel for tracking scores
- Archive for progress reviews

---

## FAQ

**Q: Can I record in-person lessons?**  
A: Yes! Use the same Aggregate Device setup, but route your computer audio to speakers in the room.

**Q: Does this work with Google Meet?**  
A: Yes! Select the Aggregate Device in your browser's audio settings when joining.

**Q: Can I use this for self-practice?**  
A: Yes! Use **"🎤 Quick Practice"** mode instead — simpler setup, no aggregate device needed.

**Q: How long does analysis take?**  
A: Usually 30-60 seconds for a 30-minute lesson.

**Q: What if I forget to stop recording?**  
A: Just click "Stop Call" when you remember. The analysis will still work.

**Q: Can I record phone calls?**  
A: Not directly. But you can route phone audio through your Mac (requires additional software like Loopback).

---

## Support

**Setup Issues:** See `CALL_RECORDING_SETUP.md`  
**Technical Issues:** Check backend logs or restart the app  
**Questions:** Open a GitHub issue or contact support  

---

**Happy teaching! 🎓**
