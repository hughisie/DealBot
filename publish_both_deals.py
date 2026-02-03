#!/usr/bin/env python
"""Publish both test deals to WhatsApp channel."""

import sys
import time
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
    
    published_count = 0
    
    for i, deal in enumerate(deals, 1):
        print(f"\n{'='*70}")
        print(f"📦 Deal {i}/{len(deals)}: {deal.title[:50]}...")
        print(f"{'='*70}")
        
        try:
            # Process the deal
            processed = controller.process_deal(deal)
            print(f"✅ Processed - €{processed.adjusted_price} - {processed.short_link.short_url}")
            
            # Format message
            message = controller.formatter.format_message(processed)
            print(f"\n📱 Message preview:")
            print(message[:200] + "...")
            
            # Publish to channel
            print(f"\n📡 Publishing to channel...")
            result = controller.publish_to_whatsapp(processed, to_group=False)
            
            if result.success:
                print(f"✅ Published successfully!")
                published_count += 1
            else:
                print(f"❌ Failed: {result.error}")
            
            # Small delay between messages
            if i < len(deals):
                time.sleep(2)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*70}")
    print(f"✅ Successfully published: {published_count}/{len(deals)}")
    print(f"{'='*70}\n")
    
    if published_count == len(deals):
        print("🎉 All deals published to your WhatsApp channel!")
        return 0
    else:
        print("⚠️ Some deals failed to publish")
        return 1

if __name__ == "__main__":
    sys.exit(main())
