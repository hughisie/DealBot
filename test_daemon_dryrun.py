#!/usr/bin/env python3
"""
Dry-run test of the daemon - shows what would happen without publishing.
"""

from pathlib import Path
from dealbot.daemon import DealBotDaemon, DealFilter
from dealbot.utils.config import Config
from dealbot.utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

def main():
    print("=" * 70)
    print("🧪 DealBot Daemon - DRY RUN TEST")
    print("=" * 70)
    print()

    # Initialize
    config = Config()
    daemon = DealBotDaemon(config)
    filter_obj = DealFilter(config)

    # Test file
    test_file = Path('/Users/m4owen/Library/CloudStorage/GoogleDrive-gunn0r@gmail.com/Shared drives/01.Player Clothing Team Drive/02. RetroShell/13. Articles and Data/09. Feed Finder/amazon_deals/2025-11/18/Tue 18th/2025-11-18_1602_evening_whatsapp.txt')

    if not test_file.exists():
        print("❌ Test file not found")
        return

    # Parse deals
    print(f"📄 Parsing: {test_file.name}")
    deals = daemon.controller.parse_file(test_file)
    print(f"   Found {len(deals)} deals\n")

    # Process first 5 deals as example
    print("🔍 Processing Sample Deals (first 5):")
    print("-" * 70)

    would_publish = 0
    would_filter = 0

    for i, deal in enumerate(deals[:5], 1):
        try:
            print(f"\n{i}. {deal.title[:55]}...")
            print(f"   ASIN: {deal.asin}")
            print(f"   TXT Price: €{deal.stated_price}")
            if deal.source_discount_pct:
                print(f"   TXT Discount: -{deal.source_discount_pct}%")

            # Process deal (this validates with PA-API)
            print(f"   ⏳ Validating with Amazon PA-API...")
            processed = daemon.controller.process_deal(deal, for_preview=False)

            if processed.price_info:
                actual_price = processed.price_info.current_price
                actual_discount = processed.price_info.savings_percentage
                availability = processed.price_info.availability

                print(f"   💰 Actual Price: €{actual_price}")
                if actual_discount:
                    print(f"   📊 Actual Discount: -{actual_discount}%")
                print(f"   📦 Availability: {availability or 'In Stock'}")

                # Apply filter
                should_publish, reason = filter_obj.should_publish(deal, processed)

                if should_publish:
                    print(f"   ✅ WOULD PUBLISH: {reason}")
                    would_publish += 1
                else:
                    print(f"   ❌ WOULD FILTER: {reason}")
                    would_filter += 1
            else:
                print(f"   ❌ WOULD FILTER: No price info available")
                would_filter += 1

        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            would_filter += 1

    print("\n" + "=" * 70)
    print("📊 Summary (first 5 deals):")
    print(f"   ✅ Would Publish: {would_publish}")
    print(f"   ❌ Would Filter: {would_filter}")
    print("=" * 70)
    print()
    print("💡 This was a DRY RUN - nothing was published to WhatsApp")
    print("   To run for real: python run_daemon.py --once")
    print()

if __name__ == "__main__":
    main()
