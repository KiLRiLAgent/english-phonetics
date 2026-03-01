# Building macOS App (.dmg)

## Quick Start

### 1. Test the app (development)
```bash
cd /Users/kilril/dev/4_openclaw/english_phonetics_analyzer/macos_app
source ../venv/bin/activate
python english_practice_app.py
```

You should see 🎤 icon in menu bar!

### 2. Build .app bundle
```bash
python setup.py py2app
```

Output: `dist/English Practice.app`

### 3. Test the .app
```bash
open "dist/English Practice.app"
```

### 4. Create .dmg installer
```bash
# Install create-dmg
brew install create-dmg

# Build DMG
create-dmg \
  --volname "English Practice" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "English Practice.app" 175 120 \
  --hide-extension "English Practice.app" \
  --app-drop-link 425 120 \
  "English_Practice_1.0.dmg" \
  "dist/"
```

Output: `English_Practice_1.0.dmg`

### 5. Distribute
Double-click `.dmg` to open, drag app to Applications folder!

---

## Features

✅ **Menu Bar App** — lives in menu bar, doesn't clutter Dock  
✅ **One-click Recording** — click "Start Recording" in menu  
✅ **Auto-Analysis** — analyzes speech when you stop  
✅ **Notifications** — shows results as notification  
✅ **Detailed Reports** — click for full grammar breakdown  
✅ **Cambridge Grammar** — every error includes textbook reference  
✅ **Saved Reports** — text files saved to `~/.english_practice/recordings/`  

---

## Usage

1. **Start app** — 🎤 appears in menu bar
2. **Click icon** → "Start Recording"
3. **Speak in English** (practice your presentation, call, etc.)
4. **Click icon** → "Stop Recording"
5. **Wait** — analysis takes ~10-20 seconds
6. **See notification** — overall score
7. **Click "Last Analysis"** — detailed grammar feedback

---

## Hotkey (Coming Soon)

- **Cmd+Shift+R** — start/stop recording (global hotkey)

---

## Folder Structure

```
~/.english_practice/recordings/
├── recording_20260215_143052.wav
├── recording_20260215_143052.txt  ← Detailed report
├── recording_20260215_151234.wav
└── recording_20260215_151234.txt
```

---

## Requirements

- macOS 11+ (Big Sur or later)
- Microphone access permission
- ~2 GB disk space (for models)

---

## Troubleshooting

### "App can't be opened"
```bash
xattr -cr "English Practice.app"
```

### Microphone permission denied
System Preferences → Security & Privacy → Microphone → Enable for "English Practice"

### Analysis is slow
First run downloads Whisper model (~500 MB), be patient!

---

## TODO for v2.0

- [ ] Global hotkey (Cmd+Shift+R)
- [ ] Real-time analysis during call
- [ ] FaceTime/Zoom auto-detection
- [ ] Progress bar during analysis
- [ ] Export to PDF
- [ ] Dark mode icon
- [ ] Auto-update

---

Built with ❤️ for English learners
