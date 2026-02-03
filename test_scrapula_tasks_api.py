#!/usr/bin/env python3
"""Test Scrapula Tasks API to find Amazon service name."""

import requests
import json
import time

def test_scrapula_tasks_api():
    """Test Scrapula Tasks API to discover Amazon service."""
    
    api_key = "ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA"
    base_url = "https://api.datapipeplatform.com"
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
    print("=" * 70)
    print("Scrapula Tasks API Test")
    print("=" * 70)
    
    # Try common Amazon service name patterns
    service_names = [
        "amazon_product_service",
        "amazon_scraper_service",
        "amazon_service",
        "amazon_product_scraper",
        "amazon_search_service",
        "amazon_product_v1",
        "amazon_products",
    ]
    
    test_asin = "B06XGWGGD8"
    
    print(f"\nTrying to create task with different service names...")
    print(f"Test ASIN: {test_asin}")
    print(f"API Key: {api_key[:20]}...")
    
    for service_name in service_names:
        print(f"\n{'=' * 70}")
        print(f"Testing: {service_name}")
        print('-' * 70)
        
        payload = {
            "service_name": service_name,
            "queries": [test_asin],
        }
        
        try:
            response = requests.post(
                f"{base_url}/tasks",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Task created!")
                print(f"Task ID: {data.get('id')}")
                
                if data.get('id'):
                    # Wait a bit then check results
                    task_id = data['id']
                    print(f"\nWaiting 5 seconds for task to complete...")
                    time.sleep(5)
                    
                    # Get results
                    result_response = requests.get(
                        f"{base_url}/tasks/{task_id}",
                        headers=headers,
                        timeout=10
                    )
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        print(f"\nTask Status: {result_data.get('status')}")
                        
                        if result_data.get('results'):
                            print(f"✅ Got results!")
                            print(f"\n🎉 WORKING SERVICE NAME: {service_name}")
                            print(f"\nSample data:")
                            print(json.dumps(result_data['results'][0], indent=2)[:500])
                            return service_name
                        else:
                            print(f"⏳ Task created but no results yet")
                            print(f"   Try checking task ID manually: {task_id}")
                    
            elif response.status_code == 400:
                error = response.json()
                print(f"❌ Invalid request: {error}")
            elif response.status_code == 401:
                print(f"❌ Authentication failed")
                break  # No point trying other names
            else:
                print(f"⚠️  Unexpected response: {response.text[:100]}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout")
        except Exception as e:
            print(f"❌ Error: {str(e)[:60]}")
    
    print(f"\n{'=' * 70}")
    print("No working service name found")
    print('=' * 70)
    
    print(f"\n📋 Next Steps:")
    print(f"1. Login to: https://datapipeplatform.cloud")
    print(f"2. Go to dashboard/services section")
    print(f"3. Look for Amazon scraping service")
    print(f"4. Copy the exact service_name")
    print(f"5. OR check your previous tasks to see what service was used")
    
    print(f"\n💡 Alternative: Check recent tasks")
    print(f"   GET {base_url}/tasks")
    print(f"   This will show your recent tasks with their service names")
    
    return None

if __name__ == "__main__":
    service_name = test_scrapula_tasks_api()
    
    if service_name:
        print(f"\n{'=' * 70}")
        print(f"✅ READY TO INTEGRATE!")
        print('=' * 70)
        print(f"\nWorking service name: {service_name}")
        print(f"\nI can now update the Scrapula service with this!")
    else:
        print(f"\n{'=' * 70}")
        print("Need Manual Check")
        print('=' * 70)
        print(f"\nPlease check your Scrapula dashboard for:")
        print(f"  - Available services list")
        print(f"  - Amazon product scraping service name")
        print(f"  - Or check a previous Amazon task you've created")
