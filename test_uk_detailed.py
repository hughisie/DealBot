#!/usr/bin/env python3
"""Test PA-API with UK marketplace in detail."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from amazon_paapi import AmazonApi

def test_uk_marketplace():
    """Test PA-API with UK marketplace."""
    print("=" * 70)
    print("Testing PA-API with UK Marketplace (amazon.co.uk)")
    print("=" * 70)
    
    access_key = "AKPAQ1JMQD1763062287"
    secret_key = "TTBuZCqH54WjKyrPK6l1otcoMmnyrDvwLUSk5WZl"
    associate_tag = "retroshell00-20"
    
    print(f"\nCredentials:")
    print(f"  Access Key: {access_key}")
    print(f"  Secret Key: {secret_key[:10]}...")
    print(f"  Associate Tag: {associate_tag}")
    print(f"  Marketplace: UK (amazon.co.uk)")
    
    try:
        print("\nCreating API client for UK...")
        api = AmazonApi(
            key=access_key,
            secret=secret_key,
            tag=associate_tag,
            country="UK"  # UK marketplace
        )
        print("✅ API client created")
        
        # Test with UK ASIN
        test_asin = "B07VGRJDFY"  # Common UK product
        print(f"\nFetching product: {test_asin}")
        
        items = api.get_items([test_asin])
        
        if items and len(items) > 0:
            item = items[0]
            
            print("\n" + "=" * 70)
            print("🎉 SUCCESS! PA-API IS WORKING!")
            print("=" * 70)
            
            title = item.item_info.title.display_value if item.item_info.title else "N/A"
            print(f"\nProduct:")
            print(f"  Title: {title[:60]}...")
            print(f"  ASIN: {test_asin}")
            
            # Get price
            if hasattr(item, "offers") and item.offers and item.offers.listings:
                listing = item.offers.listings[0]
                if hasattr(listing, "price") and listing.price:
                    print(f"  Price: {listing.price.display_amount}")
                if hasattr(listing, "availability"):
                    avail = listing.availability.type if listing.availability else "Unknown"
                    print(f"  Availability: {avail}")
            
            print("\n" + "=" * 70)
            print("SOLUTION FOUND!")
            print("=" * 70)
            print("\n✅ Your PA-API credentials work with UK marketplace (amazon.co.uk)")
            print("\n📝 To use UK marketplace in DealBot:")
            print("   1. Currency should be GBP (not EUR)")
            print("   2. Products must be from amazon.co.uk (not amazon.es)")
            
            print("\n⚠️  PROBLEM:")
            print("   Your TXT files have amazon.es (Spain) links")
            print("   But your PA-API is for amazon.co.uk (UK)")
            
            print("\n🔧 OPTIONS:")
            print("   A) Get separate PA-API credentials for amazon.es")
            print("      → Register at: https://afiliados.amazon.es")
            print("   B) Switch to amazon.co.uk products")
            print("      → Change your deal sources to UK Amazon")
            print("   C) Continue using TXT fallback for ES products")
            print("      → PA-API validation disabled, but links work")
            
            return True
            
        else:
            print("\n⚠️ API responded but returned no data")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        if "forbidden" in str(e).lower():
            print("\nStill 403 Forbidden on UK marketplace too...")
        return False

if __name__ == "__main__":
    success = test_uk_marketplace()
    
    if not success:
        print("\n" + "=" * 70)
        print("ADDITIONAL TROUBLESHOOTING")
        print("=" * 70)
        print("\nSince 403 persists across all marketplaces:")
        print("\n1. ⏰ Wait 24-48 hours")
        print("   → New credentials can take time to activate")
        print("\n2. 🔗 Check credential-to-tag linking")
        print("   → In Amazon Associates, verify AKPAQ1JMQD1763062287")
        print("     is linked to tracking ID 'retroshell00-20'")
        print("\n3. 📧 Contact Amazon Associates Support")
        print("   → Provide Access Key and ask which marketplace it's for")
        print("\n4. ✅ Meanwhile, DealBot works with TXT fallback")
        print("   → No functionality lost, just no real-time validation")
