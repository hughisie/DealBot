#!/bin/bash
# Create proper ICNS icon for macOS from PNG

set -e

echo "🎨 Creating macOS ICNS icon from PNG..."

# Create iconset directory
mkdir -p resources/DealBot.iconset

# Copy PNGs to iconset with correct names
cp resources/icon-16.png resources/DealBot.iconset/icon_16x16.png
cp resources/icon-32.png resources/DealBot.iconset/icon_16x16@2x.png
cp resources/icon-32.png resources/DealBot.iconset/icon_32x32.png
cp resources/icon-64.png resources/DealBot.iconset/icon_32x32@2x.png
cp resources/icon-128.png resources/DealBot.iconset/icon_128x128.png
cp resources/icon-256.png resources/DealBot.iconset/icon_128x128@2x.png
cp resources/icon-256.png resources/DealBot.iconset/icon_256x256.png
cp resources/icon-512.png resources/DealBot.iconset/icon_256x256@2x.png
cp resources/icon-512.png resources/DealBot.iconset/icon_512x512.png
cp resources/icon-1024.png resources/DealBot.iconset/icon_512x512@2x.png

# Convert to ICNS
iconutil -c icns resources/DealBot.iconset -o resources/icon.icns

# Clean up
rm -rf resources/DealBot.iconset

echo "✅ Created resources/icon.icns"
