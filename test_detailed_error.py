#!/usr/bin/env python3
"""Detailed PA-API error diagnostic."""

import os
from dotenv import load_dotenv
from amazon_paapi import AmazonApi

# Load environment
load_dotenv()

def test_detailed():
    """Test with detailed error information."""

    print("=" * 70)
    print("Amazon PA-API Detailed Diagnostic")
    print("=" * 70)

    # Get credentials
    access_key = os.getenv("AMAZON_PAAPI_ACCESS_KEY")
    secret_key = os.getenv("AMAZON_PAAPI_SECRET_KEY")
    tag = os.getenv("AMAZON_ASSOCIATE_TAG")

    print(f"\nCredentials from .env:")
    print(f"  Access Key: {access_key}")
    print(f"  Secret Key: {secret_key[:20]}...{secret_key[-4:]}")
    print(f"  Tag: {tag}")

    # Check format
    print(f"\nCredential Validation:")
    print(f"  Access Key length: {len(access_key)} (should be 20)")
    print(f"  Secret Key length: {len(secret_key)} (should be 40)")
    print(f"  Access Key format: {'✅ AKPA...' if access_key.startswith('AKPA') else '❌ Wrong prefix'}")

    # Test different marketplaces
    marketplaces = [
        ("US", "B08N5WRWNW"),
        ("UK", "B07VGRJDFY"),
        ("ES", "B06XGWGGD8"),
    ]

    for country, asin in marketplaces:
        print(f"\n{'=' * 70}")
        print(f"Testing {country} Marketplace")
        print('=' * 70)

        try:
            # Initialize API
            api = AmazonApi(
                key=access_key,
                secret=secret_key,
                tag=tag,
                country=country
            )

            print(f"API initialized for {country}")
            print(f"Endpoint: {getattr(api, 'region', 'Unknown')}")

            # Make request
            print(f"\nRequesting ASIN: {asin}")
            items = api.get_items([asin])

            if items and len(items) > 0:
                print(f"✅ SUCCESS for {country}!")
                item = items[0]
                if hasattr(item, 'item_info') and item.item_info.title:
                    print(f"Title: {item.item_info.title.display_value}")
                return True

        except Exception as e:
            error_msg = str(e)
            print(f"\n❌ Error: {error_msg}")

            # Detailed error analysis
            if "Forbidden" in error_msg or "403" in error_msg:
                print("\nCause: 403 Forbidden")
                print("Possible reasons:")
                print("  1. Tracking ID not linked to Access Key")
                print("  2. PA-API not enabled for this tracking ID")
                print("  3. Credentials too new (< 30 minutes old)")
                print("  4. Wrong marketplace (credentials may be US-only, etc.)")

            elif "Unauthorized" in error_msg or "401" in error_msg:
                print("\nCause: 401 Unauthorized")
                print("Possible reasons:")
                print("  1. Invalid Access Key or Secret Key")
                print("  2. Credentials have been deleted/revoked")
                print("  3. Signature mismatch")

            elif "SignatureDoesNotMatch" in error_msg:
                print("\nCause: Signature Mismatch")
                print("Possible reasons:")
                print("  1. Incorrect Secret Key")
                print("  2. Secret Key has spaces/newlines")
                print("  3. Encoding issue")

            elif "InvalidPartnerTag" in error_msg:
                print("\nCause: Invalid Partner Tag")
                print("Possible reasons:")
                print(f"  1. Tag '{tag}' doesn't exist")
                print("  2. Tag not approved for PA-API")
                print("  3. Tag for different marketplace")

    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print('=' * 70)
    print("\n❌ PA-API not working on any marketplace")
    print("\nMost likely issue: Tracking ID linkage")
    print("\nNext steps:")
    print("1. Go to Amazon Associates Central")
    print("2. Find your PA-API credentials page")
    print("3. Verify tracking IDs are linked to your Access Key")
    print("4. Wait 15-30 minutes after credential creation")
    print("5. Run this test again")

    return False

if __name__ == "__main__":
    success = test_detailed()
    exit(0 if success else 1)
