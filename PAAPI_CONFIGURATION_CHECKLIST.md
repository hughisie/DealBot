# PA-API Configuration Checklist

## Current Status: 403 Forbidden

Your credentials are formatted correctly, but PA-API is rejecting them. Let's verify the exact configuration.

---

## ✅ What's Correct

From your screenshot:
- ✅ PA-API Access Key created: `AKPAQ1JMQD1763062287`
- ✅ Access Key is "Active" status
- ✅ You have PA-API access in Amazon Associates dashboard
- ✅ Credentials are properly configured in DealBot `.env`

---

## ⚠️ Critical Check: Store ID vs Tracking ID

### The Issue:

Your screenshot shows:
```
StoreID: retroshell00-20
```

**BUT** PA-API might require a different **Tracking ID**!

### What You Need to Verify:

1. **Log into Amazon Associates:**
   - Go to: https://affiliate-program.amazon.com/home
   
2. **Find "Tracking IDs" Section:**
   - Click on "Tools" → "Tracking ID"
   - OR look for "Manage Your Tracking IDs"
   
3. **Check Your Tracking IDs:**
   - You may have MULTIPLE tracking IDs
   - Example: `retroshell00-20`, `retroshell-20`, `retroshell0020`, etc.
   
4. **Match Tracking ID to PA-API Credentials:**
   - The tracking ID must be **explicitly linked** to Access Key `AKPAQ1JMQD1763062287`
   - Look for a column or setting that shows which credentials each tracking ID uses

---

## 🔍 Most Common Issues (Check These)

### Issue #1: Wrong Tracking ID Format

**Problem:** StoreID ≠ Tracking ID

**Solution:**
- In Associates dashboard, find your actual Tracking IDs
- One might be: `retroshell-20` (without the 00)
- Or: `retroshell0020-20`
- Try each format in DealBot

**Test each format:**
```bash
# Edit .env and try different formats
AMAZON_ASSOCIATE_TAG=retroshell-20
# OR
AMAZON_ASSOCIATE_TAG=retroshell0020-20
# OR  
AMAZON_ASSOCIATE_TAG=retroshell00-21

# Then test:
./venv/bin/python3 test_api_detailed.py
```

---

### Issue #2: Tracking ID Not Linked to PA-API Credentials

**Problem:** The tracking ID exists but isn't authorized for PA-API

**Solution:**
1. Go to Associates dashboard
2. Navigate to PA-API credentials section
3. Find Access Key: `AKPAQ1JMQD1763062287`
4. Check which Tracking IDs are authorized for this key
5. Update DealBot to use the authorized tracking ID

---

### Issue #3: Wrong Marketplace

**Problem:** Credentials are for one marketplace (e.g., US) but you're accessing another (e.g., ES)

**Your Screenshot Shows:**
- Language: EN (English)
- This suggests amazon.**com** (US), not amazon.**es** (Spain)

**Solution:** Verify which marketplace your Associate account is registered with:
- If it's amazon.com → You need US products (not ES products)
- If it's amazon.co.uk → You need UK products
- If you want amazon.es → You need separate Spanish credentials

**Check Your Marketplace:**
```bash
# Test with your ACTUAL marketplace products
# If your account is US-based, test US products:
./venv/bin/python3 << 'EOF'
from amazon_paapi import AmazonApi

api = AmazonApi(
    key="AKPAQ1JMQD1763062287",
    secret="TTBuZCqH54WjKyrPK6l1otcoMmnyrDvwLUSk5WZl",
    tag="retroshell00-20",  # Or your actual tracking ID
    country="US"  # Match your Associates account marketplace
)

items = api.get_items(["B08N5WRWNW"])
if items:
    print("✅ WORKS! Your account is for US marketplace")
    print(f"Product: {items[0].item_info.title.display_value}")
else:
    print("❌ Still not working")
EOF
```

---

### Issue #4: PA-API Not Enabled for Tracking ID

**Problem:** PA-API approved for account but not for specific tracking ID

**Solution:**
1. In Associates dashboard → Tracking IDs
2. Each tracking ID has individual settings
3. Enable PA-API for the specific tracking ID you want to use
4. This might be a checkbox or toggle per tracking ID

---

## 📋 Step-by-Step Verification

### Step 1: Get Your Exact Tracking ID

```
Log into Amazon Associates
↓
Go to "Manage Tracking IDs" or "Tools" → "Tracking ID"
↓
Write down ALL tracking IDs you see:
  1. _________________
  2. _________________
  3. _________________
```

### Step 2: Find Which One Has PA-API Access

```
For each tracking ID above, check:
  □ Can be used with PA-API?
  □ Linked to Access Key: AKPAQ1JMQD1763062287?
  □ Approved/Active status?
```

### Step 3: Test Each Valid Tracking ID

For each tracking ID that has PA-API access:
```bash
# Update .env
nano .env
# Change: AMAZON_ASSOCIATE_TAG=your_tracking_id_here

# Test
./venv/bin/python3 test_api_detailed.py

# If it works, rebuild app:
./rebuild_app.sh
```

---

## 🎯 Most Likely Solution

Based on the 403 error pattern:

**The tracking ID `retroshell00-20` is not linked to Access Key `AKPAQ1JMQD1763062287`**

### How to Fix:

1. **Find the linked tracking ID:**
   - In Associates dashboard
   - Look at PA-API credentials section
   - Find what tracking ID is authorized for `AKPAQ1JMQD1763062287`

2. **Use that tracking ID:**
   ```bash
   # If the authorized ID is different, use it:
   AMAZON_ASSOCIATE_TAG=the_actual_authorized_id
   ```

3. **OR link your preferred tracking ID:**
   - In Associates dashboard
   - Edit PA-API credentials
   - Add/enable tracking ID `retroshell00-20` for this Access Key

---

## 🔧 Quick Test Script

Run this to test multiple possibilities:

```bash
cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"

# Create test script
cat > test_all_possibilities.py << 'EOFA'
from amazon_paapi import AmazonApi

access_key = "AKPAQ1JMQD1763062287"
secret_key = "TTBuZCqH54WjKyrPK6l1otcoMmnyrDvwLUSk5WZl"

# Try different combinations
tests = [
    ("retroshell00-20", "US"),
    ("retroshell-20", "US"),
    ("retroshell0020-20", "US"),
    ("retroshell00-21", "US"),
]

for tag, marketplace in tests:
    try:
        api = AmazonApi(key=access_key, secret=secret_key, tag=tag, country=marketplace)
        items = api.get_items(["B08N5WRWNW"])
        if items:
            print(f"✅ WORKS! Tag={tag}, Marketplace={marketplace}")
            break
    except Exception as e:
        print(f"❌ Failed: Tag={tag}, Marketplace={marketplace}")
EOFA

./venv/bin/python3 test_all_possibilities.py
```

---

## 📞 If Still Not Working

**Contact Amazon Associates Support with:**
- Access Key: `AKPAQ1JMQD1763062287`
- Question: "Which Tracking ID is linked to this Access Key?"
- Request: "Enable Tracking ID 'retroshell00-20' for PA-API if not already"

**Support:**
- US: https://affiliate-program.amazon.com/help/contact
- Email: After signing in to Associates Central

---

## Summary

| Check | Action |
|-------|--------|
| ✅ Credentials exist | Working |
| ✅ Formatted correctly | Working |
| ❌ Tracking ID mismatch | **VERIFY in dashboard** |
| ❌ Not linked to Access Key | **LINK in settings** |
| ❌ Wrong marketplace | **CHECK Associates country** |

**Next Step:** Log into Amazon Associates and verify the exact Tracking ID linked to your PA-API Access Key!
