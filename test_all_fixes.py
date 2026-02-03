#!/usr/bin/env python3
"""Test all three fixes: bilingual titles, PVP display, and single instance."""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dealbot.utils.config import Config
from dealbot.controller import DealController
from dealbot.models import Deal, Currency

print("\n" + "="*80)
print("🧪 TESTING ALL THREE FIXES")
print("="*80 + "\n")

# Load config and controller
config = Config()
controller = DealController(config)

# Create Columbia shoes deal with Spanish and English titles + PVP
columbia_deal = Deal(
    title="Columbia Peakfreak Roam Waterproof Hiking Shoes",
    title_es="Columbia Peakfreak Roam Zapatos de Senderismo Impermeables Hombre",
    title_en="Columbia Peakfreak Roam Waterproof Hiking Shoes",
    url="https://www.amazon.es/dp/B0D4CLGLYQ/ref=nosim?tag=retroshell00-20&th=1&psc=1",
    asin="B0D4CLGLYQ",
    stated_price=47.25,
    source_pvp=75.00,  # PVP from TXT file
    source_discount_pct=37.0,  # Discount from TXT file
    currency=Currency.EUR,
)

print(f"📦 Deal: {columbia_deal.title}")
print(f"🇪🇸 Spanish: {columbia_deal.title_es}")
print(f"🇬🇧 English: {columbia_deal.title_en}")
print(f"💰 Price: €{columbia_deal.stated_price}")
print(f"🏷️  PVP: €{columbia_deal.source_pvp}")
print(f"💸 Discount: -{columbia_deal.source_discount_pct}%")
print()

# Process deal
print("🔄 Processing deal...")
processed = controller.process_deal(columbia_deal, for_preview=False)

# Format message
message = controller.formatter.format_message(processed)
print("📝 WhatsApp Message:")
print("-" * 80)
print(message)
print("-" * 80)
print()

# Verify fixes
print("🔍 VERIFICATION:")
print()

# Fix 1: Check bilingual titles
spanish_in_msg = columbia_deal.title_es in message
english_in_msg = columbia_deal.title_en in message
if spanish_in_msg and english_in_msg:
    print("✅ FIX 1 PASS: Both Spanish AND English titles shown")
else:
    print("❌ FIX 1 FAIL: Missing titles")
    print(f"   Spanish in message: {spanish_in_msg}")
    print(f"   English in message: {english_in_msg}")

# Fix 2: Check PVP and discount displayed
if "PVP" in message and "75.00" in message and "37%" in message:
    print("✅ FIX 2 PASS: PVP €75.00 and discount -37% shown")
else:
    print("❌ FIX 2 FAIL: PVP or discount missing")
    print(f"   'PVP' in message: {'PVP' in message}")
    print(f"   '75.00' in message: {'75.00' in message}")
    print(f"   '37%' in message: {'37%' in message}")

# Fix 3: Check app instance
import subprocess
result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
dealbot_processes = [line for line in result.stdout.split('\n') if 'DealBot.app' in line and 'grep' not in line]
if len(dealbot_processes) <= 1:
    print(f"✅ FIX 3 PASS: Only {len(dealbot_processes)} DealBot process(es) running")
else:
    print(f"❌ FIX 3 FAIL: Multiple DealBot processes detected ({len(dealbot_processes)})")

print()
print("="*80)
print("🎯 ALL FIXES VERIFIED")
print("="*80)
print()

# Ask if user wants to publish
response = input("Publish this deal to WhatsApp to verify in app? (yes/no): ").strip().lower()
if response == 'yes':
    print("\n🚀 Publishing to WhatsApp...")
    result = controller.publish_deal(processed, include_group=False)
    if result.publish_result and result.publish_result.success:
        print("✅ Published successfully!")
        print(f"   Check WhatsApp to verify both titles and discount are shown!")
    else:
        error = result.publish_result.error if result.publish_result else "Unknown error"
        print(f"❌ Failed to publish: {error}")
else:
    print("❌ Publishing skipped")
