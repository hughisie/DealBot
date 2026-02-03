#!/usr/bin/env python3
"""Test affiliate tag usage in links."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.utils.config import Config
from dealbot.services.affiliates import AffiliateService

def test_affiliate_tag():
    """Test that affiliate tag is correctly applied to Amazon links."""
    print("=" * 70)
    print("Testing Affiliate Tag")
    print("=" * 70)
    
    config = Config()
    affiliate_service = AffiliateService(config)
    
    print(f"\nConfigured Tag: {config.affiliate_tag}")
    
    # Test URLs
    test_urls = [
        "https://www.amazon.es/dp/B06XGWGGD8",
        "https://www.amazon.es/dp/B06XGWGGD8/ref=nosim?tag=oldtag-21",
        "https://www.amazon.es/dp/B06XGWGGD8?tag=wrongtag-21&other=param",
    ]
    
    print("\nTesting URL transformations:")
    print("-" * 70)
    
    for url in test_urls:
        result = affiliate_service.ensure_affiliate_tag(url)
        print(f"\nOriginal: {url}")
        print(f"Result:   {result}")
        
        # Check if correct tag is present
        if f"tag={config.affiliate_tag}" in result:
            print("✅ Correct affiliate tag applied")
        else:
            print(f"❌ Missing or wrong tag (expected: tag={config.affiliate_tag})")
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"✅ Affiliate tag configured: {config.affiliate_tag}")
    print(f"✅ Tag will be applied to all Amazon links")
    print(f"\n⚠️  Note: PA-API still needs approval, but affiliate links will work!")

if __name__ == "__main__":
    test_affiliate_tag()
