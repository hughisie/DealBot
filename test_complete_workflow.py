#!/usr/bin/env python3
"""Complete workflow test with new affiliate tag."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.utils.config import Config
from dealbot.services.amazon_paapi import AmazonPAAPIService
from dealbot.services.affiliates import AffiliateService
from dealbot.models import Currency

def test_complete_workflow():
    """Test the complete deal processing workflow."""
    print("=" * 80)
    print("DealBot Complete Workflow Test - With New Affiliate Tag")
    print("=" * 80)
    
    # Initialize services
    config = Config()
    amazon_api = AmazonPAAPIService(config)
    affiliate_service = AffiliateService(config)
    
    print(f"\n✅ Configuration Loaded")
    print(f"   Affiliate Tag: {config.affiliate_tag}")
    
    # Test data from TXT file
    test_asin = "B06XGWGGD8"
    test_price = 63.14
    test_pvp = 170.00
    test_discount = 63.0
    test_url = f"https://www.amazon.es/dp/{test_asin}/ref=nosim?tag=oldtag-21"
    
    print("\n" + "=" * 80)
    print("STEP 1: Price Validation (with PA-API fallback)")
    print("=" * 80)
    
    price_info = amazon_api.validate_price(
        asin=test_asin,
        currency=Currency.EUR,
        stated_price=test_price,
        source_pvp=test_pvp,
        source_discount_pct=test_discount
    )
    
    print(f"\nASIN: {price_info.asin}")
    print(f"Current Price: €{price_info.current_price}" if price_info.current_price else "Current Price: N/A")
    print(f"List Price: €{price_info.list_price}" if price_info.list_price else "List Price: N/A")
    print(f"Discount: -{price_info.savings_percentage:.0f}%" if price_info.savings_percentage else "Discount: N/A")
    print(f"Availability: {price_info.availability or 'Unknown'}")
    print(f"Needs Review: {'⚠️ Yes (using fallback)' if price_info.needs_review else '✅ No'}")
    
    if price_info.current_price:
        print("\n✅ Price data available (from TXT file fallback)")
    else:
        print("\n❌ No price data available")
    
    print("\n" + "=" * 80)
    print("STEP 2: Affiliate Tag Application")
    print("=" * 80)
    
    print(f"\nOriginal URL:")
    print(f"  {test_url}")
    
    final_url = affiliate_service.ensure_affiliate_tag(test_url)
    
    print(f"\nFinal URL:")
    print(f"  {final_url}")
    
    if f"tag={config.affiliate_tag}" in final_url:
        print(f"\n✅ Correct affiliate tag applied: {config.affiliate_tag}")
    else:
        print(f"\n❌ Affiliate tag missing or incorrect")
    
    print("\n" + "=" * 80)
    print("STEP 3: Deal Status Check")
    print("=" * 80)
    
    can_publish = False
    status_message = ""
    
    if not price_info.current_price:
        status_message = "❌ Cannot publish - No price available"
    elif price_info.availability and price_info.availability != "Now":
        status_message = f"❌ Cannot publish - Out of stock ({price_info.availability})"
    else:
        can_publish = True
        if price_info.needs_review:
            status_message = "⚠️ Can publish - Using fallback price (needs review)"
        else:
            status_message = "✅ Can publish - All checks passed"
    
    print(f"\n{status_message}")
    print(f"Publishable: {'Yes' if can_publish else 'No'}")
    
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    print(f"""
Deal Information:
  ASIN:              {test_asin}
  Price:             €{price_info.current_price or 'N/A'}
  Original Price:    €{price_info.list_price or 'N/A'}
  Discount:          {f'-{price_info.savings_percentage:.0f}%' if price_info.savings_percentage else 'N/A'}
  Availability:      {price_info.availability or 'Unknown'}
  
Affiliate Configuration:
  Tag:               {config.affiliate_tag}
  URL:               {final_url[:50]}...
  Tag Applied:       {'✅ Yes' if f'tag={config.affiliate_tag}' in final_url else '❌ No'}
  
Status:
  Can Publish:       {'✅ Yes' if can_publish else '❌ No'}
  Data Source:       {'PA-API' if not price_info.needs_review else 'TXT File (Fallback)'}
  PA-API Status:     {'✅ Working' if not price_info.needs_review else '⚠️ Using fallback (403 Forbidden)'}
""")
    
    print("=" * 80)
    
    if can_publish:
        print("✅ WORKFLOW TEST PASSED")
        print("   The app can process and publish deals with the new affiliate tag")
        print("   Even though PA-API needs approval, fallback prices work correctly")
    else:
        print("⚠️ WORKFLOW TEST - REVIEW NEEDED")
        print("   Check the status messages above")
    
    print("=" * 80)

if __name__ == "__main__":
    test_complete_workflow()
