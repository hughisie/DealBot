#!/usr/bin/env python3
"""Direct test of Scrapula API endpoint."""

import requests
import json

api_key = "ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA"
service_name = "amazon_products_service_v2"

print("=" * 70)
print("Direct Scrapula API Test")
print("=" * 70)

# Test different possible endpoints
endpoints = [
    "https://datapipeplatform.cloud/api/tasks",
    "https://datapipeplatform.cloud/tasks",
    "https://api.datapipeplatform.cloud/tasks",
]

payload = {
    "service_name": service_name,
    "queries": ["https://www.amazon.es/dp/B06XGWGGD8"],
    "settings": {
        "output_extension": "xlsx"
    }
}

headers = {
    "X-API-KEY": api_key,
    "Content-Type": "application/json"
}

for endpoint in endpoints:
    print(f"\n{'=' * 70}")
    print(f"Testing: {endpoint}")
    print('=' * 70)
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        print(f"Response Length: {len(response.content)} bytes")
        print(f"\nFirst 500 chars of response:")
        print(response.text[:500])
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ Valid JSON response!")
                print(f"Response data: {json.dumps(data, indent=2)[:300]}...")
                break
            except:
                print(f"\n❌ Response is not JSON")
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n{'=' * 70}")
print("Test Complete")
print('=' * 70)
