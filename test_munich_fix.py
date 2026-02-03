#!/usr/bin/env python3
"""Test Munich Sports bag with PVP and image fixes."""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dealbot.utils.config import Config
from dealbot.controller import DealController
from dealbot.models import Deal, Currency

print("\n" + "="*70)
print("🧪 TESTING MUNICH SPORTS BAG - PVP & IMAGE FIXES")
print("="*70 + "\n")

# Load config and controller
config = Config()
controller = DealController(config)

# Create Munich Sports bag deal with PVP data
munich_deal = Deal(
    title="Munich Sports Gym Sack, Sport Bags Unisex Adult, M",
    url="https://www.amazon.es/dp/B09CGWDZ35/ref=nosim?tag=retroshell00-20",
    asin="B09CGWDZ35",
    stated_price=7.02,
    source_pvp=12.00,  # Original price from TXT file
    source_discount_pct=42.0,  # Discount from TXT file
    currency=Currency.EUR,
)

print(f"📦 Deal: {munich_deal.title}")
print(f"💰 Price: €{munich_deal.stated_price}")
print(f"🏷️  PVP: €{munich_deal.source_pvp}")
print(f"💸 Discount: -{munich_deal.source_discount_pct}%")
print()

# Process in preview mode first
print("🔄 Processing deal (preview mode)...")
processed = controller.process_deal(munich_deal, for_preview=True)
print(f"✅ Processed: {processed.deal.title[:50]}")
print()

# Reprocess with full data for publishing
print("🔄 Reprocessing with shortlinks (publishing mode)...")
processed = controller.process_deal(munich_deal, for_preview=False)

# Format message
message = controller.formatter.format_message(processed)
print("📝 WhatsApp Message Preview:")
print("-" * 70)
print(message)
print("-" * 70)
print()

# Check if discount is shown
if "PVP" in message and "%" in message:
    print("✅ PASS: Discount and PVP are shown in message!")
else:
    print("❌ FAIL: Discount or PVP missing from message")
    print(f"   List price in price_info: {processed.price_info.list_price}")
    print(f"   Savings % in price_info: {processed.price_info.savings_percentage}")
    print(f"   Source PVP: {processed.deal.source_pvp}")
    print(f"   Source discount: {processed.deal.source_discount_pct}")

# Check image URL
image_url = processed.price_info.main_image_url
if not image_url and processed.deal.asin:
    fallback_urls = [
        f"https://m.media-amazon.com/images/I/{processed.deal.asin}.jpg",
        f"https://images-na.ssl-images-amazon.com/images/P/{processed.deal.asin}.jpg",
    ]
    image_url = fallback_urls[0]

print()
print(f"🖼️  Image URL: {image_url}")

# Test image URL
import requests
try:
    response = requests.head(image_url, timeout=5)
    if response.status_code == 200:
        print(f"✅ PASS: Image URL is accessible (HTTP {response.status_code})")
    else:
        print(f"⚠️  WARNING: Image URL returned HTTP {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Could not access image URL: {e}")

print()
print("="*70)
print("🎯 TEST COMPLETE")
print("="*70)
print()

# Ask if user wants to publish
response = input("Publish this deal to WhatsApp to verify? (yes/no): ").strip().lower()
if response == 'yes':
    print("\n🚀 Publishing to WhatsApp...")
    result = controller.publish_deal(processed, include_group=False)
    if result.publish_result and result.publish_result.success:
        print("✅ Published successfully!")
        print(f"   Message IDs: {result.publish_result.message_ids}")
    else:
        error = result.publish_result.error if result.publish_result else "Unknown error"
        print(f"❌ Failed to publish: {error}")
else:
    print("❌ Publishing cancelled")
