#!/usr/bin/env python3
"""Test PA-API with raw request debugging."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from amazon_paapi import AmazonApi
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)

def test_with_debug():
    """Test PA-API with full debug output."""
    print("=" * 70)
    print("PA-API Raw Request Debug Test")
    print("=" * 70)
    
    # Credentials from screenshot
    access_key = "AKPAQ1JMQD1763062287"
    secret_key = "TTBuZCqH54WjKyrPK6l1otcoMmnyrDvwLUSk5WZl"
    
    # Test different tag and marketplace combinations
    test_configs = [
        ("retroshell00-20", "US", "B08N5WRWNW"),  # US marketplace
        ("retroshell00-20", "ES", "B06XGWGGD8"),  # Spain marketplace
        ("retroshell00-20", "UK", "B07VGRJDFY"),  # UK marketplace
    ]
    
    for tag, country, asin in test_configs:
        print(f"\n{'=' * 70}")
        print(f"Testing: {country} marketplace with tag={tag}")
        print(f"ASIN: {asin}")
        print('=' * 70)
        
        try:
            # Create API with explicit parameters
            api = AmazonApi(
                key=access_key,
                secret=secret_key,
                tag=tag,
                country=country,
                throttling=0.9  # Stay under rate limits
            )
            
            print(f"API client created for {country}")
            print(f"Making GetItems request...")
            
            # Try to get items
            items = api.get_items([asin])
            
            if items and len(items) > 0:
                item = items[0]
                print(f"\n✅ SUCCESS!")
                title = item.item_info.title.display_value if item.item_info.title else "N/A"
                print(f"Title: {title[:60]}...")
                
                # Get price
                if hasattr(item, "offers") and item.offers and item.offers.listings:
                    listing = item.offers.listings[0]
                    if hasattr(listing, "price") and listing.price:
                        print(f"Price: {listing.price.display_amount}")
                
                print(f"\n🎉 WORKING CONFIGURATION:")
                print(f"   Marketplace: {country}")
                print(f"   Tag: {tag}")
                return True
            else:
                print("⚠️ Empty response (no items returned)")
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error: {error_msg}")
            
            # Check specific error types
            if "Forbidden" in error_msg or "403" in error_msg:
                print("   → 403 Forbidden: Access denied")
            elif "InvalidParameterValue" in error_msg:
                print("   → Invalid parameter in request")
            elif "InvalidClientTokenId" in error_msg:
                print("   → Invalid Access Key")
            elif "SignatureDoesNotMatch" in error_msg:
                print("   → Invalid Secret Key or signature issue")
            elif "InvalidAssociateTag" in error_msg:
                print("   → Associate Tag not valid for this marketplace")
    
    return False

if __name__ == "__main__":
    success = test_with_debug()
    
    if not success:
        print("\n" + "=" * 70)
        print("DETAILED DIAGNOSTICS")
        print("=" * 70)
        
        print("\nChecking credential format:")
        access_key = "AKPAQ1JMQD1763062287"
        secret_key = "TTBuZCqH54WjKyrPK6l1otcoMmnyrDvwLUSk5WZl"
        
        print(f"  Access Key length: {len(access_key)} chars")
        print(f"  Secret Key length: {len(secret_key)} chars")
        print(f"  Access Key starts with: AKPA (PA-API key) ✓")
        
        print("\nPossible issues:")
        print("  1. Associate Tag not linked to Access Key")
        print("  2. Wrong marketplace for this Associate account")
        print("  3. Missing PA-API permissions")
        print("  4. Secret key copied incorrectly (check for spaces)")
