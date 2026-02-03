#!/usr/bin/env python
"""Test full publishing to WhatsApp broadcast channel."""

import sys
from pathlib import Path

from adp.controller import DealController
from adp.utils.config import Config
from adp.utils.logging import get_logger

logger = get_logger(__name__)


def main():
    """Test publishing the test file to WhatsApp."""
    config = Config()
    controller = DealController(config)
    
    # Parse the test file
    test_file = Path("TEST 2025-11-10_1602_evening_whatsapp TEST.txt")
    logger.info(f"📂 Parsing test file: {test_file}")
    
    deals = controller.parse_file(test_file)
    logger.info(f"✅ Found {len(deals)} deals\n")
    
    if not deals:
        logger.error("❌ No deals found!")
        return 1
    
    # Process and publish each deal
    results = []
    for i, deal in enumerate(deals, 1):
        logger.info(f"\n{'='*70}")
        logger.info(f"📦 Deal {i}/{len(deals)}: {deal.title[:50]}...")
        logger.info(f"{'='*70}\n")
        
        try:
            # Process the deal
            processed = controller.process_deal(deal)
            
            logger.info(f"✅ Deal processed:")
            logger.info(f"   💰 Adjusted Price: €{processed.adjusted_price:.2f}")
            logger.info(f"   🔗 Short Link: {processed.short_link.short_url}")
            logger.info(f"   ⚠️  Needs Review: {processed.price_info.needs_review}")
            
            # Format WhatsApp message
            whatsapp_msg = controller.formatter.format_message(processed)
            logger.info(f"\n📱 WhatsApp Message Preview:")
            logger.info("─" * 50)
            logger.info(whatsapp_msg)
            logger.info("─" * 50)
            
            # Publish to WhatsApp broadcast channel
            logger.info(f"\n📡 Publishing to WhatsApp broadcast channel...")
            publish_result = controller.publish_to_whatsapp(
                processed, 
                to_group=False  # Send to channel, not group
            )
            
            if publish_result.success:
                logger.info(f"✅ Successfully published!")
                logger.info(f"   📍 Destinations: {len(publish_result.destinations)}")
                for destination in publish_result.destinations:
                    logger.info(f"      • {destination}")
            else:
                logger.error(f"❌ Failed to publish: {publish_result.error}")
            
            results.append(publish_result)
            
        except Exception as e:
            logger.error(f"❌ Failed to process/publish deal: {e}", exc_info=True)
            return 1
    
    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("📊 PUBLISHING SUMMARY")
    logger.info(f"{'='*70}")
    successful = sum(1 for r in results if r.success)
    logger.info(f"✅ Successful: {successful}/{len(results)}")
    logger.info(f"❌ Failed: {len(results) - successful}/{len(results)}")
    
    if successful == len(results):
        logger.info(f"\n🎉 All deals published successfully to WhatsApp broadcast channel!")
        return 0
    else:
        logger.error(f"\n⚠️  Some deals failed to publish")
        return 1


if __name__ == "__main__":
    sys.exit(main())
