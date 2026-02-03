#!/usr/bin/env python3
"""Comprehensive Scrapula troubleshooting."""
import requests
import json
import time

api_key = "ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA"
base_url = "https://api.datapipeplatform.cloud"

print("=" * 70)
print("SCRAPULA TROUBLESHOOTING")
print("=" * 70)

# Test 1: Check account
print("\n1. CHECKING ACCOUNT...")
try:
    r = requests.get(f"{base_url}/profile/balance", headers={"X-API-KEY": api_key}, timeout=10)
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Account valid")
        print(f"   Balance: ${data.get('balance', 0)}")
        print(f"   Status: {data.get('account_status', 'unknown')}")
    else:
        print(f"   ❌ Error: {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: List recent tasks
print("\n2. CHECKING RECENT TASKS...")
try:
    r = requests.get(f"{base_url}/tasks", headers={"X-API-KEY": api_key}, timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        tasks = r.json()
        print(f"   Response: {json.dumps(tasks, indent=2)[:500]}")
    else:
        print(f"   Response: {r.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Try simplest possible task
print("\n3. CREATING MINIMAL TEST TASK...")
simple_payload = {
    "service_name": "amazon_products_service_v2",
    "queries": ["https://www.amazon.es/dp/B06XGWGGD8"]
}
print(f"   Payload: {json.dumps(simple_payload, indent=2)}")

try:
    r = requests.post(
        f"{base_url}/tasks",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=simple_payload,
        timeout=10
    )
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.text}")
    
    if r.status_code == 200:
        data = r.json()
        task_id = data.get("id")
        print(f"\n   ✅ Task created: {task_id}")
        
        # Poll for 2 minutes max
        print(f"\n4. POLLING TASK (2 minutes max)...")
        start = time.time()
        while time.time() - start < 120:
            time.sleep(10)
            elapsed = int(time.time() - start)
            
            r2 = requests.get(
                f"{base_url}/tasks/{task_id}",
                headers={"X-API-KEY": api_key},
                timeout=10
            )
            
            print(f"   [{elapsed}s] Status code: {r2.status_code}")
            print(f"   [{elapsed}s] Response: {r2.text[:200]}")
            
            if r2.status_code == 200 and r2.text != "{}":
                result = r2.json()
                status = result.get("status", "UNKNOWN")
                print(f"   [{elapsed}s] Task status: {status}")
                
                if status in ["SUCCESS", "FAILURE"]:
                    print(f"\n   FINAL RESPONSE:")
                    print(json.dumps(result, indent=2)[:1000])
                    break
            
            if r2.text == "{}":
                print(f"   [{elapsed}s] ⚠️ Empty response - task may have expired")
    else:
        print(f"   ❌ Failed to create task")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
print("TROUBLESHOOTING COMPLETE")
print("=" * 70)
