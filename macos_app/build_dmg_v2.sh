#!/bin/bash
set -e

echo "🚀 Building English Practice macOS App v2..."
echo ""

# 1. Clean previous builds
echo "1️⃣  Cleaning previous builds..."
rm -rf build dist
rm -f English_Practice_*.dmg

# 2. Build .app
echo "2️⃣  Building .app bundle with Speaker Diarization..."
python setup_v2.py py2app

# 3. Check if .app exists
if [ ! -d "dist/English Practice.app" ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ .app built successfully!"

# 4. Create DMG
echo "3️⃣  Creating DMG installer..."

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    echo "⚠️  create-dmg not found. Installing..."
    brew install create-dmg
fi

# Build DMG
VERSION="2.0"
DMG_NAME="English_Practice_${VERSION}.dmg"

create-dmg \
  --volname "English Practice v2" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "English Practice.app" 175 120 \
  --hide-extension "English Practice.app" \
  --app-drop-link 425 120 \
  --no-internet-enable \
  "$DMG_NAME" \
  "dist/" \
  2>/dev/null || true

# Fallback: simple DMG if create-dmg fails
if [ ! -f "$DMG_NAME" ]; then
    echo "⚠️  create-dmg failed, creating simple DMG..."
    hdiutil create -volname "English Practice" -srcfolder "dist" -ov -format UDZO "$DMG_NAME"
fi

if [ -f "$DMG_NAME" ]; then
    echo ""
    echo "🎉 SUCCESS!"
    echo "=========================================="
    echo "DMG created: $DMG_NAME"
    echo "Size: $(du -h "$DMG_NAME" | cut -f1)"
    echo ""
    echo "To test:"
    echo "  open $DMG_NAME"
    echo ""
    echo "Features:"
    echo "  ✅ Speaker diarization (multi-speaker)"
    echo "  ✅ Timestamps for all errors"
    echo "  ✅ Summary + Top-3 + Timeline format"
    echo "  ✅ Cambridge Grammar explanations"
    echo ""
    echo "To distribute:"
    echo "  - Upload to GitHub releases"
    echo "  - Share download link"
    echo "  - Users drag to Applications folder"
    echo "=========================================="
else
    echo "❌ DMG creation failed!"
    exit 1
fi
