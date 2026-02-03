#!/usr/bin/env python3
"""Diagnose what changed since Wednesday when it was working."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from amazon_paapi import AmazonApi
import json

def test_detailed_error():
    """Get detailed error information to diagnose the issue."""
    
    print("=" * 70)
    print("Detailed PA-API Error Diagnosis")
    print("=" * 70)
    
    # Current credentials (created yesterday)
    access_key = "AKPA0DQU0S1763063154"
    secret_key = "8M+aK0sKmYBjxfQk2HL6KdEKuiJtX13xpQiNuDWL"
    partner_tag = "retroshell00-20"
    
    print(f"\nCredentials:")
    print(f"  Access Key: {access_key}")
    print(f"  Created: Thu Nov 13 19:45:54 UTC 2025")
    print(f"  Partner Tag: {partner_tag}")
    print(f"  Status: Active (from screenshot)")
    
    print(f"\nUser Report:")
    print(f"  ✅ Was working on Wednesday (Nov 13)")
    print(f"  ❌ Not working now (Nov 14)")
    
    # Test configurations
    test_configs = [
        ("US", "B08N5WRWNW", "United States - amazon.com"),
        ("UK", "B07VGRJDFY", "United Kingdom - amazon.co.uk"),
        ("ES", "B06XGWGGD8", "Spain - amazon.es"),
        ("CA", "B08N5WRWNW", "Canada - amazon.ca"),
        ("AU", "B07VGRJDFY", "Australia - amazon.com.au"),
    ]
    
    print(f"\n{'=' * 70}")
    print("Testing All Marketplaces")
    print('=' * 70)
    
    for country, asin, description in test_configs:
        print(f"\n📍 {description}")
        
        try:
            api = AmazonApi(
                key=access_key,
                secret=secret_key,
                tag=partner_tag,
                country=country,
                throttling=1.0  # Be conservative
            )
            
            # Try GetItems
            items = api.get_items([asin])
            
            if items and len(items) > 0:
                item = items[0]
                title = item.item_info.title.display_value if item.item_info.title else "N/A"
                
                print(f"   🎉 SUCCESS!")
                print(f"   Title: {title[:50]}...")
                
                # Get price
                if hasattr(item, "offers") and item.offers and item.offers.listings:
                    listing = item.offers.listings[0]
                    if hasattr(listing, "price") and listing.price:
                        print(f"   Price: {listing.price.display_amount}")
                
                print(f"\n{'=' * 70}")
                print(f"✅ FOUND WORKING MARKETPLACE!")
                print('=' * 70)
                print(f"\nWorking Configuration:")
                print(f"  Marketplace: {country} ({description})")
                print(f"  Partner Tag: {partner_tag}")
                print(f"  Access Key: {access_key}")
                return True, country
            else:
                print(f"   ⚠️  Empty response")
                
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Error: {error_msg[:80]}...")
            
            # Detailed error analysis
            if "403" in error_msg or "Forbidden" in error_msg:
                print(f"      → 403 Forbidden")
            elif "InvalidPartnerTag" in error_msg:
                print(f"      → Partner tag '{partner_tag}' not recognized")
            elif "InvalidClientTokenId" in error_msg:
                print(f"      → Access Key invalid")
            elif "SignatureDoesNotMatch" in error_msg:
                print(f"      → Secret Key incorrect or signature issue")
            elif "RequestThrottled" in error_msg:
                print(f"      → Too many requests (rate limited)")
            elif "InvalidParameterValue" in error_msg:
                print(f"      → Invalid parameter in request")
    
    print(f"\n{'=' * 70}")
    print("Diagnosis")
    print('=' * 70)
    
    print(f"\n❌ PA-API not working on ANY marketplace")
    print(f"\n🔍 Possible Causes:")
    print(f"  1. **Sales Requirement Not Met**")
    print(f"     → PA-API requires 10 qualified sales in trailing 30 days")
    print(f"     → If sales dropped below threshold, API access suspended")
    print(f"  ")
    print(f"  2. **Credentials Invalidated**")
    print(f"     → Old credentials from Wednesday may have been deleted")
    print(f"     → New credentials need different tracking ID")
    print(f"  ")
    print(f"  3. **Account Status Changed**")
    print(f"     → Associates account may have issue")
    print(f"     → PA-API access may have been revoked")
    print(f"  ")
    print(f"  4. **Rate Limiting**")
    print(f"     → Too many requests in short time")
    print(f"     → Try again after 1 hour")
    
    return False, None

if __name__ == "__main__":
    success, working_marketplace = test_detailed_error()
    
    if not success:
        print(f"\n{'=' * 70}")
        print("CRITICAL QUESTIONS TO ANSWER")
        print('=' * 70)
        print(f"\n1. Did you DELETE the old credentials from Wednesday?")
        print(f"   → If yes, that's why it stopped working")
        print(f"   → The app was using old credentials")
        print(f"\n2. Check your Associates account dashboard:")
        print(f"   → Any warnings or alerts?")
        print(f"   → Sales count in last 30 days?")
        print(f"   → PA-API status (approved/suspended)?")
        print(f"\n3. What were Wednesday's credentials?")
        print(f"   → Access Key starting with AKPA...")
        print(f"   → If different, that's the issue")
        print(f"\n4. Check email from Amazon:")
        print(f"   → Any notifications about PA-API access?")
        print(f"   → Account status changes?")
