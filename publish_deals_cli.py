#!/usr/bin/env python3
"""
Command-line script to publish deals directly, bypassing GUI.
This demonstrates the fixes are working by actually publishing to WhatsApp.
"""
import sys
import time
import logging
from pathlib import Path

# Add project to path - must come BEFORE imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "dealbot"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("\n" + "="*70)
    print("🚀 DEALBOT AUTOMATED PUBLISH - COMMAND LINE TEST")
    print("="*70 + "\n")
    
    try:
        from dealbot.utils.config import Config
        from dealbot.controller import DealController
        
        # Load configuration
        print("📋 Loading configuration...")
        config = Config()  # Automatically loads config.yaml and .env
        print("✅ Configuration loaded\n")
        
        # Initialize controller
        print("🔧 Initializing controller...")
        controller = DealController(config)
        print("✅ Controller initialized\n")
        
        # Parse file
        test_file = project_root / "PRODUCTION_TEST.txt"
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return 1
            
        print(f"📂 Parsing file: {test_file.name}")
        deals = controller.parse_file(test_file)
        print(f"✅ Parsed {len(deals)} deals\n")
        
        # Process deals in preview mode
        print(f"🔄 Processing {len(deals)} deals (preview mode - no shortlinks)...")
        processed_deals = []
        errors = 0
        
        for i, deal in enumerate(deals, 1):
            try:
                processed = controller.process_deal(deal, for_preview=True)
                processed_deals.append(processed)
                
                if i % 5 == 0 or i == len(deals):
                    print(f"   ✓ Processed {i}/{len(deals)}")
                    
            except Exception as e:
                errors += 1
                print(f"   ⚠️  Error processing deal {i} ({deal.asin}): {e}")
        
        print(f"\n✅ Preview complete: {len(processed_deals)}/{len(deals)} deals processed ({errors} errors)\n")
        
        # Filter ready deals
        ready_deals = []
        for processed in processed_deals:
            if (processed.price_info and 
                processed.price_info.current_price and 
                processed.price_info.availability in ["Now", None, ""]):
                ready_deals.append(processed)
        
        print(f"📊 Ready to publish: {len(ready_deals)}/{len(processed_deals)} deals")
        print(f"   (Filtered out {len(processed_deals) - len(ready_deals)} out-of-stock/unavailable)\n")
        
        if len(ready_deals) == 0:
            print("❌ No deals ready to publish (all out of stock or had errors)")
            return 1
        
        # Ask for confirmation
        print(f"⚠️  About to publish {len(ready_deals)} deals to WhatsApp")
        print("   This will create shortlinks and send real messages!")
        response = input("\n   Continue? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("\n❌ Publishing cancelled by user")
            return 0
        
        # Publish deals
        print(f"\n🚀 Publishing {len(ready_deals)} deals to WhatsApp...\n")
        published_count = 0
        failed_count = 0
        
        for i, processed in enumerate(ready_deals, 1):
            try:
                # Reprocess with shortlinks enabled (for_preview=False)
                print(f"   [{i}/{len(ready_deals)}] Processing: {processed.deal.title[:50]}...")
                final_processed = controller.process_deal(processed.deal, for_preview=False)
                
                # Publish
                result = controller.publish_deal(final_processed, include_group=False)
                
                if result.publish_result and result.publish_result.success:
                    published_count += 1
                    print(f"      ✅ Published successfully")
                else:
                    failed_count += 1
                    error = result.publish_result.error if result.publish_result else "Unknown error"
                    print(f"      ❌ Failed: {error}")
                
                # Rate limiting
                time.sleep(3)
                
            except Exception as e:
                failed_count += 1
                print(f"      ⚠️  Exception: {e}")
        
        # Summary
        print("\n" + "="*70)
        print(f"✅ PUBLISHING COMPLETE")
        print(f"   Published: {published_count}/{len(ready_deals)}")
        print(f"   Failed: {failed_count}/{len(ready_deals)}")
        print("="*70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
