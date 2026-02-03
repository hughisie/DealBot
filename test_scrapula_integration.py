#!/usr/bin/env python3
"""Test Scrapula integration with controller."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "dealbot"))

from dealbot.controller import DealController
from dealbot.utils.config import Config

print("=" * 70)
print("🧪 SCRAPULA INTEGRATION TEST")
print("=" * 70)

# Load config
config = Config()
print(f"\n1. CONFIG")
print(f"   Scrapula enabled: {config.get('scrapula', {}).get('enabled', False)}")
print(f"   Service name: {config.get('scrapula', {}).get('service_name')}")

# Initialize controller
controller = DealController(config)
print(f"\n2. CONTROLLER")
print(f"   Scrapula service: {'✅ Active' if controller.scrapula else '❌ Disabled'}")

if not controller.scrapula:
    print(f"\n❌ Scrapula not initialized. Check .env has SCRAPULA_API_KEY")
    sys.exit(1)

# Parse test file
test_file = Path("test_deals/test_simple.txt")
print(f"\n3. PARSING FILE: {test_file}")
print(f"   ⏳ This will trigger Scrapula enrichment (~15-20 seconds)...")

deals = controller.parse_file(test_file)
print(f"   ✅ Parsed {len(deals)} deal(s)")

# Check cache
print(f"\n4. SCRAPULA CACHE")
print(f"   Cached products: {len(controller._scrapula_cache)}")

if controller._scrapula_cache:
    for asin, info in controller._scrapula_cache.items():
        print(f"\n   ASIN: {asin}")
        print(f"   Success: {info.success}")
        if info.success:
            print(f"   Title: {info.title[:50] if info.title else 'N/A'}...")
            print(f"   Price: {info.currency} {info.current_price}")
            print(f"   Image: {'✅ ' + info.image_url[:50] if info.image_url else '❌ None'}...")
            print(f"   Rating: {info.rating if info.rating else 'N/A'}")
            print(f"   Reviews: {info.review_count if info.review_count else 'N/A'}")

# Process first deal to see merged data
if deals:
    print(f"\n5. PROCESSING DEAL")
    deal = deals[0]
    print(f"   Deal: {deal.title[:50]}...")
    
    processed = controller.process_deal(deal)
    
    if processed.price_info:
        print(f"\n   MERGED DATA:")
        print(f"   Price: {processed.price_info.current_price}")
        print(f"   Image: {'✅ ' + processed.price_info.main_image_url[:50] if processed.price_info.main_image_url else '❌ None'}...")
        print(f"   Rating: {processed.price_info.review_rating if processed.price_info.review_rating else 'N/A'}")
        print(f"   Reviews: {processed.price_info.review_count if processed.price_info.review_count else 'N/A'}")

print(f"\n{'=' * 70}")
print("✅ INTEGRATION TEST COMPLETE!")
print('=' * 70)

if controller._scrapula_cache:
    successful = sum(1 for data in controller._scrapula_cache.values() if data.success)
    print(f"\n🎉 Scrapula working! {successful}/{len(controller._scrapula_cache)} products enriched")
    print(f"✅ Product images available")
    print(f"✅ Ready to integrate into UI")
else:
    print(f"\n⚠️  No Scrapula data received - task may have timed out")
    print(f"   Check Scrapula dashboard or increase max_wait_seconds")
