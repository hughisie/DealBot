#!/usr/bin/env python
"""Simple test to publish directly to WhatsApp channel."""

import sys
from adp.controller import DealController
from adp.utils.config import Config

def main():
    config = Config()
    controller = DealController(config)
    
    # Parse test file
    print("📂 Parsing test file...")
    deals = controller.parse_file('TEST 2025-11-10_1602_evening_whatsapp TEST.txt')
    print(f"✅ Found {len(deals)} deals\n")
    
    if not deals:
        print("❌ No deals found")
        return 1
    
    # Process first deal only
    deal = deals[0]
    print(f"📦 Processing: {deal.title[:50]}...")
    
    try:
        # Process the deal
        processed = controller.process_deal(deal)
        print(f"✅ Deal processed")
        print(f"   💰 Price: €{processed.adjusted_price}")
        print(f"   🔗 Link: {processed.short_link.short_url}")
        
        # Format message
        message = controller.formatter.format_message(processed)
        print(f"\n📱 Message to send:")
        print("─" * 50)
        print(message)
        print("─" * 50)
        
        # Publish to channel (not group)
        print(f"\n📡 Publishing to channel...")
        result = controller.publish_to_whatsapp(processed, to_group=False)
        
        if result.success:
            print(f"✅ Published successfully!")
            print(f"   Destinations: {result.destinations}")
            print(f"   Message IDs: {result.message_ids}")
        else:
            print(f"❌ Failed: {result.error}")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
