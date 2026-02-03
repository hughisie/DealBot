#!/usr/bin/env python3
"""Test Amazon HTML scraping for PVP/discount."""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dealbot.utils.config import Config
from dealbot.controller import DealController
from dealbot.models import Deal, Currency

print("\n" + "="*80)
print("🧪 TESTING AMAZON HTML SCRAPING FOR PVP/DISCOUNT")
print("="*80 + "\n")

# Load config and controller
config = Config()
controller = DealController(config)

# Create backpack deal WITHOUT PVP from TXT
backpack_deal = Deal(
    title="Columbia Echo Mountain 25L Unisex Backpack",
    title_es="Columbia Echo Mountain 25L Unisex Backpack",
    title_en="Columbia Echo Mountain 25L Unisex Backpack",
    url="https://www.amazon.es/dp/B0D4BWF1MZ/ref=nosim?tag=retroshell00-20&th=1&psc=1",
    asin="B0D4BWF1MZ",
    stated_price=35.70,
    source_pvp=None,  # Missing from TXT
    source_discount_pct=None,  # Missing from TXT
    currency=Currency.EUR,
)

print(f"📦 Deal: {backpack_deal.title}")
print(f"💰 Price: €{backpack_deal.stated_price}")
print(f"❌ PVP from TXT: None")
print(f"❌ Discount from TXT: None")
print()

print("🔄 Processing deal (will scrape Amazon page for PVP)...")
processed = controller.process_deal(backpack_deal, for_preview=False)

print()
print("📋 After Processing:")
print(f"   Current Price: €{processed.price_info.current_price}")
print(f"   List Price (PVP): €{processed.price_info.list_price}")
print(f"   Savings %: {processed.price_info.savings_percentage}%")
print()

# Now publish (this is where Amazon scraping happens)
print("🚀 Publishing (Amazon page scraping happens here)...")
result = controller.publish_deal(processed, include_group=False)

print()
print("📋 After Publishing:")
print(f"   Current Price: €{processed.price_info.current_price}")
print(f"   List Price (PVP): €{processed.price_info.list_price}")
print(f"   Savings %: {processed.price_info.savings_percentage}%")
print()

# Format final message
message = controller.formatter.format_message(processed)
print("📝 Final WhatsApp Message:")
print("-" * 80)
print(message)
print("-" * 80)
print()

# Verify
has_pvp = processed.price_info.list_price and processed.price_info.list_price > processed.adjusted_price
has_discount = processed.price_info.savings_percentage and processed.price_info.savings_percentage > 0
pvp_in_msg = "PVP" in message
discount_in_msg = "%" in message

print("🔍 VERIFICATION:")
if has_pvp and has_discount:
    print(f"✅ PriceInfo has PVP (€{processed.price_info.list_price}) and discount ({processed.price_info.savings_percentage}%)")
else:
    print(f"❌ PriceInfo missing PVP or discount")

if pvp_in_msg and discount_in_msg:
    print(f"✅ WhatsApp message shows 'PVP' and '%'")
else:
    print(f"❌ WhatsApp message missing PVP or discount indicators")

if result.publish_result and result.publish_result.success:
    print(f"✅ Published successfully to WhatsApp!")
else:
    print(f"❌ Publishing failed")

print()
if has_pvp and has_discount and pvp_in_msg and discount_in_msg:
    print("="*80)
    print("✅✅✅ SUCCESS - AMAZON SCRAPING EXTRACTED PVP/DISCOUNT! ✅✅✅")
    print("="*80)
else:
    print("❌ Test incomplete - check logs above")
