#!/bin/bash
# Quick rebuild and reinstall script for DealBot macOS app

set -e  # Exit on error

cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"

echo "🔄 Syncing source code from adp/ to dealbot/..."
cp -r adp/* dealbot/

echo "🎨 Generating ICNS icon..."
./create_icns.sh

echo "🗑️  Removing old app..."
rm -rf /Applications/DealBot.app

echo "🔨 Building DealBot macOS app..."
./venv/bin/briefcase build macOS

echo "📄 Bundling config files..."
cp config.yaml build/dealbot/macos/app/DealBot.app/Contents/Resources/
cp .env build/dealbot/macos/app/DealBot.app/Contents/Resources/

echo "📦 Installing to /Applications..."
cp -r build/dealbot/macos/app/DealBot.app /Applications/

echo "🔄 Resetting Launchpad and Dock..."
defaults write com.apple.dock ResetLaunchPad -bool true
killall Dock

echo ""
echo "✅ Done! DealBot has been updated."
echo "🚀 Open Launchpad to see your updated DealBot with custom icon!"
echo "⏱️  Wait a few seconds for Launchpad to refresh..."
echo ""
echo "📝 Testing app launch..."
open /Applications/DealBot.app
sleep 3
if ps aux | grep -v grep | grep -q "/Applications/DealBot.app"; then
    echo "✅ App is running successfully!"
else
    echo "⚠️  App may not have launched. Check for errors."
fi
