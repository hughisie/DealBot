#!/usr/bin/env python3
"""Test PA-API credentials across different Amazon marketplaces."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.utils.config import Config
from amazon_paapi import AmazonApi

def test_all_marketplaces():
    """Test PA-API with multiple marketplaces to find which one works."""
    print("=" * 70)
    print("Testing PA-API Across Multiple Marketplaces")
    print("=" * 70)
    
    config = Config()
    access_key = config.require_env("AMAZON_PAAPI_ACCESS_KEY")
    secret_key = config.require_env("AMAZON_PAAPI_SECRET_KEY")
    associate_tag = config.affiliate_tag
    
    print(f"\nCredentials:")
    print(f"  Access Key: {access_key[:10]}...")
    print(f"  Secret Key: {secret_key[:10]}...")
    print(f"  Associate Tag: {associate_tag}")
    
    # Test different marketplaces
    marketplaces = {
        "ES": ("B06XGWGGD8", "Spain"),      # Spain
        "UK": ("B07VGRJDFY", "United Kingdom"),
        "US": ("B08N5WRWNW", "United States"),
        "DE": ("B07VGRJDFY", "Germany"),
        "FR": ("B07VGRJDFY", "France"),
        "IT": ("B07VGRJDFY", "Italy"),
    }
    
    successful_marketplace = None
    
    print("\n" + "=" * 70)
    print("Testing Marketplaces")
    print("=" * 70)
    
    for country_code, (test_asin, country_name) in marketplaces.items():
        print(f"\n📍 {country_name} ({country_code})")
        print(f"   ASIN: {test_asin}")
        
        try:
            api = AmazonApi(
                key=access_key,
                secret=secret_key,
                tag=associate_tag,
                country=country_code
            )
            
            items = api.get_items([test_asin])
            
            if items and len(items) > 0:
                item = items[0]
                title = item.item_info.title.display_value if item.item_info.title else "N/A"
                
                # Try to get price
                price = "N/A"
                if hasattr(item, "offers") and item.offers and item.offers.listings:
                    listing = item.offers.listings[0]
                    if hasattr(listing, "price") and listing.price:
                        price = f"{listing.price.display_amount}"
                
                print(f"   ✅ SUCCESS!")
                print(f"   Title: {title[:50]}...")
                print(f"   Price: {price}")
                successful_marketplace = country_code
            else:
                print(f"   ⚠️  No data returned (empty response)")
                
        except Exception as e:
            error_str = str(e).lower()
            if "forbidden" in error_str or "403" in error_str:
                print(f"   ❌ 403 Forbidden - No access to this marketplace")
            elif "not found" in error_str or "404" in error_str:
                print(f"   ⚠️  Product not found in this marketplace")
            else:
                print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    if successful_marketplace:
        print(f"\n✅ PA-API WORKS with {successful_marketplace} marketplace!")
        print(f"\nTo use this marketplace, update config.yaml:")
        print(f"   - For EUR (Spain): Use 'ES' marketplace")
        print(f"   - For GBP (UK): Use 'UK' marketplace")
        print(f"   - For USD (US): Use 'US' marketplace")
        print(f"\nOr the associate tag may be registered for {successful_marketplace} only.")
    else:
        print("\n❌ PA-API FAILED on all marketplaces")
        print("\nPossible issues:")
        print("1. Associate Tag not approved for PA-API")
        print("2. Access Key/Secret Key invalid")
        print("3. PA-API access not activated")
        print("\nNext steps:")
        print("→ Verify PA-API approval at Amazon Associates")
        print("→ Check that tag is linked to PA-API credentials")
        print("→ Ensure PA-API is activated for your account")

if __name__ == "__main__":
    test_all_marketplaces()
