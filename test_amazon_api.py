#!/usr/bin/env python3
"""Test Amazon PA-API to diagnose stock availability issues."""

import sys
import os
from pathlib import Path

# Add dealbot to path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.utils.config import Config
from dealbot.services.amazon_paapi import AmazonPAAPIService
from dealbot.models import Currency

def test_api():
    """Test Amazon PA-API with a known ASIN."""
    print("=" * 70)
    print("Testing Amazon Product Advertising API")
    print("=" * 70)
    
    try:
        # Initialize config
        print("\n1. Loading configuration...")
        config = Config()
        print("   ✅ Config loaded")
        
        # Initialize PA-API service
        print("\n2. Initializing Amazon PA-API service...")
        try:
            api_service = AmazonPAAPIService(config)
            print("   ✅ Service initialized")
        except Exception as e:
            print(f"   ❌ Failed to initialize: {e}")
            print("\n⚠️  API credentials may not be configured correctly!")
            print("   Check that .env contains:")
            print("   - AMAZON_PAAPI_ACCESS_KEY")
            print("   - AMAZON_PAAPI_SECRET_KEY")
            return
        
        # Test with a known ASIN from the file
        test_asin = "B06XGWGGD8"  # Helly Hansen jacket from the file
        test_price = 63.14
        
        print(f"\n3. Testing with ASIN: {test_asin}")
        print(f"   Expected price: €{test_price}")
        
        # Call PA-API
        print("\n4. Calling Amazon PA-API...")
        price_info = api_service.validate_price(
            asin=test_asin,
            currency=Currency.EUR,
            stated_price=test_price
        )
        
        # Display results
        print("\n" + "=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"ASIN: {price_info.asin}")
        print(f"Title: {price_info.title}")
        print(f"Current Price: €{price_info.current_price}" if price_info.current_price else "Current Price: N/A")
        print(f"List Price (PVP): €{price_info.list_price}" if price_info.list_price else "List Price: N/A")
        print(f"Discount: -{price_info.savings_percentage:.0f}%" if price_info.savings_percentage else "Discount: N/A")
        print(f"Availability: {price_info.availability or 'Unknown'}")
        print(f"Rating: ⭐{price_info.review_rating:.1f}" if price_info.review_rating else "Rating: N/A")
        print(f"Reviews: {price_info.review_count}" if price_info.review_count else "Reviews: N/A")
        print(f"Needs Review: {price_info.needs_review}")
        
        # Diagnosis
        print("\n" + "=" * 70)
        print("DIAGNOSIS")
        print("=" * 70)
        
        if not price_info.current_price:
            print("❌ NO PRICE DATA RETURNED")
            print("   This explains why all items show 'Out of Stock'")
            print("\n   Possible causes:")
            print("   1. API credentials are invalid or expired")
            print("   2. API request limit exceeded")
            print("   3. Product is not available in ES marketplace")
            print("   4. PA-API is not returning offer data")
        elif price_info.availability != "Now":
            print(f"⚠️  AVAILABILITY ISSUE: {price_info.availability}")
            print("   Product has price but availability is not 'Now'")
        else:
            print("✅ API IS WORKING CORRECTLY")
            print(f"   Product is in stock with price €{price_info.current_price}")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
