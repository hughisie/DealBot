#!/usr/bin/env python3
"""Test different associate tag formats."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.utils.config import Config
from amazon_paapi import AmazonApi

def test_tag_formats():
    """Test PA-API with different tag formats."""
    print("=" * 70)
    print("Testing Different Associate Tag Formats")
    print("=" * 70)
    
    config = Config()
    access_key = "AKPAQ1JMQD1763062287"  # From screenshot
    secret_key = "TTBuZCqH54WjKyrPK6l1otcoMmnyrDvwLUSk5WZl"  # From your message
    
    # Try different tag formats
    tag_formats = [
        "retroshell00-20",      # Current format
        "retroshell0020-20",    # Without hyphen in middle
        "retroshell-20",        # Simplified
        "retroshell00-21",      # -21 ending (common for US)
    ]
    
    for tag in tag_formats:
        print(f"\n{'=' * 70}")
        print(f"Testing tag: {tag}")
        print('=' * 70)
        
        try:
            # Try US marketplace
            api = AmazonApi(
                key=access_key,
                secret=secret_key,
                tag=tag,
                country="US"
            )
            
            items = api.get_items(["B08N5WRWNW"])
            
            if items and len(items) > 0:
                print(f"✅ SUCCESS with tag: {tag}")
                item = items[0]
                title = item.item_info.title.display_value if item.item_info.title else "N/A"
                print(f"   Product: {title[:50]}...")
                
                # Get price if available
                if hasattr(item, "offers") and item.offers and item.offers.listings:
                    listing = item.offers.listings[0]
                    if hasattr(listing, "price") and listing.price:
                        print(f"   Price: {listing.price.display_amount}")
                
                print(f"\n🎉 WORKING TAG FOUND: {tag}")
                print(f"   Update your .env with: AMAZON_ASSOCIATE_TAG={tag}")
                return tag
            else:
                print(f"⚠️  Tag {tag}: API responded but no data")
                
        except Exception as e:
            error_str = str(e).lower()
            if "forbidden" in error_str:
                print(f"❌ Tag {tag}: 403 Forbidden")
            else:
                print(f"❌ Tag {tag}: {e}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print("\n❌ None of the tag formats worked")
    print("\n🔍 Next steps:")
    print("1. Check your Amazon Associates dashboard")
    print("2. Look for 'Tracking IDs' or 'Store IDs'") 
    print("3. Find which Tracking ID is linked to Access Key: AKPAQ1JMQD1763062287")
    print("4. That's the exact tag format to use")
    print("\nOR:")
    print("→ The credentials might be for UK marketplace (amazon.co.uk)")
    print("→ Try checking which marketplace your Associates account is registered with")

if __name__ == "__main__":
    test_tag_formats()
