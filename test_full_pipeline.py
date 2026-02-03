#!/usr/bin/env python
"""Test the full deal processing pipeline."""

import sys
from pathlib import Path

from adp.controller import DealController
from adp.utils.config import Config
from adp.utils.logging import get_logger

logger = get_logger(__name__)


def main():
    """Test processing the test file."""
    config = Config()
    controller = DealController(config)
    
    # Parse the test file
    test_file = Path("TEST 2025-11-10_1602_evening_whatsapp TEST.txt")
    logger.info(f"Parsing test file: {test_file}")
    
    deals = controller.parse_file(test_file)
    logger.info(f"Found {len(deals)} deals")
    
    if not deals:
        logger.error("No deals found!")
        return 1
    
    # Process each deal
    for i, deal in enumerate(deals, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing Deal {i}/{len(deals)}")
        logger.info(f"Title: {deal.title}")
        logger.info(f"ASIN: {deal.asin}")
        logger.info(f"Stated Price: €{deal.stated_price}")
        logger.info(f"{'='*60}\n")
        
        try:
            # Process the deal (validate, adjust price, create short link)
            processed = controller.process_deal(deal)
            
            logger.info(f"✅ Deal processed successfully!")
            logger.info(f"   Validated Price: €{processed.price_info.current_price}")
            logger.info(f"   Adjusted Price: €{processed.adjusted_price}")
            logger.info(f"   Short Link: {processed.short_link.short_url}")
            logger.info(f"   Needs Review: {processed.price_info.needs_review}")
            
            # Format WhatsApp message
            whatsapp_msg = controller.formatter.format_message(processed)
            logger.info(f"\n📱 WhatsApp Message:\n{whatsapp_msg}\n")
            
        except Exception as e:
            logger.error(f"❌ Failed to process deal: {e}", exc_info=True)
            return 1
    
    logger.info("✅ All deals processed successfully!")
    logger.info("\nℹ️  To publish to WhatsApp, use the GUI and click 'Process & Publish Selected'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
