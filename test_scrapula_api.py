#!/usr/bin/env python3
"""Test Scrapula API to get Amazon product data."""

import requests
import json

def test_scrapula_api():
    """Test Scrapula API endpoints."""
    
    api_key = "ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA"
    
    print("=" * 70)
    print("Testing Scrapula API")
    print("=" * 70)
    
    # Common API endpoint patterns to try
    base_urls = [
        "https://api.datapipeplatform.cloud",
        "https://datapipeplatform.cloud/api",
        "https://api.scrapula.com",
    ]
    
    # Common endpoints for Amazon product data
    endpoints = [
        "/product",
        "/amazon/product",
        "/v1/product",
        "/v1/amazon/product",
        "/scrape/amazon",
    ]
    
    # Test ASIN
    test_asin = "B06XGWGGD8"
    test_url = f"https://www.amazon.es/dp/{test_asin}"
    
    print(f"\nAPI Key: {api_key[:20]}...")
    print(f"Test ASIN: {test_asin}")
    print(f"Test URL: {test_url}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }
    
    print(f"\n{'=' * 70}")
    print("Trying Common API Patterns")
    print('=' * 70)
    
    for base_url in base_urls:
        for endpoint in endpoints:
            full_url = f"{base_url}{endpoint}"
            
            print(f"\n📍 {full_url}")
            
            # Try GET with ASIN parameter
            try:
                params = {"asin": test_asin, "marketplace": "es"}
                response = requests.get(full_url, headers=headers, params=params, timeout=10)
                
                print(f"   GET with params: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS!")
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
                    return True, full_url, "GET", params
                    
            except Exception as e:
                print(f"   GET error: {str(e)[:40]}...")
            
            # Try POST with ASIN in body
            try:
                payload = {"asin": test_asin, "marketplace": "es"}
                response = requests.post(full_url, headers=headers, json=payload, timeout=10)
                
                print(f"   POST with JSON: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS!")
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
                    return True, full_url, "POST", payload
                    
            except Exception as e:
                print(f"   POST error: {str(e)[:40]}...")
            
            # Try POST with URL
            try:
                payload = {"url": test_url}
                response = requests.post(full_url, headers=headers, json=payload, timeout=10)
                
                print(f"   POST with URL: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS!")
                    data = response.json()
                    print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
                    return True, full_url, "POST", payload
                    
            except Exception as e:
                print(f"   POST with URL error: {str(e)[:40]}...")
    
    print(f"\n{'=' * 70}")
    print("No working endpoint found")
    print('=' * 70)
    
    print(f"\n📧 Next Steps:")
    print(f"  1. Check Scrapula documentation at: https://datapipeplatform.cloud/api-docs")
    print(f"  2. Look for API documentation link or tab")
    print(f"  3. Find the correct endpoint format")
    print(f"  4. Contact Scrapula support if docs aren't clear")
    
    return False, None, None, None

if __name__ == "__main__":
    success, url, method, params = test_scrapula_api()
    
    if success:
        print(f"\n{'=' * 70}")
        print("✅ FOUND WORKING SCRAPULA API!")
        print('=' * 70)
        print(f"\nEndpoint: {url}")
        print(f"Method: {method}")
        print(f"Parameters: {params}")
        print(f"\nReady to integrate into DealBot!")
