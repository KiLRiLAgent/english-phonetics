# ✅ Testing Checklist: Call Recording Feature

## Pre-Testing Setup

- [ ] Backend server running: `cd backend && python server.py`
- [ ] Check Hugging Face token in `.env` (for diarization)
- [ ] Verify BlackHole is installed: `brew list blackhole-2ch`

---

## 1. Menu Bar App - UI Tests

### Basic UI Elements

- [ ] App launches without errors
- [ ] Menu bar shows: `🎤 English Practice`
- [ ] Menu contains:
  - [ ] 🎤 Quick Practice
  - [ ] 📞 Start Call Recording
  - [ ] 📊 View Reports
  - [ ] 🎙️ Select Audio Device
  - [ ] Speaker Diarization toggle
  - [ ] Settings, About, Quit

### Audio Device Selection

- [ ] Click "🎙️ Select Audio Device"
- [ ] Dialog shows list of available input devices
- [ ] Can select a device by number
- [ ] Notification confirms selection
- [ ] Selected device persists in `self.selected_device_index`

### Aggregate Device Detection

- [ ] On first launch (no aggregate device):
  - [ ] Warning appears after 2 seconds
  - [ ] Warning offers to show setup instructions
  - [ ] Clicking "Show Instructions" opens `CALL_RECORDING_SETUP.md`

- [ ] On launch (with aggregate device):
  - [ ] No warning shown
  - [ ] Device auto-selected
  - [ ] Console shows: `✅ Found aggregate device: ...`

---

## 2. Quick Practice Mode (Existing Functionality)

- [ ] Click "🎤 Quick Practice"
- [ ] Menu bar shows: `🔴 Recording...`
- [ ] Button changes to: `⏹ Stop Practice`
- [ ] Notification: "Quick Practice started"
- [ ] Record for 10 seconds
- [ ] Click "⏹ Stop Practice"
- [ ] Analysis runs (30-60 sec)
- [ ] Notification shows results
- [ ] File saved in `~/.english_practice/recordings/`
- [ ] Report saved as `.txt` file
- [ ] "Last Analysis" shows results

**Expected behavior:** Same as before (no regressions)

---

## 3. Call Recording Mode (New Feature)

### Start Recording

- [ ] Click "📞 Start Call Recording"
- [ ] If no device selected:
  - [ ] Alert appears: "Select Audio Device"
  - [ ] Option to select device
- [ ] With device selected:
  - [ ] Menu bar shows: `🔴 Recording 00:00`
  - [ ] Button changes to: `⏹️ Stop Call`
  - [ ] Notification: "Call Recording started"

### During Recording

- [ ] Timer updates every second:
  - [ ] `🔴 Recording 00:01`
  - [ ] `🔴 Recording 00:15`
  - [ ] `🔴 Recording 01:30`
- [ ] Other menu items still accessible
- [ ] Can click "Stop Call" at any time

### Stop Recording

- [ ] Click "⏹️ Stop Call"
- [ ] Menu bar returns to: `🎤 English Practice`
- [ ] Button returns to: `📞 Start Call Recording`
- [ ] Notification: "Call recording stopped"
- [ ] Analysis starts (may take 60-120 sec for diarization)

### Results (Single Speaker)

If recording only has one speaker:

- [ ] Notification shows:
  ```
  Анализ завершён
  Оценка: X/100
  Ошибки: Y
  ```
- [ ] File saved in `~/.english_practice/call_recordings/`
- [ ] Filename: `call_YYYYMMDD_HHMMSS.wav`
- [ ] Report: `call_YYYYMMDD_HHMMSS.txt`
- [ ] Report contains normal analysis (single speaker)

### Results (Multi-Speaker)

If recording has 2+ speakers:

- [ ] Notification shows:
  ```
  🎓 Урок завершён
  
  Ученик (Speaker 1): X ошибки (Grammar: Y/100)
  Преподаватель (Speaker 0): Z ошибка (Grammar: W/100)
  ```
- [ ] Report contains **MULTI-SPEAKER ANALYSIS** section
- [ ] Each speaker has separate:
  - [ ] Overall score
  - [ ] Speaking time
  - [ ] Grammar errors
  - [ ] Top errors list
- [ ] Report shows who is Speaker 0 vs Speaker 1

### View Reports

- [ ] Click "📊 View Reports"
- [ ] Finder opens `~/.english_practice/call_recordings/`
- [ ] Folder contains `.wav` and `.txt` files

---

## 4. Backend Tests

### Single Speaker Analysis

```bash
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer
./venv/bin/python test_call_recording.py test_data/kirill_normal.wav
```

**Expected output:**
- [ ] Transcription runs successfully
- [ ] Overall score calculated
- [ ] `speaker_breakdown` is `None` or has only one speaker
- [ ] JSON file created with results

### Multi-Speaker Analysis (Manual Test)

**Setup:**
1. Record a test conversation with two people
2. Save as `test_multi_speaker.wav`
3. Run:
   ```bash
   ./venv/bin/python test_call_recording.py test_multi_speaker.wav
   ```

