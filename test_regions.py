#!/usr/bin/env python3
"""Test PA-API with different Amazon regional endpoints."""

from amazon_paapi import AmazonApi
import os
from dotenv import load_dotenv

load_dotenv()

def test_all_regions():
    """Test all Amazon regional endpoints."""

    print("=" * 70)
    print("Testing PA-API Across All Amazon Regions")
    print("=" * 70)

    access_key = os.getenv("AMAZON_PAAPI_ACCESS_KEY")
    secret_key = os.getenv("AMAZON_PAAPI_SECRET_KEY")

    # Test all your tracking IDs
    tracking_ids = [
        "retroshell00-20",
        "amazoneschollos-20",
    ]

    # All Amazon marketplaces
    marketplaces = [
        ("US", "B08N5WRWNW", "United States - amazon.com"),
        ("UK", "B07VGRJDFY", "United Kingdom - amazon.co.uk"),
        ("ES", "B06XGWGGD8", "Spain - amazon.es"),
        ("DE", "B0819KW3H1", "Germany - amazon.de"),
        ("FR", "B07YNK87NZ", "France - amazon.fr"),
        ("IT", "B08C4QY7N4", "Italy - amazon.it"),
        ("CA", "B08L5VFJ4M", "Canada - amazon.ca"),
        ("JP", "B08HN37YZL", "Japan - amazon.co.jp"),
        ("AU", "B08F2DR3BG", "Australia - amazon.com.au"),
        ("BR", "B08DFPBL64", "Brazil - amazon.com.br"),
    ]

    print(f"\nCredentials:")
    print(f"  Access Key: {access_key}")
    print(f"  Testing {len(tracking_ids)} tracking IDs across {len(marketplaces)} marketplaces")

    # Test each combination
    for tag in tracking_ids:
        print(f"\n{'=' * 70}")
        print(f"TRACKING ID: {tag}")
        print('=' * 70)

        for country, asin, description in marketplaces:
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

                    print(f"\n🎉 SUCCESS! {description}")
                    print(f"   ASIN: {asin}")
                    print(f"   Title: {title[:50]}...")

                    if hasattr(item, "offers") and item.offers and item.offers.listings:
                        listing = item.offers.listings[0]
                        if hasattr(listing, "price") and listing.price:
                            print(f"   Price: {listing.price.display_amount}")

                    print(f"\n{'=' * 70}")
                    print(f"✅ WORKING CONFIGURATION FOUND!")
                    print('=' * 70)
                    print(f"\nWorking settings:")
                    print(f"  Marketplace: {country} ({description})")
                    print(f"  Tracking ID: {tag}")
                    print(f"  Access Key: {access_key}")
                    print(f"\nUpdate .env:")
                    print(f"  AMAZON_ASSOCIATE_TAG={tag}")
                    print(f"\nYour credentials are registered for the {country} marketplace!")
                    return True, country, tag
                else:
                    print(f"  {description}: ⚠️  Empty response")

            except Exception as e:
                error_str = str(e)
                if "Forbidden" in error_str or "403" in error_str:
                    status = "❌ 403 Forbidden"
                elif "Unauthorized" in error_str or "401" in error_str:
                    status = "❌ 401 Unauthorized"
                elif "InvalidPartnerTag" in error_str:
                    status = "❌ Invalid Tag"
                else:
                    status = f"❌ {error_str[:30]}..."

                print(f"  {description}: {status}")

    print(f"\n{'=' * 70}")
    print("RESULTS")
    print('=' * 70)
    print("\n❌ No working marketplace found")
    print("\nAll marketplaces returning 403 Forbidden indicates:")
    print("1. Credentials are too new (< 30 minutes)")
    print("2. Tracking IDs not yet linked to Access Key")
    print("3. Need to wait for Amazon to activate")
    print("\nRecommendation:")
    print("  Wait 15-30 minutes and run this test again")
    return False, None, None

if __name__ == "__main__":
    success, marketplace, tag = test_all_regions()
    exit(0 if success else 1)
