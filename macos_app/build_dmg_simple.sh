#!/bin/bash
set -e

echo "🚀 Building English Practice macOS App (Simple Installation)..."
echo ""

# Clean previous builds
echo "1️⃣  Cleaning previous builds..."
rm -rf build dist dmg_contents
rm -f English_Practice_*.dmg

# Build .app with bundled backend
echo "2️⃣  Building .app bundle (with auto-start backend)..."
python3 setup_microservice.py py2app

# Check if .app exists
if [ ! -d "dist/English Practice.app" ]; then
    echo "❌ App build failed!"
    exit 1
fi

echo "✅ App built successfully!"

# Verify backend files are bundled
BACKEND_PATH="dist/English Practice.app/Contents/Resources/Backend"
if [ ! -f "$BACKEND_PATH/server.py" ]; then
    echo "⚠️  Backend not bundled, copying manually..."
    mkdir -p "$BACKEND_PATH"
    cp ../backend/server.py "$BACKEND_PATH/"
    cp ../backend/analyzer_diarization.py "$BACKEND_PATH/"
    cp ../backend/cambridge_grammar_rules.py "$BACKEND_PATH/"
    cp ../backend/requirements.txt "$BACKEND_PATH/"
fi

echo "✅ Backend bundled in .app"

# Create DMG contents folder
echo "3️⃣  Preparing DMG contents..."
mkdir -p dmg_contents

# Copy .app to DMG contents
cp -r "dist/English Practice.app" dmg_contents/

# Create simple README
cat > dmg_contents/README.txt << 'EOF'
English Speaking Practice v2.1
===============================

INSTALLATION (Super Simple!):

1. Drag "English Practice.app" to your Applications folder
2. Launch "English Practice" from Applications
3. That's it! ✅

The backend will start automatically on first launch.

---

FIRST LAUNCH:

When you first open the app:
- macOS will ask for Microphone permission → Click "OK"
- The backend server will auto-start in background
- You'll see a menu bar icon: 🎤 English Practice

---

FEATURES:

✅ Quick Practice (single speaker)
✅ Call Recording (multi-speaker for teachers)
✅ Grammar analysis (Cambridge Grammar rules)
✅ Fluency metrics (WPM, pauses, hesitations)
✅ Pronunciation scoring (WER)
✅ Speaker diarization (optional, requires HF token)
✅ Timestamps for all errors
✅ Summary + Top-3 Errors + Full Timeline

---

OPTIONAL: Speaker Diarization

For multi-speaker detection (Call Recording mode):

1. Get a free Hugging Face token:
   https://huggingface.co/settings/tokens

2. Create config file:
   mkdir -p ~/.english_practice
   echo "HUGGINGFACE_TOKEN=hf_your_token_here" > ~/.english_practice/.env

3. Restart the app

Without token: Call Recording still works, but won't separate speakers.

---

REQUIREMENTS:

- macOS 10.14 or later
- Python 3.9+ (pre-installed on modern macOS)
- Microphone access

---

TROUBLESHOOTING:

"Backend Not Running" error:
  1. Quit the app
  2. Open Terminal
  3. Run: python3 -m pip install flask requests whisper language-tool-python pyannote.audio
  4. Relaunch the app

Check backend health:
  curl http://localhost:8780/health

View logs:
  tail -f ~/.english_practice/backend.log

If problems persist:
  - Reinstall the app (drag to Trash, then reinstall)
  - Check you have Python 3.9+: python3 --version

---

USAGE:

Quick Practice (self-recording):
  1. Click menu bar icon: 🎤 English Practice
  2. Click "🎤 Quick Practice"
  3. Speak for 10-30 seconds
  4. Results appear automatically

Call Recording (for teachers):
  1. Setup: See CALL_RECORDING_SETUP.md
  2. Click "📞 Start Call Recording"
  3. Record your lesson
  4. Click "⏹️ Stop Call"
  5. Get analysis for both teacher and student

---

SUPPORT:

Logs: ~/.english_practice/backend.log
Recordings: ~/.english_practice/recordings/
Call recordings: ~/.english_practice/call_recordings/

Documentation: https://github.com/your-repo
Issues: https://github.com/your-repo/issues

---

Built with ❤️ for English learners

Version 2.1 - February 2026
EOF

# Create symlink to Applications (for drag-and-drop in DMG)
ln -s /Applications dmg_contents/Applications

# Create DMG
echo "4️⃣  Creating DMG installer..."

VERSION="2.1"
DMG_NAME="English_Practice_${VERSION}.dmg"

# Simple DMG (no create-dmg dependency)
echo "   Creating DMG with hdiutil..."
hdiutil create -volname "English Practice" -srcfolder "dmg_contents" -ov -format UDZO "$DMG_NAME"

if [ -f "$DMG_NAME" ]; then
    echo ""
    echo "🎉 SUCCESS!"
    echo "=========================================="
    echo "DMG created: $DMG_NAME"
    echo "Size: $(du -h "$DMG_NAME" | cut -f1)"
    echo ""
    echo "Installation for users:"
    echo "  1. Open $DMG_NAME"
    echo "  2. Drag English Practice.app → Applications"
    echo "  3. Launch app"
    echo "  4. Done! ✅"
    echo ""
    echo "New features (v2.1):"
    echo "  ✅ Auto-start backend (no terminal needed!)"
    echo "  ✅ Call Recording mode (for teachers)"
    echo "  ✅ Speaker diarization (multi-speaker)"
    echo "  ✅ Simplified installation (just drag-and-drop)"
    echo "=========================================="
else
    echo "❌ DMG creation failed!"
    exit 1
fi
