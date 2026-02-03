#!/bin/bash
echo "🔍 Checking DealBot window status..."

# Kill existing instance
echo "⏹️  Stopping DealBot..."
pkill -9 DealBot 2>/dev/null
sleep 1

# Launch app in background
echo "🚀 Launching DealBot..."
open /Applications/DealBot.app

# Wait for app to start
sleep 3

# Check if running
if ps aux | grep -v grep | grep DealBot > /dev/null; then
    echo "✅ DealBot is running"
    PID=$(ps aux | grep -v grep | grep DealBot | awk '{print $2}')
    echo "   PID: $PID"
else
    echo "❌ DealBot is NOT running"
    exit 1
fi

# Check if visible
VISIBLE=$(osascript -e 'tell application "System Events" to tell process "DealBot" to get visible' 2>/dev/null)
echo "   Visible: $VISIBLE"

# Check if frontmost
FRONTMOST=$(osascript -e 'tell application "System Events" to tell process "DealBot" to get frontmost' 2>/dev/null)
echo "   Frontmost: $FRONTMOST"

# Try to activate
echo ""
echo "🔄 Attempting to activate window..."
osascript -e 'tell application "DealBot" to activate' 2>/dev/null
sleep 1

# Check again
FRONTMOST=$(osascript -e 'tell application "System Events" to tell process "DealBot" to get frontmost' 2>/dev/null)
echo "   Frontmost after activation: $FRONTMOST"

echo ""
echo "👀 Please check if you can see the DealBot window now!"
echo "   If you can see it, the fix is working ✅"
echo "   If you cannot see it, there may be another issue ❌"
