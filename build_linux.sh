#!/bin/bash
# ──────────────────────────────────────────────
# Build script for دادیار هوشمند (Linux)
# ──────────────────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔨 Building دادیار هوشمند ..."
echo ""

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Ensure pyinstaller is installed
pip install pyinstaller -q 2>/dev/null

# Clean previous build
rm -rf build/ dist/

# Build
echo "📦 Running PyInstaller..."
pyinstaller dadyar.spec --noconfirm 2>&1 | tail -20

# Check result
if [ -f "dist/dadyar/dadyar" ]; then
    SIZE=$(du -sh dist/dadyar/ | cut -f1)
    echo ""
    echo "✅ Build successful!"
    echo "   📁 Output: dist/dadyar/"
    echo "   📏 Size: $SIZE"
    echo ""
    echo "   To run:"
    echo "   ./dist/dadyar/dadyar"
    echo ""
    echo "   To distribute: zip the dist/dadyar/ folder"
else
    echo "❌ Build failed!"
    exit 1
fi
