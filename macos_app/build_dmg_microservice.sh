#!/bin/bash
set -e

echo "🚀 Building English Practice macOS App (Microservice Architecture)..."
echo ""

# Clean previous builds
echo "1️⃣  Cleaning previous builds..."
rm -rf build dist dmg_contents
rm -f English_Practice_*.dmg

# Build .app (lightweight client)
echo "2️⃣  Building .app bundle (UI client only)..."
python setup_microservice.py py2app

# Check if .app exists
if [ ! -d "dist/English Practice.app" ]; then
    echo "❌ App build failed!"
    exit 1
fi

echo "✅ App built successfully!"

# Create DMG contents folder
echo "3️⃣  Preparing DMG contents..."
mkdir -p dmg_contents

# Copy .app to DMG contents
cp -r "dist/English Practice.app" dmg_contents/

# Copy backend to DMG contents
echo "4️⃣  Copying backend server..."
cd ..
mkdir -p macos_app/dmg_contents/Backend

# Copy backend files
cp backend/server.py macos_app/dmg_contents/Backend/
cp backend/start_backend.sh macos_app/dmg_contents/Backend/
cp backend/com.exodus.englishpractice.backend.plist macos_app/dmg_contents/Backend/

# Copy core analyzer files
cp analyzer_diarization.py macos_app/dmg_contents/Backend/
cp cambridge_grammar_rules.py macos_app/dmg_contents/Backend/
cp requirements.txt macos_app/dmg_contents/Backend/
cp .env.example macos_app/dmg_contents/Backend/

# Make scripts executable
chmod +x macos_app/dmg_contents/Backend/start_backend.sh

# Create installation script
cat > macos_app/dmg_contents/Backend/install.sh << 'EOF'
#!/bin/bash
# English Practice Backend Installation Script

echo "🚀 Installing English Practice Backend..."
echo ""

# Get user home directory
USER_HOME="$HOME"
INSTALL_DIR="$USER_HOME/Library/Application Support/EnglishPractice"

# Create installation directory
echo "1️⃣  Creating installation directory..."
mkdir -p "$INSTALL_DIR"

# Copy files
echo "2️⃣  Copying backend files..."
cp -r . "$INSTALL_DIR/"

# Setup virtual environment
echo "3️⃣  Setting up Python environment..."
cd "$INSTALL_DIR"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup .env if needed
if [ ! -f ".env" ]; then
    echo "4️⃣  Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env to add your HUGGINGFACE_TOKEN"
    echo "   (Required for speaker diarization)"
    echo ""
    echo "   Get token: https://huggingface.co/settings/tokens"
    echo ""
fi

# Install launchd service
echo "5️⃣  Installing auto-start service..."
PLIST_FILE="$USER_HOME/Library/LaunchAgents/com.exodus.englishpractice.backend.plist"

# Replace placeholders in plist
sed "s|INSTALL_PATH|$INSTALL_DIR|g; s|HOME|$USER_HOME|g" \
    com.exodus.englishpractice.backend.plist > "$PLIST_FILE"

# Load service
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Backend server is now running at: http://localhost:8780"
echo "Logs: $USER_HOME/.english_practice/backend.log"
echo ""
echo "To check status:"
echo "  curl http://localhost:8780/health"
echo ""
echo "To manually start/stop:"
echo "  launchctl start com.exodus.englishpractice.backend"
echo "  launchctl stop com.exodus.englishpractice.backend"
echo ""
echo "Now you can launch 'English Practice.app' from Applications folder!"
echo ""
EOF

chmod +x macos_app/dmg_contents/Backend/install.sh

# Create README for DMG
cat > macos_app/dmg_contents/README.txt << 'EOF'
English Speaking Practice v2.0
===============================

INSTALLATION:

1. Drag "English Practice.app" to your Applications folder
2. Open Terminal and run:
   cd "/Volumes/English Practice v2/Backend"
   ./install.sh
3. Launch "English Practice" from Applications

REQUIREMENTS:

- macOS 10.14 or later
- Python 3.9+ (usually pre-installed)
- Microphone access (will be requested on first run)

OPTIONAL:

For speaker diarization (multi-speaker detection):
1. Get Hugging Face token: https://huggingface.co/settings/tokens
2. Edit: ~/Library/Application Support/EnglishPractice/.env
3. Add: HUGGINGFACE_TOKEN=hf_your_token_here

FEATURES:

✅ Grammar analysis (Cambridge Grammar)
✅ Fluency metrics (WPM, pauses)
✅ Pronunciation (WER)
✅ Speaker diarization (optional)
✅ Timestamps for all errors
✅ Summary + Top-3 + Timeline format

TROUBLESHOOTING:

If app shows "Backend not running":
  cd ~/Library/Application\ Support/EnglishPractice/
  ./Backend/install.sh

Check backend status:
  curl http://localhost:8780/health

View logs:
  tail -f ~/.english_practice/backend.log

SUPPORT:

Documentation: See Backend/README.md
Issues: [Your GitHub/support URL]

Built with ❤️ for English learners
EOF

# Return to macos_app directory
cd macos_app

# Create DMG
echo "5️⃣  Creating DMG installer..."

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    echo "⚠️  create-dmg not found. Installing..."
    brew install create-dmg
fi

VERSION="2.0"
DMG_NAME="English_Practice_${VERSION}.dmg"

create-dmg \
  --volname "English Practice v2" \
  --window-pos 200 120 \
  --window-size 700 500 \
  --icon-size 100 \
  --icon "English Practice.app" 150 150 \
  --icon "Backend" 350 150 \
  --icon "README.txt" 550 150 \
  --hide-extension "English Practice.app" \
  --app-drop-link 150 320 \
  --no-internet-enable \
  "$DMG_NAME" \
  "dmg_contents/" \
  2>/dev/null || true

# Fallback: simple DMG if create-dmg fails
if [ ! -f "$DMG_NAME" ]; then
    echo "⚠️  create-dmg failed, creating simple DMG..."
    hdiutil create -volname "English Practice v2" -srcfolder "dmg_contents" -ov -format UDZO "$DMG_NAME"
fi

if [ -f "$DMG_NAME" ]; then
    echo ""
    echo "🎉 SUCCESS!"
    echo "=========================================="
    echo "DMG created: $DMG_NAME"
    echo "Size: $(du -h "$DMG_NAME" | cut -f1)"
    echo ""
    echo "Contents:"
    echo "  - English Practice.app (menu bar app)"
    echo "  - Backend/ (analysis server)"
    echo "  - README.txt (installation guide)"
    echo ""
    echo "To test:"
    echo "  open $DMG_NAME"
    echo ""
    echo "Installation steps for users:"
    echo "  1. Drag English Practice.app to Applications"
    echo "  2. cd \"/Volumes/English Practice v2/Backend\""
    echo "  3. ./install.sh"
    echo "  4. Launch app from Applications"
    echo ""
    echo "Features:"
    echo "  ✅ Speaker diarization (multi-speaker)"
    echo "  ✅ Timestamps for all errors"
    echo "  ✅ Summary + Top-3 + Timeline"
    echo "  ✅ Cambridge Grammar explanations"
    echo "  ✅ Microservice architecture"
    echo "=========================================="
else
    echo "❌ DMG creation failed!"
    exit 1
fi
