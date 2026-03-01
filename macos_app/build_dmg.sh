#!/bin/bash
set -e

echo "🚀 Building English Practice macOS App..."
echo ""

# 1. Clean previous builds
echo "1️⃣  Cleaning previous builds..."
rm -rf build dist
rm -f English_Practice_*.dmg

# 2. Build .app
echo "2️⃣  Building .app bundle..."
python setup.py py2app

# 3. Check if .app exists
if [ ! -d "dist/English Practice.app" ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✅ .app built successfully!"

# 4. Test .app (optional)
echo "3️⃣  Testing .app..."
# open "dist/English Practice.app" &
# sleep 3
# killall "English Practice" 2>/dev/null || true

# 5. Create DMG
echo "4️⃣  Creating DMG installer..."

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    echo "⚠️  create-dmg not found. Installing..."
    brew install create-dmg
fi

# Build DMG
VERSION="1.0.0"
DMG_NAME="English_Practice_${VERSION}.dmg"

create-dmg \
  --volname "English Practice" \
  --volicon "dist/English Practice.app/Contents/Resources/app.icns" \
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

if [ -f "$DMG_NAME" ]; then
    echo ""
    echo "🎉 SUCCESS!"
    echo "="*60
    echo "DMG created: $DMG_NAME"
    echo "Size: $(du -h "$DMG_NAME" | cut -f1)"
    echo ""
    echo "To test:"
    echo "  open $DMG_NAME"
    echo ""
    echo "To distribute:"
    echo "  - Upload to GitHub releases"
    echo "  - Share download link"
    echo "  - Users drag to Applications folder"
    echo "="*60
else
    echo "⚠️  DMG creation had warnings, but may have succeeded"
    echo "Check for .dmg file manually"
fi
