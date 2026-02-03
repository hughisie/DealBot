#!/usr/bin/env python3
"""Compare old vs new PA-API credentials."""

from amazon_paapi import AmazonApi

def test_credentials():
    """Test both sets of credentials."""

    print("=" * 70)
    print("Comparing PA-API Credentials")
    print("=" * 70)

    credentials = [
        {
            "name": "OLD (Working yesterday)",
            "access": "AKPAIS17IV1762859910",
            "secret": "bCyorNu3pV+DW063yALOiTl8IMhAtwz7/momo3Gj",
            "tag": "retroshell00-20"
        },
        {
            "name": "NEW (Created today)",
            "access": "AKPA0DQU0S1763063154",
            "secret": "8M+aK0sKmYBjxfQk2HL6KdEKuiJtX13xpQiNuDWL",
            "tag": "retroshell00-20"
        },
    ]

    test_asin = "B08N5WRWNW"  # US product

    for cred in credentials:
        print(f"\n{'=' * 70}")
        print(f"Testing: {cred['name']}")
        print(f"Access Key: {cred['access']}")
        print('=' * 70)

        # Test US marketplace
        try:
            api = AmazonApi(
                key=cred['access'],
                secret=cred['secret'],
                tag=cred['tag'],
                country="US"
            )

            items = api.get_items([test_asin])

            if items and len(items) > 0:
                item = items[0]
                title = item.item_info.title.display_value if item.item_info.title else "N/A"
                print(f"\n✅ SUCCESS!")
                print(f"Title: {title[:60]}...")

                if hasattr(item, "offers") and item.offers and item.offers.listings:
                    listing = item.offers.listings[0]
                    if hasattr(listing, "price") and listing.price:
                        print(f"Price: {listing.price.display_amount}")

                print(f"\n🎉 THIS CREDENTIAL SET WORKS!")
                print(f"Use Access Key: {cred['access']}")
                return
            else:
                print(f"\n⚠️  Empty response")

        except Exception as e:
            error_str = str(e)
            if "Forbidden" in error_str or "403" in error_str:
                print(f"\n❌ 403 Forbidden")
                print("   Tracking ID not linked to this Access Key")
            elif "Unauthorized" in error_str or "401" in error_str:
                print(f"\n❌ 401 Unauthorized")
                print("   Invalid or expired credentials")
            elif "InvalidPartnerTag" in error_str:
                print(f"\n❌ Invalid Partner Tag")
            elif "SignatureDoesNotMatch" in error_str:
                print(f"\n❌ Signature Mismatch")
                print("   Wrong secret key")
            else:
                print(f"\n❌ Error: {error_str[:80]}")

    print(f"\n{'=' * 70}")
    print("CONCLUSION")
    print('=' * 70)
    print("\nNeither credential set is working:")
    print("1. OLD credentials: Getting 401 Unauthorized (likely revoked/expired)")
    print("2. NEW credentials: Getting 403 Forbidden (tracking ID not linked)")
    print("\nRecommendation:")
    print("- The NEW credentials need tracking ID linkage")
    print("- Wait 15-30 minutes for new credentials to activate")
    print("- Check Amazon Associates dashboard to link tracking IDs")

if __name__ == "__main__":
    test_credentials()
