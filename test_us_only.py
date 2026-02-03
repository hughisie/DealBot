#!/usr/bin/env python3
"""Test US marketplace only with retroshell00-20."""

from amazon_paapi import AmazonApi

def test_us_marketplace():
    """Test US marketplace specifically."""

    print("=" * 70)
    print("Testing US Marketplace with retroshell00-20")
    print("=" * 70)

    access_key = "AKPA0DQU0S1763063154"
    secret_key = "8M+aK0sKmYBjxfQk2HL6KdEKuiJtX13xpQiNuDWL"
    tag = "retroshell00-20"  # Your primary store ID

    print(f"\nConfiguration:")
    print(f"  Access Key: {access_key}")
    print(f"  Tracking ID: {tag}")
    print(f"  Marketplace: US (amazon.com)")

    # US test ASINs
    test_asins = [
        ("B08N5WRWNW", "Popular US Product 1"),
        ("B0D1XD1ZV3", "Popular US Product 2"),
        ("B0BSHF7WHW", "Popular US Product 3"),
    ]

    for asin, description in test_asins:
        print(f"\n{'=' * 70}")
        print(f"Testing: {description}")
        print(f"ASIN: {asin}")
        print('=' * 70)

        try:
            api = AmazonApi(
                key=access_key,
                secret=secret_key,
                tag=tag,
                country="US"
            )

            items = api.get_items([asin])

            if items and len(items) > 0:
                item = items[0]
                title = item.item_info.title.display_value if item.item_info.title else "N/A"

                print(f"✅ SUCCESS!")
                print(f"Title: {title}")

                # Get price
                if hasattr(item, "offers") and item.offers and item.offers.listings:
                    listing = item.offers.listings[0]
                    if hasattr(listing, "price") and listing.price:
                        print(f"Price: {listing.price.display_amount}")

                print(f"\n{'=' * 70}")
                print(f"🎉 PA-API IS WORKING!")
                print('=' * 70)
                print(f"\nYour .env is already configured correctly!")
                print(f"\nNote: You can only use US marketplace (amazon.com)")
                print(f"Your Associates account appears to be US-based.")
                return True
            else:
                print(f"⚠️  Empty response")

        except Exception as e:
            error_str = str(e)
            if "Forbidden" in error_str or "403" in error_str:
                print(f"❌ 403 Forbidden - Credentials still propagating...")
                print(f"   Created at: Thu Nov 13 19:45:54 UTC 2025")
                print(f"   Wait time: Typically 5-30 minutes")
            elif "InvalidPartnerTag" in error_str:
                print(f"❌ Invalid Partner Tag - {tag} not authorized for PA-API")
            elif "SignatureDoesNotMatch" in error_str:
                print(f"❌ Invalid Secret Key")
            else:
                print(f"❌ Error: {error_str}")

    print(f"\n{'=' * 70}")
    print("Results: Not working yet")
    print('=' * 70)
    print("\nNext steps:")
    print("1. Wait 10-15 more minutes (credentials are very new)")
    print("2. Run this test again:")
    print("   ./venv/bin/python3 test_us_only.py")
    print("\n3. Or run continuous monitoring:")
    print("   ./wait_and_retry.sh")
    return False

if __name__ == "__main__":
    test_us_marketplace()
