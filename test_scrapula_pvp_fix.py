#!/usr/bin/env python3
"""Test Scrapula PVP/discount extraction for deals missing TXT file data."""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dealbot.utils.config import Config
from dealbot.controller import DealController
from dealbot.models import Deal, Currency

print("\n" + "="*80)
print("🧪 TESTING SCRAPULA PVP/DISCOUNT EXTRACTION")
print("="*80 + "\n")

# Load config and controller
config = Config()
controller = DealController(config)

# Create Columbia backpack deal WITHOUT PVP/discount in TXT file
# (simulating a deal that has PVP on Amazon but not parsed from TXT)
backpack_deal = Deal(
    title="Columbia Echo Mountain 25L Unisex Backpack",
    title_es="Columbia Echo Mountain 25L Unisex Backpack",
    title_en="Columbia Echo Mountain 25L Unisex Backpack",
    url="https://www.amazon.es/dp/B0D4BWF1MZ/ref=nosim?tag=retroshell00-20&th=1&psc=1",
    asin="B0D4BWF1MZ",
    stated_price=35.70,
    source_pvp=None,  # ❌ NOT in TXT file
    source_discount_pct=None,  # ❌ NOT in TXT file
    currency=Currency.EUR,
)

print(f"📦 Deal: {backpack_deal.title}")
print(f"💰 Price: €{backpack_deal.stated_price}")
print(f"🏷️  PVP from TXT: {backpack_deal.source_pvp} (missing)")
print(f"💸 Discount from TXT: {backpack_deal.source_discount_pct} (missing)")
print()

print("🔍 SCENARIO: PA-API fails + TXT has no PVP + Scrapula should provide it")
print()

# Enrich with Scrapula BEFORE processing
print("🔄 Step 1: Enriching with Scrapula data...")
controller.enrich_deals_before_publish([backpack_deal])

if backpack_deal.asin in controller._scrapula_cache:
    scrapula_info = controller._scrapula_cache[backpack_deal.asin]
    if scrapula_info.success:
        print(f"✅ Scrapula extracted:")
        print(f"   - Image: {scrapula_info.image_url[:60] if scrapula_info.image_url else 'None'}...")
        print(f"   - Current Price: €{scrapula_info.current_price}")
        print(f"   - List Price (PVP): €{scrapula_info.list_price}")
        print(f"   - Rating: {scrapula_info.rating}")
    else:
        print(f"❌ Scrapula failed: {scrapula_info.error}")
else:
    print("❌ No Scrapula data in cache")

print()

# Process deal (will merge Scrapula PVP into price_info)
print("🔄 Step 2: Processing deal (merging Scrapula PVP)...")
processed = controller.process_deal(backpack_deal, for_preview=False)

print()
print("📋 PriceInfo after processing:")
print(f"   - Current Price: €{processed.price_info.current_price}")
print(f"   - List Price (PVP): €{processed.price_info.list_price}")
print(f"   - Savings %: {processed.price_info.savings_percentage}%")
print(f"   - Image URL: {processed.price_info.main_image_url[:60] if processed.price_info.main_image_url else 'None'}...")
print()

# Format message
message = controller.formatter.format_message(processed)
print("📝 WhatsApp Message:")
print("-" * 80)
print(message)
print("-" * 80)
print()

# Verify PVP and discount are shown
print("🔍 VERIFICATION:")
print()

has_pvp = processed.price_info.list_price and processed.price_info.list_price > processed.adjusted_price
has_discount = processed.price_info.savings_percentage and processed.price_info.savings_percentage > 0
pvp_in_msg = "PVP" in message and "€" in message
discount_in_msg = "%" in message

if has_pvp and has_discount:
    print(f"✅ PriceInfo has PVP (€{processed.price_info.list_price}) and discount ({processed.price_info.savings_percentage}%)")
else:
    print(f"❌ PriceInfo missing PVP or discount")
    print(f"   - has_pvp: {has_pvp}")
    print(f"   - has_discount: {has_discount}")

if pvp_in_msg and discount_in_msg:
    print(f"✅ WhatsApp message shows PVP and discount")
else:
    print(f"❌ WhatsApp message missing PVP or discount")
    print(f"   - 'PVP' in message: {pvp_in_msg}")
    print(f"   - '%' in message: {discount_in_msg}")

print()
print("="*80)
print("🎯 TEST COMPLETE")
print("="*80)
print()

if has_pvp and has_discount and pvp_in_msg and discount_in_msg:
    print("✅✅✅ ALL CHECKS PASSED - SCRAPULA PVP FIX WORKING! ✅✅✅")
else:
    print("❌ SOME CHECKS FAILED - REVIEW OUTPUT ABOVE")

print()
print("💡 This deal should now show PVP and discount in WhatsApp,")
print("   even though the TXT file didn't have this data.")
print("   Scrapula extracted it from the Amazon product page!")
