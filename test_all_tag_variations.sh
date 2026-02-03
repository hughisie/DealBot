#!/bin/bash
# Test all possible tracking ID variations

cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"

echo "======================================================================"
echo "Testing All Possible Tracking ID Variations"
echo "======================================================================"
echo ""

# Array of possible tracking ID formats
TAGS=(
    "retroshell00-20"
    "retroshell-20"
    "retroshell0020-20"
    "retroshell00-21"
    "retroshell-21"
)

# Array of possible marketplaces
MARKETPLACES=("US" "UK" "ES")

echo "This will test ${#TAGS[@]} tag variations across ${#MARKETPLACES[@]} marketplaces"
echo ""

for TAG in "${TAGS[@]}"; do
    for MARKETPLACE in "${MARKETPLACES[@]}"; do
        echo "Testing: Tag='$TAG' Marketplace='$MARKETPLACE'"
        
        # Create temporary test script
        cat > /tmp/test_paapi_combo.py << EOPYTHON
from amazon_paapi import AmazonApi

try:
    api = AmazonApi(
        key="AKPAQ1JMQD1763062287",
        secret="TTBuZCqH54WjKyrPK6l1otcoMmnyrDvwLUSk5WZl",
        tag="$TAG",
        country="$MARKETPLACE"
    )
    
    test_asins = {
        "US": "B08N5WRWNW",
        "UK": "B07VGRJDFY", 
        "ES": "B06XGWGGD8"
    }
    
    items = api.get_items([test_asins["$MARKETPLACE"]])
    
    if items and len(items) > 0:
        print("✅ SUCCESS!")
        print(f"   Product: {items[0].item_info.title.display_value[:50]}...")
        exit(0)
    else:
        print("⚠️  Empty response")
        exit(1)
        
except Exception as e:
    error = str(e)
    if "Forbidden" in error:
        print("❌ 403 Forbidden")
    elif "InvalidPartnerTag" in error:
        print("❌ Invalid Partner Tag")
    else:
        print(f"❌ Error: {error[:50]}...")
    exit(1)
EOPYTHON

        ./venv/bin/python3 /tmp/test_paapi_combo.py
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "======================================================================"
            echo "🎉 FOUND WORKING CONFIGURATION!"
            echo "======================================================================"
            echo ""
            echo "Update your .env file with:"
            echo "  AMAZON_ASSOCIATE_TAG=$TAG"
            echo ""
            echo "Marketplace: $MARKETPLACE"
            echo ""
            echo "To update DealBot:"
            echo "  1. Edit .env: nano .env"
            echo "  2. Set: AMAZON_ASSOCIATE_TAG=$TAG"
            echo "  3. Rebuild: ./rebuild_app.sh"
            echo ""
            exit 0
        fi
        
        echo ""
    done
done

echo "======================================================================"
echo "❌ None of the combinations worked"
echo "======================================================================"
echo ""
echo "This means:"
echo "  1. The tracking ID is different from the tested variations"
echo "  2. The tracking ID is not linked to this Access Key"
echo "  3. PA-API access is not properly enabled"
echo ""
echo "Next steps:"
echo "  → Log into Amazon Associates dashboard"
echo "  → Find 'Manage Tracking IDs' section"
echo "  → Check which tracking ID is linked to Access Key: AKPAQ1JMQD1763062287"
echo "  → Use that EXACT tracking ID"
echo ""
