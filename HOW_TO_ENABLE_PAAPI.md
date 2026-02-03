# How to Enable Amazon Product Advertising API (PA-API)

## Current Status: ❌ 403 Forbidden

Your PA-API credentials return "403 Forbidden" across all marketplaces, indicating **PA-API access is not activated**.

---

## What is PA-API?

PA-API (Product Advertising API) provides real-time product data from Amazon:
- Current prices
- Stock availability  
- Product images
- Customer ratings
- List prices (PVP)

**Note**: PA-API requires **separate approval** from Amazon Associates program.

---

## Step-by-Step: Enable PA-API

### Step 1: Check PA-API Eligibility

**Requirements:**
- ✅ Active Amazon Associates account
- ✅ At least 3 qualifying sales in the last 180 days (for some regions)
- ✅ Approved website/app

**Check your eligibility:**
1. Go to: https://affiliate-program.amazon.es/home
2. Log in to your Associates account
3. Navigate to **Tools** → **Product Advertising API**

### Step 2: Apply for PA-API Access

**For Amazon.es (Spain):**
1. **Go to**: https://affiliate-program.amazon.es/assoc_credentials/home
2. Click **"Product Advertising API"** in the menu
3. **Apply for PA-API access**
   - Fill out application form
   - Describe your use case (e.g., "WhatsApp deal publishing bot")
   - Provide details about your application

**Wait for approval:** 1-3 business days

### Step 3: Create PA-API Credentials

Once approved:

1. **Go to**: https://webservices.amazon.es/paapi5/documentation/register-for-pa-api.html
2. Sign in with your **Amazon Associates account**
3. Click **"Add a new application"**
4. **Fill out the form:**
   - Application Name: "DealBot"
   - Description: "Deal publishing application"
5. **Generate credentials:**
   - Access Key (starts with "AKPA...")
   - Secret Key (long alphanumeric string)

**Important:** Save these credentials immediately - Secret Key is only shown once!

### Step 4: Link Associate Tag to PA-API

**Critical:** Your associate tag must be linked to PA-API credentials:

1. When creating PA-API application, select your **associate tag**: `retroshell00-20`
2. Or in Associates Central:
   - Go to **Manage Your Tracking IDs**
   - Find `retroshell00-20`
   - Enable PA-API for this tag

### Step 5: Update DealBot Configuration

Update `.env` file with new credentials:
```bash
cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"

# Edit .env file
nano .env
```

Add your credentials:
```
AMAZON_PAAPI_ACCESS_KEY=AKPA_YOUR_NEW_KEY
AMAZON_PAAPI_SECRET_KEY=your_new_secret_key_here
AMAZON_ASSOCIATE_TAG=retroshell00-20
```

### Step 6: Test PA-API

Run the diagnostic test:
```bash
./venv/bin/python3 test_api_detailed.py
```

**Success looks like:**
```
✅ SUCCESS! API returned data:
   Title: Helly Hansen Dubliner...
   Price: €63.14
   Availability: Now
```

**Failure looks like:**
```
❌ ERROR: Request failed: Forbidden
```

---

## Common Issues & Solutions

### Issue 1: "Not eligible for PA-API"

**Cause:** Insufficient qualifying sales

**Solutions:**
- Generate 3 sales through your affiliate links
- Wait 180 days from sales
- Contact Amazon Associates support

### Issue 2: "403 Forbidden" after approval

**Causes:**
- Associate tag not linked to PA-API credentials
- Credentials for wrong marketplace
- Credentials not fully activated (can take 24 hours)

**Solutions:**
1. Verify tag `retroshell00-20` is linked to PA-API
2. Ensure credentials are for amazon.**es** (not .com, .co.uk, etc.)
3. Wait 24 hours after credential creation
4. Regenerate credentials if issue persists

### Issue 3: "Invalid signature"

**Cause:** Wrong Access Key or Secret Key

**Solution:**
- Double-check credentials (no extra spaces/characters)
- Regenerate credentials at Associates Central

### Issue 4: Works in US but not ES

**Cause:** Credentials are for wrong marketplace

**Solution:**
- Create separate credentials for each marketplace
- For amazon.es, register at: https://afiliados.amazon.es
- Use marketplace-specific credentials

---

## Alternative: Continue Without PA-API

Your DealBot **already works without PA-API** using the fallback system:

### Current Setup (Working ✅):
- ✅ Prices from TXT file
- ✅ Affiliate tag applied
- ✅ Can publish deals
- ⚠️ Status: "Price Check" (using fallback)

### What You're Missing:
- ❌ Real-time price validation
- ❌ Stock availability checks
- ❌ Product images from Amazon
- ❌ Customer ratings from Amazon

### When to Enable PA-API:
- **Now**: If you want real-time Amazon data
- **Later**: If fallback prices work fine for your workflow
- **Never**: If you only trust your own TXT file data

---

## Verification Checklist

Before contacting Amazon support, verify:

- [ ] Amazon Associates account is **active** and **approved**
- [ ] Associate tag `retroshell00-20` exists in your account
- [ ] You have **at least 3 sales** in the last 180 days (if required)
- [ ] You've **applied for PA-API access** (separate from Associates)
- [ ] PA-API application was **approved** (check email)
- [ ] You've **created PA-API credentials** (Access Key + Secret Key)
- [ ] Associate tag is **linked** to PA-API credentials
- [ ] Credentials are for **amazon.es** marketplace
- [ ] Credentials are **correctly copied** to `.env` file (no spaces)
- [ ] You've waited **24 hours** since credential creation

---

## Contact Amazon Support

If still not working after following all steps:

**Amazon Associates Support:**
- Email: associates-es@amazon.es
- Phone: Check Associates Central for local number
- Form: https://affiliate-program.amazon.es/help/contact

**Provide to support:**
- Your associate tag: `retroshell00-20`
- Error message: "403 Forbidden"
- What you've tried: "Applied for PA-API, created credentials, but getting 403 error"

---

## Summary

| Step | Status | Next Action |
|------|--------|-------------|
| Amazon Associates Account | ✅ Active | - |
| Associate Tag | ✅ `retroshell00-20` | - |
| PA-API Access | ❌ Not approved | Apply at Associates Central |
| PA-API Credentials | ❌ Invalid/Not linked | Create after approval |
| DealBot App | ✅ Working | Using TXT fallback |

**Immediate next step:**
1. Go to: https://affiliate-program.amazon.es/assoc_credentials/home
2. Apply for PA-API access
3. Wait for approval email
4. Generate new credentials
5. Link `retroshell00-20` tag to PA-API

---

**Note**: While PA-API is being approved, your DealBot **continues to work** using prices from TXT files. No functionality is lost!

**Current Status**: November 13, 2025 at 8:35 PM  
**DealBot Status**: ✅ Working with fallback prices  
**PA-API Status**: ⏳ Requires approval from Amazon
