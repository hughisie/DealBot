#!/usr/bin/env python3
"""Verify credentials are correctly formatted."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "dealbot"))

from dealbot.utils.config import Config

def verify_credentials():
    """Verify all credential details."""
    
    print("=" * 70)
    print("Credential Verification")
    print("=" * 70)
    
    config = Config()
    
    access_key = config.require_env("AMAZON_PAAPI_ACCESS_KEY")
    secret_key = config.require_env("AMAZON_PAAPI_SECRET_KEY")
    associate_tag = config.affiliate_tag
    
    print(f"\nLoaded from .env:")
    print(f"  Access Key: {access_key}")
    print(f"  Secret Key: {secret_key}")
    print(f"  Associate Tag: {associate_tag}")
    
    print(f"\nCredential Analysis:")
    print(f"  Access Key length: {len(access_key)} chars")
    print(f"  Secret Key length: {len(secret_key)} chars")
    print(f"  Access Key format: {'✅ Valid (starts with AKPA)' if access_key.startswith('AKPA') else '❌ Invalid'}")
    print(f"  Secret Key format: {'✅ Valid (40 chars)' if len(secret_key) == 40 else f'⚠️  Unusual ({len(secret_key)} chars)'}")
    
    # Check for common issues
    issues = []
    
    if ' ' in access_key:
        issues.append("Access Key contains spaces")
    if ' ' in secret_key:
        issues.append("Secret Key contains spaces")
    if '\n' in access_key or '\n' in secret_key:
        issues.append("Credentials contain newline characters")
    
    if issues:
        print(f"\n⚠️  Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ No formatting issues detected")
    
    print(f"\nExpected from screenshot:")
    print(f"  Access Key: AKPA0DQU0S1763063154")
    print(f"  Secret Key: 8M+aK0sKmYBjxfQk2HL6KdEKuiJtX13xpQiNuDWL")
    
    # Compare
    expected_access = "AKPA0DQU0S1763063154"
    expected_secret = "8M+aK0sKmYBjxfQk2HL6KdEKuiJtX13xpQiNuDWL"
    
    print(f"\nComparison:")
    print(f"  Access Key matches: {'✅ Yes' if access_key == expected_access else '❌ No'}")
    print(f"  Secret Key matches: {'✅ Yes' if secret_key == expected_secret else '❌ No'}")
    
    if access_key != expected_access:
        print(f"\n  Expected: {expected_access}")
        print(f"  Got:      {access_key}")
    
    if secret_key != expected_secret:
        print(f"\n  Expected: {expected_secret}")
        print(f"  Got:      {secret_key}")

if __name__ == "__main__":
    verify_credentials()
