#!/usr/bin/env python3
"""Quick Scrapula integration test."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.services.scrapula import ScrapulaService

api_key = "ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA"
service = ScrapulaService(api_key, service_name="amazon_products_service_v2")

print("Testing Scrapula with amazon_products_service_v2...")
print("ASIN: B06XGWGGD8 (Helly Hansen jacket)")
print("\nCreating task and waiting up to 5 minutes...\n")

result = service.get_product_data("B06XGWGGD8", marketplace="es")

print("=" * 70)
if result.success:
    print("✅ SUCCESS!")
    print(f"  Title: {result.title[:60] if result.title else 'N/A'}...")
    print(f"  Price: {result.currency} {result.current_price}")
    print(f"  Image: {result.image_url[:50] if result.image_url else 'N/A'}...")
    print("\n✅ Scrapula integration WORKING!")
else:
    print("❌ FAILED")
    print(f"  Error: {result.error}")
print("=" * 70)
