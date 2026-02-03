#!/usr/bin/env python3
"""Test PA-API with US marketplace."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.utils.config import Config
from amazon_paapi import AmazonApi

def test_us_marketplace():
    """Test PA-API with US marketplace specifically."""
    print("=" * 70)
    print("Testing PA-API with US Marketplace")
    print("=" * 70)
    
    config = Config()
    access_key = config.require_env("AMAZON_PAAPI_ACCESS_KEY")
    secret_key = config.require_env("AMAZON_PAAPI_SECRET_KEY")
    associate_tag = config.affiliate_tag
    
    print(f"\nCredentials from Amazon Associates:")
    print(f"  Access Key: {access_key}")
    print(f"  Store ID: {associate_tag}")
    print(f"  Testing: US marketplace (amazon.com)")
    
    try:
        print("\n" + "=" * 70)
        print("Creating API client for US...")
        print("=" * 70)
        
        api = AmazonApi(
            key=access_key,
            secret=secret_key,
            tag=associate_tag,
            country="US"  # US marketplace
        )
        print("✅ API client created")
        
        # Test with a US ASIN
        test_asin = "B08N5WRWNW"  # Example US product
        print(f"\nTesting with US ASIN: {test_asin}")
        
        items = api.get_items([test_asin])
        
        if items and len(items) > 0:
            item = items[0]
            
            print("\n" + "=" * 70)
            print("✅ SUCCESS! PA-API IS WORKING!")
            print("=" * 70)
            
            # Extract details
            title = item.item_info.title.display_value if item.item_info.title else "N/A"
            print(f"\nProduct Details:")
            print(f"  Title: {title[:60]}...")
            
            # Get price
            if hasattr(item, "offers") and item.offers and item.offers.listings:
                listing = item.offers.listings[0]
                if hasattr(listing, "price") and listing.price:
                    print(f"  Price: {listing.price.display_amount}")
                    print(f"  Currency: {listing.price.currency}")
                
                if hasattr(listing, "availability"):
                    print(f"  Availability: {listing.availability.type if listing.availability else 'Unknown'}")
            
            print("\n" + "=" * 70)
            print("DIAGNOSIS")
            print("=" * 70)
            print("\n✅ Your PA-API credentials ARE VALID!")
            print("\n⚠️  ISSUE IDENTIFIED:")
            print("   Your credentials are for amazon.com (US)")
            print("   But DealBot is configured for amazon.es (Spain)")
            
            print("\n📝 SOLUTION:")
            print("   Option 1: Use US marketplace (if you work with US products)")
            print("   Option 2: Get separate credentials for amazon.es")
            
        else:
            print("\n⚠️ API worked but returned no data for this ASIN")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nIf you still get 403, your credentials might be for a specific marketplace")

if __name__ == "__main__":
    test_us_marketplace()
