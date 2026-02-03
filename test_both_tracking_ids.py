#!/usr/bin/env python3
"""Test BOTH tracking IDs with new credentials."""

from amazon_paapi import AmazonApi

def test_tracking_ids():
    """Test both amazoneschollos-20 and retroshell00-20."""
    
    print("=" * 70)
    print("Testing BOTH Tracking IDs with NEW Credentials")
    print("=" * 70)
    
    # NEW credentials from screenshot
    access_key = "AKPA0DQU0S1763063154"
    secret_key = "8M+aK0sKmYBjxfQk2HL6KdEKuiJtX13xpQiNuDWL"
    
    print(f"\nCredentials:")
    print(f"  Access Key: {access_key}")
    print(f"  Secret Key: {secret_key[:15]}...")
    
    # Both tracking IDs from screenshot
    tracking_ids = [
        "amazoneschollos-20",  # Selected/default one
        "retroshell00-20",      # Alternative one
    ]
    
    # Test marketplaces
    marketplaces = [
        ("ES", "B06XGWGGD8", "Spain"),
        ("US", "B08N5WRWNW", "United States"),
        ("UK", "B07VGRJDFY", "United Kingdom"),
    ]
    
    for tag in tracking_ids:
        print(f"\n{'=' * 70}")
        print(f"Testing Tracking ID: {tag}")
        print('=' * 70)
        
        for country, asin, name in marketplaces:
            print(f"\n📍 {name} ({country}) - ASIN: {asin}")
            
            try:
                api = AmazonApi(
                    key=access_key,
                    secret=secret_key,
                    tag=tag,
                    country=country
                )
                
                items = api.get_items([asin])
                
                if items and len(items) > 0:
                    item = items[0]
                    title = item.item_info.title.display_value if item.item_info.title else "N/A"
                    
                    print(f"   🎉 SUCCESS!")
                    print(f"   Title: {title[:50]}...")
                    
                    # Get price
                    if hasattr(item, "offers") and item.offers and item.offers.listings:
                        listing = item.offers.listings[0]
                        if hasattr(listing, "price") and listing.price:
                            print(f"   Price: {listing.price.display_amount}")
                    
                    print(f"\n{'=' * 70}")
                    print(f"✅ PA-API IS WORKING!")
                    print('=' * 70)
                    print(f"\nWorking Configuration:")
                    print(f"  Access Key: {access_key}")
                    print(f"  Tracking ID: {tag}")
                    print(f"  Marketplace: {country} ({name})")
                    print(f"\nUpdate .env with:")
                    print(f"  AMAZON_PAAPI_ACCESS_KEY={access_key}")
                    print(f"  AMAZON_PAAPI_SECRET_KEY={secret_key}")
                    print(f"  AMAZON_ASSOCIATE_TAG={tag}")
                    return True, tag, country
                else:
                    print(f"   ⚠️  Empty response")
                    
            except Exception as e:
                error_str = str(e)
                if "Forbidden" in error_str or "403" in error_str:
                    print(f"   ❌ 403 Forbidden")
                elif "InvalidPartnerTag" in error_str:
                    print(f"   ❌ Invalid Partner Tag")
                elif "SignatureDoesNotMatch" in error_str:
                    print(f"   ❌ Invalid Secret Key")
                else:
                    print(f"   ❌ Error: {error_str[:60]}...")
    
    return False, None, None

if __name__ == "__main__":
    success, working_tag, working_marketplace = test_tracking_ids()
    
    if not success:
        print("\n" + "=" * 70)
        print("❌ STILL NOT WORKING")
        print("=" * 70)
        print("\nPossible reasons:")
        print("1. Credentials were just created - may need a few minutes")
        print("2. Tracking IDs not yet linked to this Access Key")
        print("3. PA-API not enabled for these tracking IDs")
        print("\nWait 5-10 minutes and run again:")
        print("  ./venv/bin/python3 test_both_tracking_ids.py")
