#!/usr/bin/env python3
"""Check if the issue is PA-API sales requirement."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from amazon_paapi import AmazonApi
import time

def test_sales_requirement():
    """
    PA-API 5.0 requires:
    - 10 qualified sales in trailing 30 days
    - OR recent credential creation (grace period)
    
    If neither condition is met, you get 403 Forbidden.
    """
    
    print("=" * 70)
    print("PA-API Sales Requirement Analysis")
    print("=" * 70)
    
    # Credentials from CSV
    access_key = "AKPA0DQU0S1763063154"
    secret_key = "8M+aK0sKmYBjxfQk2HL6KdEKuiJtX13xpQiNuDWL"
    
    # Both tracking IDs
    tracking_ids = ["retroshell00-20", "amazoneschollos-20"]
    
    print(f"\nFrom PA-API Documentation:")
    print(f"  'To maintain access to PA-API, you must:")
    print(f"   - Complete at least 10 qualified sales in trailing 30 days'")
    print(f"\nYour Status:")
    print(f"  Credentials Created: Thu Nov 13 19:45:54 UTC 2025")
    print(f"  Time Since Creation: ~14 hours")
    print(f"  Tracking IDs: {', '.join(tracking_ids)}")
    
    print(f"\n{'=' * 70}")
    print("Testing Immediate Activation")
    print('=' * 70)
    
    # Test with minimal delay between requests
    for tag_index, tag in enumerate(tracking_ids):
        print(f"\n📋 Tracking ID: {tag}")
        
        # Test US marketplace (most common)
        try:
            api = AmazonApi(
                key=access_key,
                secret=secret_key,
                tag=tag,
                country="US",
                throttling=0.5
            )
            
            print(f"   Testing: US marketplace")
            items = api.get_items(["B08N5WRWNW"])
            
            if items and len(items) > 0:
                print(f"   ✅ SUCCESS with {tag}!")
                return True, tag
            else:
                print(f"   ⚠️  Empty response")
                
        except Exception as e:
            error_msg = str(e)
            
            if "403" in error_msg or "Forbidden" in error_msg:
                print(f"   ❌ 403 Forbidden")
            elif "TooManyRequests" in error_msg or "RequestThrottled" in error_msg:
                print(f"   ⚠️  Rate limited - waiting 2 seconds...")
                time.sleep(2)
            else:
                print(f"   ❌ Error: {error_msg[:60]}...")
        
        # Small delay between tracking ID tests
        if tag_index < len(tracking_ids) - 1:
            time.sleep(1)
    
    print(f"\n{'=' * 70}")
    print("PA-API Access Requirements Check")
    print('=' * 70)
    
    print(f"\n📋 Requirements for PA-API Access:")
    print(f"  1. ✅ Approved Amazon Associates account")
    print(f"  2. ✅ PA-API credentials generated")
    print(f"  3. ✅ Valid tracking ID")
    print(f"  4. ❓ Sales requirement:")
    print(f"     → 10 qualified sales in trailing 30 days")
    print(f"     → OR grace period for new accounts")
    
    print(f"\n🔍 Most Likely Cause:")
    print(f"  Your Associates account may not have met the 10 sales threshold")
    print(f"  ")
    print(f"  When you DELETED the old credentials and created NEW ones:")
    print(f"  → The grace period may have reset")
    print(f"  → Amazon re-checked your sales count")
    print(f"  → If below 10 sales, PA-API access suspended")
    
    print(f"\n💡 Solutions:")
    print(f"  ")
    print(f"  Option 1: Check Your Sales Count")
    print(f"  → Log into Amazon Associates")
    print(f"  → Go to Reports")
    print(f"  → Check 'Qualifying Sales' in last 30 days")
    print(f"  → Need at least 10 qualifying sales")
    print(f"  ")
    print(f"  Option 2: Generate Sales")
    print(f"  → Make purchases through your affiliate links")
    print(f"  → Need 10 'qualifying' sales (not canceled/returned)")
    print(f"  → Sales must be from different customers")
    print(f"  ")
    print(f"  Option 3: Contact Amazon Support")
    print(f"  → Explain credentials were working Wednesday")
    print(f"  → Ask why new credentials getting 403")
    print(f"  → Request manual review of PA-API access")
    print(f"  ")
    print(f"  Option 4: Use Old Credentials (if not fully deleted)")
    print(f"  → Check if old credentials still exist in Amazon dashboard")
    print(f"  → If they do, use those instead")
    
    return False, None

if __name__ == "__main__":
    success, working_tag = test_sales_requirement()
    
    if not success:
        print(f"\n{'=' * 70}")
        print("IMMEDIATE ACTION REQUIRED")
        print('=' * 70)
        
        print(f"\n1. Check your Associates dashboard:")
        print(f"   https://affiliate-program.amazon.com/home/reports")
        print(f"   ")
        print(f"   Look for:")
        print(f"   - 'Orders' or 'Clicks' in last 30 days")
        print(f"   - 'Qualified Sales' count")
        print(f"   - Any warnings about PA-API access")
        
        print(f"\n2. The PA-API requirement states:")
        print(f"   'In order to gain PA API access and maintain the ability to")
        print(f"    call PA API, you must generate 10 qualified sales in the")
        print(f"    trailing 30 days.'")
        
        print(f"\n3. If sales < 10:")
        print(f"   → This is why you're getting 403 Forbidden")
        print(f"   → DealBot will continue using TXT file prices (fallback)")
        print(f"   → Generate sales to regain PA-API access")
        
        print(f"\n4. If sales >= 10:")
        print(f"   → Contact Amazon Associates support")
        print(f"   → Provide Access Key: AKPA0DQU0S1763063154")
        print(f"   → Ask why PA-API returning 403 with sufficient sales")