**Expected output:**
- [ ] `Total speakers: 2` (or more)
- [ ] `SPEAKER BREAKDOWN` section shows:
  - [ ] `SPEAKER_0` with score, errors, speaking time
  - [ ] `SPEAKER_1` with score, errors, speaking time
- [ ] Each speaker has transcript snippet
- [ ] Top errors per speaker
- [ ] JSON file contains `speaker_breakdown` dict

---

## 5. Integration Test (End-to-End)

### Test Scenario: Teacher Recording a Lesson

**Setup:**
1. Create Aggregate Device (see `CALL_RECORDING_SETUP.md`)
2. Start Zoom/Discord test call (or use system audio)
3. Configure call app to use Aggregate Device

**Flow:**
1. [ ] Open English Practice app
2. [ ] Click "🎙️ Select Audio Device" → select Aggregate Device
3. [ ] Join test call / play audio
4. [ ] Click "📞 Start Call Recording"
5. [ ] Timer shows: `🔴 Recording 00:00`
6. [ ] Speak as "teacher" for 10 seconds
7. [ ] Have "student" speak for 10 seconds (or play audio)
8. [ ] Timer updates to: `🔴 Recording 00:20`
9. [ ] Click "⏹️ Stop Call"
10. [ ] Wait for analysis (60-120 sec)
11. [ ] Notification shows both speakers' scores
12. [ ] Click "📊 View Reports"
13. [ ] Open latest `.txt` file
14. [ ] Verify multi-speaker breakdown

**Success criteria:**
- [ ] Both speakers detected
- [ ] Separate analysis for each
- [ ] Notification in Russian
- [ ] Report readable and complete

---

## 6. Error Handling Tests

### No Backend Server

- [ ] Stop backend server
- [ ] Try to record and analyze
- [ ] Alert appears: "Backend Server Not Running"
- [ ] Instructions shown for starting backend

### No Aggregate Device (Call Recording)

- [ ] Remove/rename aggregate device
- [ ] Restart app
- [ ] Warning appears about missing device
- [ ] Can still use Quick Practice mode

### Invalid Audio Device Selection

- [ ] Click "Select Audio Device"
- [ ] Enter invalid device number
- [ ] Alert: "Device X not found!"

### Recording Interruption

- [ ] Start call recording
- [ ] Quit app before stopping
- [ ] Restart app
- [ ] No crash, can record again

---

## 7. Documentation Tests

### Setup Guide

- [ ] Open `CALL_RECORDING_SETUP.md`
- [ ] Follow instructions step-by-step
- [ ] Verify:
  - [ ] BlackHole installation works
  - [ ] Aggregate Device creation works
  - [ ] Zoom/Discord configuration works
  - [ ] Test recording captures both sides

### Teacher Guide

- [ ] Open `TEACHER_GUIDE.md`
- [ ] Verify all sections are clear:
  - [ ] Quick Start is accurate
  - [ ] Daily Usage instructions work
  - [ ] Understanding Results matches actual output
  - [ ] Troubleshooting addresses common issues

---

## 8. Performance Tests

### Recording Duration

- [ ] Record 1 minute → Works
- [ ] Record 5 minutes → Works
- [ ] Record 30 minutes → Works
- [ ] Memory usage reasonable (<500MB)

### Analysis Speed

- [ ] 1 minute audio: ~30 sec analysis
- [ ] 5 minute audio: ~60 sec analysis
- [ ] 30 minute audio: ~3-5 min analysis

### File Sizes

- [ ] 1 min stereo WAV: ~3-5MB
- [ ] 30 min stereo WAV: ~100MB
- [ ] Disk space warning if needed

---

## 9. Compatibility Tests

### macOS Versions

- [ ] macOS 12 (Monterey)
- [ ] macOS 13 (Ventura)
- [ ] macOS 14 (Sonoma)
- [ ] macOS 15 (Sequoia)

### Call Apps

- [ ] Zoom
- [ ] Discord
- [ ] Skype
- [ ] Google Meet (browser)

---

## 10. Privacy & Security

### Data Storage

- [ ] Recordings saved locally (not uploaded)
- [ ] Files in hidden folder (`~/.english_practice/`)
- [ ] Can delete old recordings manually
- [ ] No cloud sync without user action

### Permissions

- [ ] Microphone permission requested
- [ ] No network requests except to localhost:8780
- [ ] Backend doesn't save recordings permanently

---

## ✅ Sign-Off

**Tester:** _________________  
**Date:** _________________  
**macOS Version:** _________________  
**App Version:** 2.1  

**Overall Result:**
- [ ] ✅ All tests passed
- [ ] ⚠️ Minor issues (list below)
- [ ] ❌ Major issues found (list below)

**Issues Found:**

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

**Notes:**

_______________________________________________
_______________________________________________
_______________________________________________

---

## Quick Test (5 Minutes)

Minimal test for smoke testing:

1. [ ] Launch app → No crashes
2. [ ] Click "🎤 Quick Practice" → Record 5 sec → Stop → Results show
3. [ ] Click "📞 Start Call Recording" → Timer appears → Stop → Results show
4. [ ] Click "📊 View Reports" → Folder opens
5. [ ] Click "Settings" → Shows status

**If all pass:** ✅ Basic functionality works!
