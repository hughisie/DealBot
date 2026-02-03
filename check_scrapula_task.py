#!/usr/bin/env python3
"""Check status of the Scrapula task we just created."""

import requests
import time
import json

api_key = "ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA"
task_id = "ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmEsMjAyNTExMTQxMzMyNTl4czg1"

print("=" * 70)
print("Checking Scrapula Task Status")
print("=" * 70)
print(f"\nTask ID: {task_id}")
print(f"\n⏱️  Polling every 5 seconds (max 3 minutes)...")

headers = {"X-API-KEY": api_key}
start_time = time.time()
max_wait = 180  # 3 minutes

while time.time() - start_time < max_wait:
    try:
        response = requests.get(
            f"https://api.datapipeplatform.cloud/tasks/{task_id}",
            headers=headers,
            timeout=10
        )
        
        elapsed = int(time.time() - start_time)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "UNKNOWN")
            
            print(f"\n[{elapsed}s] Status: {status}")
            
            if status == "SUCCESS":
                print(f"\n{'=' * 70}")
                print("✅ TASK COMPLETE!")
                print('=' * 70)
                print(f"\nFull Response:")
                print(json.dumps(data, indent=2)[:1000])
                
                # Check for results
                if "results" in data:
                    print(f"\n✅ Has results!")
                    results = data["results"]
                    if isinstance(results, list) and len(results) > 0:
                        print(f"   Found {len(results)} result(s)")
                        for i, result in enumerate(results[:2]):
                            print(f"\n   Result {i+1}:")
                            if isinstance(result, dict):
                                if "file_url" in result:
                                    print(f"     File URL: {result['file_url'][:60]}...")
                                if "asin" in result:
                                    print(f"     ASIN: {result['asin']}")
                                if "name" in result:
                                    print(f"     Name: {result['name'][:50]}...")
                                if "price" in result:
                                    print(f"     Price: {result['price']}")
                break
            elif status == "FAILURE":
                print(f"\n❌ Task FAILED")
                print(f"Response: {json.dumps(data, indent=2)}")
                break
            else:
                print(f"    Still processing...")
                time.sleep(5)
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            break
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        break

if time.time() - start_time >= max_wait:
    print(f"\n⏱️  Timeout after {max_wait}s")
    print(f"Task may still be processing in Scrapula dashboard")

print(f"\n{'=' * 70}")
