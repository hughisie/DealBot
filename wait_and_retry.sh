#!/bin/bash
# Wait and retry PA-API test every minute until it works

cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"

echo "======================================================================"
echo "PA-API Activation Monitor"
echo "======================================================================"
echo ""
echo "Access Key: AKPA0DQU0S1763063154"
echo "Created: Thu Nov 13 19:45:54 UTC 2025"
echo "Tracking IDs: retroshell00-20, amazoneschollos-20"
echo ""
echo "Waiting for Amazon to link tracking IDs to credentials..."
echo "This typically takes 5-30 minutes"
echo ""
echo "Testing every 60 seconds (max 60 minutes)"
echo "Press Ctrl+C to stop"
echo ""

MAX_ATTEMPTS=60
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "======================================================================"
    ELAPSED=$((ATTEMPT - 1))
    echo "Attempt $ATTEMPT of $MAX_ATTEMPTS | Elapsed: $ELAPSED minutes | $(date '+%H:%M:%S')"
    echo "======================================================================"

    # Run test and capture output
    OUTPUT=$(./venv/bin/python3 test_both_tracking_ids.py 2>&1)

    # Check if SUCCESS appears in output
    if echo "$OUTPUT" | grep -q "SUCCESS"; then
        echo ""
        echo "$OUTPUT"
        echo ""
        echo "======================================================================"
        echo "🎉 PA-API IS NOW WORKING!"
        echo "======================================================================"
        echo ""
        echo "Your DealBot can now use PA-API for real-time Amazon data!"
        echo ""
        echo "Rebuild the app to use new credentials:"
        echo "  ./rebuild_app.sh"
        echo ""
        exit 0
    fi

    # Show error status
    if echo "$OUTPUT" | grep -q "403"; then
        echo "⏳ Status: 403 Forbidden (tracking IDs not linked yet)"
    elif echo "$OUTPUT" | grep -q "401"; then
        echo "❌ Status: 401 Unauthorized (invalid credentials)"
        echo ""
        echo "This is unexpected. Please check your credentials:"
        echo "  - Access Key: AKPA0DQU0S1763063154"
        echo "  - Make sure you didn't delete these credentials"
        break
    else
        echo "❓ Status: Unknown error"
    fi

    if [ $ATTEMPT -lt $MAX_ATTEMPTS ]; then
        echo "Waiting 60 seconds before next attempt..."
        echo ""
        sleep 60
    fi

    ATTEMPT=$((ATTEMPT + 1))
done

echo ""
echo "======================================================================"
echo "⏰ Monitoring stopped after $((MAX_ATTEMPTS - 1)) minutes"
echo "======================================================================"
echo ""
echo "PA-API still showing 403 Forbidden"
echo ""
echo "Next steps:"
echo "1. Check Amazon Associates dashboard for tracking ID linkage"
echo "2. Verify credentials are for the correct marketplace (US/UK/ES)"
echo "3. Contact Amazon Support if issue persists after 24 hours"
echo ""
echo "Note: DealBot continues to work using TXT file prices as fallback"
echo ""
