#!/bin/bash
# Run this script tomorrow (Nov 14) or Friday (Nov 15) to check if PA-API is active

cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"

echo "=============================================="
echo "Checking PA-API Activation Status"
echo "=============================================="
echo ""
echo "Testing PA-API credentials..."
echo ""

./venv/bin/python3 test_api_detailed.py

echo ""
echo "=============================================="
echo "Next Steps:"
echo "=============================================="
echo ""
echo "If you see '✅ SUCCESS!':"
echo "  → Run: ./rebuild_app.sh"
echo "  → Your PA-API is now active!"
echo ""
echo "If you still see '❌ 403 Forbidden':"
echo "  → Wait another 24 hours"
echo "  → Or contact Amazon Associates support"
echo ""
