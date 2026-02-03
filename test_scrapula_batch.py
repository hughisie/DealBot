#!/usr/bin/env python3
"""Test Scrapula batch workflow."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.services.scrapula import ScrapulaService

def test_scrapula_batch():
    """Test Scrapula batch workflow with multiple ASINs."""
    
    print("=" * 70)
    print("Scrapula Batch Workflow Test")
    print("=" * 70)
    
    api_key = "ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA"
    
    # Test ASINs from your TXT file
    test_asins = [
        "B06XGWGGD8",  # Helly Hansen jacket
        "B08N5WRWNW",  # Another product
    ]
    
    print(f"\nTest ASINs: {', '.join(test_asins)}")
    print(f"Marketplace: amazon.es")
    print(f"\nThis will:")
    print(f"  1. Create Scrapula task")
    print(f"  2. Wait for completion (up to 5 minutes)")
    print(f"  3. Download and parse results")
    print(f"  4. Display product data")
    
    # Try the service name provided by user
    service_names = [
        "amazon_products_service_v2",  # User-provided service name
        "amazon_product_service",
        "amazon_scraper_service",
        "amazon_search_service",
    ]
    
    for service_name in service_names:
        print(f"\n{'=' * 70}")
        print(f"Trying service: {service_name}")
        print('=' * 70)
        
        service = ScrapulaService(api_key, service_name=service_name)
        
        print(f"\nCreating batch task...")
        results = service.get_batch_product_data(
            asins=test_asins,
            marketplace="es",
            max_wait_seconds=300  # 5 minutes
        )
        
        # Check if any succeeded
        success_count = sum(1 for r in results.values() if r.success)
        
        if success_count > 0:
            print(f"\n🎉 SUCCESS with service: {service_name}")
            print(f"\nResults:")
            for asin, product in results.items():
                print(f"\n  ASIN: {asin}")
                if product.success:
                    print(f"    ✅ Title: {product.title[:50] if product.title else 'N/A'}...")
                    print(f"    ✅ Price: {product.currency} {product.current_price}")
                    if product.list_price:
                        print(f"    ✅ List Price: {product.currency} {product.list_price}")
                    print(f"    ✅ Image: {product.image_url[:50] if product.image_url else 'N/A'}...")
                else:
                    print(f"    ❌ Error: {product.error}")
            
            return True
        else:
            print(f"\n❌ Failed with service: {service_name}")
            for asin, product in results.items():
                if product.error:
                    print(f"    {asin}: {product.error}")
    
    print(f"\n{'=' * 70}")
    print("No working service found")
    print('=' * 70)
    print(f"\n📋 Next Step:")
    print(f"  Check Scrapula dashboard for the correct Amazon service name")
    print(f"  Or contact Scrapula support to ask for Amazon product scraping service")
    
    return False

if __name__ == "__main__":
    print("\n⏱️  Note: This test may take 1-5 minutes per service name")
    print("     Scrapula processes tasks asynchronously\n")
    
    success = test_scrapula_batch()
    
    if success:
        print(f"\n{'=' * 70}")
        print("✅ READY TO INTEGRATE!")
        print('=' * 70)
        print(f"\nNext: Integrate into DealBot controller")
    else:
        print(f"\n{'=' * 70}")
        print("Need Service Name")
        print('=' * 70)
        print(f"\nCheck your Scrapula dashboard for Amazon service name")
