#!/usr/bin/env python3
"""Detailed Amazon PA-API diagnostic test."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.utils.config import Config
from amazon_paapi import AmazonApi

def test_raw_api():
    """Test Amazon PA-API directly to see exact error."""
    print("=" * 70)
    print("Amazon PA-API Detailed Diagnostic")
    print("=" * 70)
    
    config = Config()
    access_key = config.require_env("AMAZON_PAAPI_ACCESS_KEY")
    secret_key = config.require_env("AMAZON_PAAPI_SECRET_KEY")
    associate_tag = config.affiliate_tag
    
    print(f"\nAccess Key: {access_key[:10]}...")
    print(f"Secret Key: {secret_key[:10]}...")
    print(f"Associate Tag: {associate_tag}")
    print(f"Marketplace: ES (Spain)")
    
    try:
        print("\nInitializing Amazon PA-API client...")
        api = AmazonApi(
            key=access_key,
            secret=secret_key,
            tag=associate_tag,
            country="ES"
        )
        print("✅ API client created")
        
        test_asin = "B06XGWGGD8"
        print(f"\nFetching product data for ASIN: {test_asin}")
        
        # Try getting item with all resources
        items = api.get_items([test_asin])
        
        if items and len(items) > 0:
            item = items[0]
            print("\n✅ SUCCESS! API returned data:")
            print(f"   Title: {item.item_info.title.display_value if item.item_info.title else 'N/A'}")
            
            if hasattr(item, "offers") and item.offers and item.offers.listings:
                listing = item.offers.listings[0]
                if hasattr(listing, "price") and listing.price:
                    print(f"   Price: €{listing.price.amount}")
                else:
                    print("   Price: Not available")
                    
                if hasattr(listing, "availability"):
                    print(f"   Availability: {listing.availability.type if listing.availability else 'Unknown'}")
            else:
                print("   ⚠️  No offers data returned")
                print("   This product may:")
                print("   - Be unavailable in ES marketplace")
                print("   - Have restricted pricing")
                print("   - Be out of stock")
        else:
            print("\n⚠️  No items returned (empty response)")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nError type:", type(e).__name__)
        
        # Provide specific diagnosis
        error_str = str(e).lower()
        print("\n" + "=" * 70)
        print("DIAGNOSIS")
        print("=" * 70)
        
        if "forbidden" in error_str or "403" in error_str:
            print("❌ API CREDENTIALS ISSUE")
            print("\nThe PA-API is rejecting your credentials with 'Forbidden'.")
            print("\nCommon causes:")
            print("1. Associate Tag not approved for PA-API")
            print("   → Your Amazon Associates account must apply for PA-API access")
            print("   → Go to: https://affiliate-program.amazon.es/assoc_credentials/home")
            print("\n2. PA-API access not activated")
            print("   → PA-API requires separate approval from Associates program")
            print("\n3. Wrong marketplace credentials")
            print("   → Ensure credentials are for amazon.es (Spain)")
            print("\n4. Invalid Access Key or Secret Key")
            print("   → Double-check credentials in .env file")
            
        elif "unauthorized" in error_str or "401" in error_str:
            print("❌ AUTHENTICATION ERROR")
            print("\nThe Access Key or Secret Key is incorrect.")
            print("→ Regenerate credentials at: https://webservices.amazon.es/paapi5/home")
            
        elif "throttled" in error_str or "rate" in error_str:
            print("⚠️  RATE LIMIT EXCEEDED")
            print("\nYou've exceeded the PA-API request limit.")
            print("→ Wait a few minutes and try again")
            
        else:
            print(f"❓ UNKNOWN ERROR: {error_str}")
            print("\n→ Check Amazon PA-API status")
            print("→ Verify all credentials in .env")

if __name__ == "__main__":
    test_raw_api()
