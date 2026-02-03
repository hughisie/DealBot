#!/bin/bash

echo "=================================================="
echo "DEALBOT COMPREHENSIVE TEST MONITOR"
echo "=================================================="
echo ""

echo "1. Checking running processes..."
PROCESS_COUNT=$(ps aux | grep "DealBot.app" | grep -v grep | wc -l | tr -d ' ')
echo "   DealBot processes running: $PROCESS_COUNT"
if [ "$PROCESS_COUNT" -eq "2" ]; then
    echo "   ✅ PASS: Correct number of processes (2 = 1 main + 1 tracker)"
else
    echo "   ❌ FAIL: Expected 2 processes, found $PROCESS_COUNT"
fi
echo ""

echo "2. Checking app initialization..."
if tail -50 ~/Library/Logs/DealBot/dealbot.log | grep -q "DealBot ready"; then
    echo "   ✅ PASS: App initialized successfully"
else
    echo "   ❌ FAIL: App not ready"
fi
echo ""

echo "3. Monitoring log file for activity..."
echo "   Last 10 log entries:"
tail -10 ~/Library/Logs/DealBot/dealbot.log | sed 's/^/   | /'
echo ""

echo "=================================================="
echo "LIVE LOG MONITORING (Ctrl+C to stop)"
echo "=================================================="
tail -f ~/Library/Logs/DealBot/dealbot.log | grep --line-buffered -E "Loading file|Parsed|Processing|Processed|Preview ready|ERROR"
