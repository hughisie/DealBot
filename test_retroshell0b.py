#!/usr/bin/env python3
"""Test with retroshell0b-21 tracking ID."""

from amazon_paapi import AmazonApi

def test_tracking_id():
    """Test retroshell0b-21 tracking ID."""

    print("=" * 70)
    print("Testing Tracking ID: retroshell0b-21")
    print("=" * 70)

    access_key = "AKPA0DQU0S1763063154"
    secret_key = "8M+aK0sKmYBjxfQk2HL6KdEKuiJtX13xpQiNuDWL"
    tag = "retroshell0b-21"  # Different tracking ID

    print(f"\nConfiguration:")
    print(f"  Access Key: {access_key}")
    print(f"  Tracking ID: {tag}")

    # Test all marketplaces
    tests = [
        ("US", "B08N5WRWNW", "United States"),
        ("UK", "B07VGRJDFY", "United Kingdom"),
        ("ES", "B06XGWGGD8", "Spain"),
    ]

    for country, asin, name in tests:
        print(f"\n{'=' * 70}")
        print(f"Testing: {name} ({country})")
        print(f"ASIN: {asin}")
        print('=' * 70)

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

                print(f"\n🎉 SUCCESS!")
                print(f"Title: {title[:60]}...")

                # Get price
                if hasattr(item, "offers") and item.offers and item.offers.listings:
                    listing = item.offers.listings[0]
                    if hasattr(listing, "price") and listing.price:
                        print(f"Price: {listing.price.display_amount}")

                print(f"\n{'=' * 70}")
                print(f"✅ PA-API IS WORKING WITH {tag}!")
                print('=' * 70)
                print(f"\nWorking Configuration:")
                print(f"  Access Key: {access_key}")
                print(f"  Tracking ID: {tag}")
                print(f"  Marketplace: {country} ({name})")
                print(f"\nUpdate your .env file with:")
                print(f"  AMAZON_ASSOCIATE_TAG={tag}")
                print(f"\nThen rebuild:")
                print(f"  ./rebuild_app.sh")
                return True
            else:
                print(f"⚠️  Empty response")

        except Exception as e:
            error_str = str(e)
            if "Forbidden" in error_str or "403" in error_str:
                print(f"❌ 403 Forbidden")
            elif "Unauthorized" in error_str or "401" in error_str:
                print(f"❌ 401 Unauthorized")
            elif "InvalidPartnerTag" in error_str:
                print(f"❌ Invalid Partner Tag")
                print(f"   '{tag}' may not exist or not be approved")
            elif "SignatureDoesNotMatch" in error_str:
                print(f"❌ Signature Mismatch")
            else:
                print(f"❌ Error: {error_str[:80]}")

    print(f"\n{'=' * 70}")
    print("RESULT")
    print('=' * 70)
    print(f"\n❌ Tracking ID '{tag}' not working with current credentials")
    print(f"\nPossible reasons:")
    print(f"1. '{tag}' is not linked to Access Key {access_key}")
    print(f"2. '{tag}' is not approved for PA-API")
    print(f"3. Credentials still propagating (wait 15-30 minutes)")
    print(f"\nNote: Same Access Key, different tracking ID still gets 403")
    print(f"This confirms the issue is tracking ID linkage, not credentials")
    return False

if __name__ == "__main__":
    success = test_tracking_id()
    exit(0 if success else 1)
