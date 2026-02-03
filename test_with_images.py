#!/usr/bin/env python
"""Test publishing with images, PVP, discount, and ratings."""

import sys
from adp.controller import DealController
from adp.utils.config import Config

def main():
    config = Config()
    controller = DealController(config)
    
    print("📂 Parsing test file...")
    deals = controller.parse_file('TEST 2025-11-10_1602_evening_whatsapp TEST.txt')
    print(f"✅ Found {len(deals)} deals\n")
    
    if not deals:
        print("❌ No deals found")
        return 1
    
    # Test with first deal only
    deal = deals[0]
    print(f"📦 Processing: {deal.title[:60]}...")
    print(f"   ASIN: {deal.asin}")
    print(f"   Stated Price: €{deal.stated_price}")
    
    try:
        # Process the deal
        processed = controller.process_deal(deal)
        
        print(f"\n✅ Deal Processed:")
        print(f"   💰 Current Price: €{processed.price_info.current_price}")
        print(f"   💵 List Price (PVP): €{processed.price_info.list_price or 'N/A'}")
        print(f"   🏷️  Discount: {processed.price_info.savings_percentage or 0:.0f}%")
        print(f"   🖼️  Image: {processed.price_info.main_image_url[:80] if processed.price_info.main_image_url else 'N/A'}...")
        print(f"   🔗 Short Link: {processed.short_link.short_url}")
        
        if processed.rating:
            print(f"   ⭐ Rating: {processed.rating.stars} {processed.rating.value}/5 ({processed.rating.count:,}+)")
        else:
            print(f"   ⭐ Rating: Not available")
        
        # Format message
        message = controller.formatter.format_message(processed)
        print(f"\n📱 WhatsApp Message:")
        print("─" * 70)
        print(message)
        print("─" * 70)
        
        # Publish to channel
        print(f"\n📡 Publishing to WhatsApp channel...")
        result = controller.publish_to_whatsapp(processed, to_group=False)
        
        if result.success:
            print(f"\n✅ SUCCESS! Message published with:")
            print(f"   • Image: {'✅ Yes' if processed.price_info.main_image_url else '❌ No'}")
            print(f"   • PVP/Discount: {'✅ Yes' if processed.price_info.list_price else '❌ No'}")
            print(f"   • Rating: {'✅ Yes' if processed.rating else '❌ No'}")
            print(f"   • Destinations: {result.destinations}")
            print(f"\n🎉 Check your WhatsApp channel now!")
        else:
            print(f"\n❌ Failed: {result.error}")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
