#!/usr/bin/env python3
"""Quick integration test with real TXT file."""
import sys
from pathlib import Path

# Test with dealbot folder
sys.path.insert(0, str(Path.cwd() / "dealbot"))

from dealbot.controller import DealController
from dealbot.utils.config import Config

print("=" * 70)
print("SCRAPULA INTEGRATION TEST")
print("=" * 70)

# Load config
config = Config()
print(f"\n✅ Config loaded")
print(f"   Scrapula enabled: {config.get('scrapula', {}).get('enabled', False)}")

# Initialize controller
controller = DealController(config)
print(f"✅ Controller initialized")
print(f"   Scrapula service: {'Active' if controller.scrapula else 'Disabled'}")

# Find a test TXT file
test_dir = Path(config.default_source_dir)
txt_files = list(test_dir.glob("*.txt"))

if not txt_files:
    print(f"\n❌ No TXT files found in: {test_dir}")
    sys.exit(1)

test_file = txt_files[0]
print(f"\n📄 Testing with: {test_file.name}")

# Parse file (this will trigger Scrapula enrichment)
print(f"\n⏳ Parsing file and enriching with Scrapula...")
deals = controller.parse_file(test_file)

print(f"\n✅ Parsed {len(deals)} deals")

# Check first few deals for Scrapula data
print(f"\n{'=' * 70}")
print("SAMPLE ENRICHED DEALS:")
print('=' * 70)

for i, deal in enumerate(deals[:3], 1):
    print(f"\nDeal {i}: {deal.title[:50]}...")
    print(f"  ASIN: {deal.asin}")
    
    # Process the deal to see if Scrapula data is merged
    processed = controller.process_deal(deal)
    
    if processed.price_info:
        print(f"  Price: {processed.price_info.currency} {processed.price_info.current_price}")
        if processed.price_info.main_image_url:
            print(f"  ✅ Image: {processed.price_info.main_image_url[:60]}...")
        else:
            print(f"  ❌ No image")
        
        if processed.price_info.review_rating:
            print(f"  ✅ Rating: {processed.price_info.review_rating} ⭐")
        else:
            print(f"  ❌ No rating")

print(f"\n{'=' * 70}")
print("INTEGRATION TEST COMPLETE!")
print('=' * 70)

if controller.scrapula:
    cache_size = len(controller._scrapula_cache)
    print(f"\n✅ Scrapula cache: {cache_size} products")
    if cache_size > 0:
        successful = sum(1 for data in controller._scrapula_cache.values() if data.success)
        print(f"✅ Success rate: {successful}/{cache_size}")
        print(f"\n🎉 Scrapula integration working!")
    else:
        print(f"\n⚠️  Scrapula cache empty - check if task completed")
else:
    print(f"\n❌ Scrapula not enabled")

