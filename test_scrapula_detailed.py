#!/usr/bin/env python3
"""Detailed Scrapula API test to see actual responses."""

import requests
import json

def test_scrapula_detailed():
    """Test Scrapula API with detailed response inspection."""
    
    api_key = "ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA"
    
    print("=" * 70)
    print("Scrapula API Detailed Test")
    print("=" * 70)
    
    # Test with ASIN
    test_asin = "B06XGWGGD8"
    test_url = "https://www.amazon.es/dp/B06XGWGGD8"
    
    # Common header patterns
    header_variations = [
        {"Authorization": f"Bearer {api_key}"},
        {"X-API-Key": api_key},
        {"api-key": api_key},
        {"apikey": api_key},
    ]
    
    base_url = "https://datapipeplatform.cloud/api"
    
    print(f"\nAPI Key: {api_key[:20]}...")
    print(f"Base URL: {base_url}")
    print(f"Test ASIN: {test_asin}")
    
    # Test different endpoint and header combinations
    tests = [
        ("POST", "/product", {"url": test_url}),
        ("POST", "/scrape", {"url": test_url}),
        ("POST", "/amazon/scrape", {"url": test_url, "marketplace": "es"}),
        ("POST", "/product", {"asin": test_asin, "marketplace": "es"}),
        ("GET", "/product", {"asin": test_asin}),
    ]
    
    for method, endpoint, params in tests:
        for headers in header_variations:
            url = f"{base_url}{endpoint}"
            
            print(f"\n{'=' * 70}")
            print(f"{method} {url}")
            print(f"Headers: {list(headers.keys())}")
            print(f"Params/Body: {params}")
            print('-' * 70)
            
            try:
                if method == "GET":
                    response = requests.get(url, headers=headers, params=params, timeout=10)
                else:
                    response = requests.post(url, headers=headers, json=params, timeout=10)
                
                print(f"Status: {response.status_code}")
                print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                print(f"Response Length: {len(response.content)} bytes")
                
                # Try to parse JSON
                try:
                    data = response.json()
                    print(f"✅ Valid JSON response!")
                    print(f"\nResponse:")
                    print(json.dumps(data, indent=2)[:1000])
                    
                    # Check if it contains product data
                    if any(key in data for key in ['title', 'price', 'asin', 'product', 'data']):
                        print(f"\n🎉 FOUND WORKING API!")
                        return True, url, method, params, headers
                        
                except:
                    # Not JSON, show text
                    text = response.text[:500]
                    if text:
                        print(f"Text response: {text}")
                    else:
                        print("⚠️  Empty response")
                
                # Check for error messages
                if response.status_code >= 400:
                    print(f"❌ Error status: {response.status_code}")
                    if response.text:
                        print(f"Error message: {response.text[:200]}")
                
            except requests.exceptions.Timeout:
                print(f"⏱️  Timeout")
            except Exception as e:
                print(f"❌ Error: {str(e)[:100]}")
    
    print(f"\n{'=' * 70}")
    print("Testing Complete")
    print('=' * 70)
    
    print(f"\n📧 Need Help:")
    print(f"  1. Login to: https://datapipeplatform.cloud")
    print(f"  2. Check API documentation or dashboard")
    print(f"  3. Look for:")
    print(f"     - Correct endpoint URL")
    print(f"     - Required headers format")
    print(f"     - Request body structure")
    print(f"     - Example requests")
    
    return False, None, None, None, None

if __name__ == "__main__":
    success, url, method, params, headers = test_scrapula_detailed()
    
    if success:
        print(f"\n{'=' * 70}")
        print("✅ READY TO INTEGRATE!")
        print('=' * 70)
        print(f"\nEndpoint: {url}")
        print(f"Method: {method}")
        print(f"Headers: {headers}")
        print(f"Body: {params}")
