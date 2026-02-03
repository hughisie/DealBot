#!/usr/bin/env python3
"""Test PA-API with direct HTTP request to see exact error."""

import hmac
import hashlib
import base64
from datetime import datetime
import requests
import json

def make_direct_paapi_request():
    """Make a direct PA-API request to see the exact error response."""
    
    print("=" * 70)
    print("Direct PA-API HTTP Request Test")
    print("=" * 70)
    
    # Credentials
    access_key = "AKPAQ1JMQD1763062287"
    secret_key = "TTBuZCqH54WjKyrPK6l1otcoMmnyrDvwLUSk5WZl"
    partner_tag = "retroshell00-20"
    
    # PA-API endpoint for US
    host = "webservices.amazon.com"
    region = "us-east-1"
    endpoint = f"https://{host}/paapi5/getitems"
    
    # Request payload
    payload = {
        "ItemIds": ["B08N5WRWNW"],
        "Resources": [
            "ItemInfo.Title",
            "Offers.Listings.Price"
        ],
        "PartnerTag": partner_tag,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.com"
    }
    
    # Timestamp
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    datestamp = datetime.utcnow().strftime('%Y%m%d')
    
    print(f"\nRequest Details:")
    print(f"  Endpoint: {endpoint}")
    print(f"  Access Key: {access_key}")
    print(f"  Partner Tag: {partner_tag}")
    print(f"  Region: {region}")
    print(f"  Timestamp: {timestamp}")
    
    # Headers
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'X-Amz-Date': timestamp,
        'X-Amz-Target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems',
        'Content-Encoding': 'amz-1.0',
        'Host': host
    }
    
    print(f"\nMaking request...")
    
    try:
        # Note: This won't work without proper AWS signature
        # But the error response will tell us what's wrong
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"\nResponse Body:")
        
        try:
            response_json = response.json()
            print(json.dumps(response_json, indent=2))
            
            # Check for specific error messages
            if "__type" in response_json:
                error_type = response_json["__type"]
                print(f"\n📋 Error Type: {error_type}")
                
                if "AccessDeniedException" in error_type:
                    print("   → This is an access/permissions error")
                    print("   → PA-API access may not be granted")
                elif "InvalidParameterException" in error_type:
                    print("   → Request parameters are invalid")
                elif "InvalidPartnerTag" in error_type:
                    print("   → Partner tag 'retroshell00-20' not recognized")
                    
        except:
            print(response.text)
            
    except Exception as e:
        print(f"❌ Request Error: {e}")
    
    print("\n" + "=" * 70)
    print("IMPORTANT CHECK:")
    print("=" * 70)
    print("\nIn your Amazon Associates account, verify:")
    print("1. Go to: https://affiliate-program.amazon.com/assoc_credentials/home")
    print("2. Find your 'Tracking IDs' section")
    print("3. Check if 'retroshell00-20' is listed there")
    print("4. Verify the tracking ID has PA-API access enabled")
    print("\nThe 'Store ID' you see might be different from the 'Tracking ID'")
    print("You may need to use a different tag format for PA-API")

if __name__ == "__main__":
    make_direct_paapi_request()
