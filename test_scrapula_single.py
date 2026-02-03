#!/usr/bin/env python3
"""Quick test of Scrapula API with user-provided service name."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.services.scrapula import ScrapulaService

def test_service():
    """Test Scrapula with the correct service name."""
    
    print("=" * 70)
    print("Scrapula API Test - amazon_products_service_v2")
    print("=" * 70)
    
    api_key = "ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA"
    service_name = "amazon_products_service_v2"  # User-provided
    
    # Single ASIN test
    test_asin = "B06XGWGGD8"  # Helly Hansen jacket
    
    print(f"\nTesting single ASIN: {test_asin}")
    print(f"Service: {service_name}")
    print(f"Marketplace: amazon.es")
    print(f"\nThis will:")
    print(f"  1. Create Scrapula task")
    print(f"  2. Wait for completion (1-5 minutes)")
    print(f"  3. Parse and display results")
    print(f"\n⏱️  Please wait...")
    
    service = ScrapulaService(api_key, service_name=service_name)
    
    # Test single product
    result = service.get_product_data(asin=test_asin, marketplace="es")
    
    print(f"\n{'=' * 70}")
    print("RESULT:")
    print('=' * 70)
    
    if result.success:
        print(f"\n🎉 SUCCESS!")
        print(f"\n  ASIN: {result.asin}")
        print(f"  Title: {result.title[:60] if result.title else 'N/A'}...")
        print(f"  Price: {result.currency} {result.current_price}")
        if result.list_price:
            print(f"  List Price: {result.currency} {result.list_price}")
            discount = ((result.list_price - result.current_price) / result.list_price) * 100
            print(f"  Discount: {discount:.1f}%")
        print(f"  Availability: {result.availability}")
        if result.rating:
            print(f"  Rating: {result.rating} ⭐")
        if result.review_count:
            print(f"  Reviews: {result.review_count:,}")
        if result.image_url:
            print(f"  Image: {result.image_url[:60]}...")
        
        print(f"\n✅ Scrapula integration working!")
        print(f"✅ Ready to integrate into DealBot!")
        return True
    else:
        print(f"\n❌ FAILED")
        print(f"  Error: {result.error}")
        
        if "Failed to create Scrapula task" in result.error:
            print(f"\n💡 Troubleshooting:")
            print(f"  1. Verify API key is correct")
            print(f"  2. Check if service name 'amazon_products_service_v2' exists")
            print(f"  3. Ensure you have credits/balance in Scrapula account")
            print(f"  4. Try accessing Scrapula dashboard to verify")
        
        return False

if __name__ == "__main__":
    print("\n⚠️  This test will take 1-5 minutes to complete")
    print("   Scrapula processes requests asynchronously\n")
    
    input("Press ENTER to start test...")
    
    success = test_service()
    
    if success:
        print(f"\n{'=' * 70}")
        print("✅ INTEGRATION READY!")
        print('=' * 70)
        print(f"\nNext steps:")
        print(f"  1. Integrate into DealBot controller")
        print(f"  2. Add batch processing for TXT files")
        print(f"  3. Update UI to show product images")
        print(f"  4. Deploy!")
    else:
        print(f"\n{'=' * 70}")
        print("⚠️  Check Scrapula Dashboard")
        print('=' * 70)
        print(f"\nPlease verify:")
        print(f"  • Service name: amazon_products_service_v2")
        print(f"  • API key is valid")
        print(f"  • Account has credits")
