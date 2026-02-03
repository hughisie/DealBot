# 🔑 DealBot API Keys Setup Guide

## ❗ IMPORTANT: ACTION REQUIRED

Your DealBot app needs API keys to function. The `.env` file is currently set to placeholder values.

---

## 🚨 **Current Issue**

**Error**: "Required environment variable not set: AMAZON_PAAPI_ACCESS_KEY"

**Cause**: The `.env` file contains placeholder text instead of your actual API keys.

**Solution**: Fill in your actual API keys in the `.env` file.

---

## 📝 **TWO WAYS TO SET UP API KEYS**

### **Option 1: Interactive Setup (Recommended)**

Run this command and answer the prompts:

```bash
./setup_env.sh
```

This will guide you through entering all required keys.

### **Option 2: Manual Edit**

Edit `.env` file directly:

```bash
nano .env
# or
open -e .env
```

---

## 🔑 **REQUIRED API KEYS**

You mentioned these keys were working before. Please locate them and fill them in:

### **1. WhatsApp API (whapi.cloud)** ✅
```
WHAPI_API_KEY=your_actual_key_here
```
- Get from: https://whapi.cloud
- Format: Usually starts with `whapi_`

### **2. Amazon Product Advertising API** ✅
```
AMAZON_PAAPI_ACCESS_KEY=your_actual_access_key
AMAZON_PAAPI_SECRET_KEY=your_actual_secret_key  
AMAZON_ASSOCIATE_TAG=your_tag-21
```
- Get from: Amazon PA-API Dashboard
- ACCESS_KEY: Usually starts with `AKPA` or similar
- SECRET_KEY: Long alphanumeric string
- ASSOCIATE_TAG: Your Amazon Associate ID (ends with -21 or similar)

### **3. Short Link Provider** ✅

**Option A: Cloudflare (Recommended)**
```
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_API_TOKEN=your_api_token
```
- Get from: Cloudflare Dashboard → Workers → Account ID
- API Token: Create one with "Edit Workers" permissions

**Option B: Bitly**
```
BITLY_TOKEN=your_bitly_token
```
- Get from: Bitly Dashboard → Settings → API

### **4. Ratings Provider (Optional)**
```
KEEPA_API_KEY=your_keepa_key
```
- Get from: Keepa.com API Dashboard
- Optional but recommended for better deal ratings

---

## 📂 **WHERE IS THE .env FILE?**

Location: `/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot/.env`

Current content (needs your keys):
```bash
cat .env
```

---

## ✏️ **HOW TO FILL IN YOUR KEYS**

### **Step 1: Open .env**
```bash
cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"
open -e .env
```

### **Step 2: Replace Placeholders**

**Before (placeholders):**
```
WHAPI_API_KEY=your_whapi_key_here
AMAZON_PAAPI_ACCESS_KEY=your_amazon_access_key_here
```

**After (your actual keys):**
```
WHAPI_API_KEY=whapi_abc123def456ghi789
AMAZON_PAAPI_ACCESS_KEY=AKPA8WCRLR1761407306
```

### **Step 3: Save File**

Press `⌘ + S` to save, then close the editor.

### **Step 4: Verify**

```bash
cat .env | grep -v "^#" | grep "="
```

You should see your actual keys (not "your_key_here").

---

## 🚀 **AFTER FILLING IN KEYS**

### **Option 1: Rebuild App (Recommended)**

This will bundle your keys into the macOS app:

```bash
./rebuild_app.sh
```

### **Option 2: Test Locally First**

Test that keys work before building app:

```bash
make run
```

If it opens without errors, your keys are correct!

---

## 🔍 **WHERE TO FIND YOUR OLD KEYS**

You mentioned the app was "working perfectly" before. Check these locations:

### **1. Shell History**
```bash
history | grep -E "(export|AMAZON|WHAPI|CLOUDFLARE)"
```

### **2. Shell Profile**
```bash
cat ~/.zshrc | grep -E "(AMAZON|WHAPI|CLOUDFLARE)"
cat ~/.bash_profile | grep -E "(AMAZON|WHAPI|CLOUDFLARE)"
```

### **3. Environment Variables**
```bash
env | grep -E "(AMAZON|WHAPI|CLOUDFLARE)"
```

### **4. Backup .env Files**
```bash
find ~ -name ".env*" -type f 2>/dev/null | head -10
```

### **5. Git Stash**
```bash
git stash list
git stash show -p stash@{0} | grep -A 5 ".env"
```

---

## 🛠️ **TROUBLESHOOTING**

### **Error: "Required environment variable not set"**

**Check:**
1. `.env` file exists: `ls -la .env`
2. Contains actual keys (not placeholders): `cat .env`
3. No typos in key names
4. No extra spaces around `=`

**Format:**
```bash
✅ CORRECT: WHAPI_API_KEY=abc123
❌ WRONG:   WHAPI_API_KEY = abc123  (spaces around =)
❌ WRONG:   WHAPI_API_KEY=your_key_here  (placeholder)
```

### **Keys Not Loading in App**

The new code looks for `.env` in the same folder as `config.yaml`. When you run:

```bash
./rebuild_app.sh
```

It will automatically:
1. Copy `.env` to app Resources folder
2. Load it when app starts
3. Make keys available to the app

---

## 📋 **QUICK CHECKLIST**

Before rebuilding the app:

- [ ] `.env` file exists
- [ ] WHAPI_API_KEY filled in
- [ ] AMAZON_PAAPI_ACCESS_KEY filled in
- [ ] AMAZON_PAAPI_SECRET_KEY filled in
- [ ] AMAZON_ASSOCIATE_TAG filled in
- [ ] CLOUDFLARE keys OR BITLY_TOKEN filled in
- [ ] KEEPA_API_KEY filled in (optional)
- [ ] No "your_key_here" placeholders remain
- [ ] Saved the file

**Then run:**
```bash
./rebuild_app.sh
```

---

## 🎯 **EXAMPLE .env FILE**

Here's what a correctly filled `.env` looks like (with fake keys):

```bash
# DealBot Environment Variables

# WhatsApp API
WHAPI_API_KEY=whapi_1a2b3c4d5e6f7g8h9i0j

# Amazon PA-API
AMAZON_PAAPI_ACCESS_KEY=AKPA8WCRLR1761407306
AMAZON_PAAPI_SECRET_KEY=AbCdEf12GhIjKl34MnOpQr56StUvWx78YzAb90Cd
AMAZON_ASSOCIATE_TAG=yourstore-21

# Cloudflare
CLOUDFLARE_ACCOUNT_ID=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
CLOUDFLARE_API_TOKEN=AbCdEfGhIjKlMnOpQrStUvWxYz1234567890abcd

# Optional: Keepa
KEEPA_API_KEY=abc123def456ghi789jkl012mno345
```

---

## 🔐 **SECURITY NOTES**

1. **Never commit .env to git** - It's gitignored by default
2. **Keep keys private** - Don't share them
3. **Rotate if exposed** - Generate new keys if compromised
4. **Use environment-specific keys** - Different keys for dev/prod

---

## 🎉 **ONCE KEYS ARE SET**

1. ✅ App will launch without errors
2. ✅ Can load and process deals
3. ✅ Can publish to WhatsApp
4. ✅ All features will work

---

## 📞 **NEED HELP?**

### **Can't find your old keys?**

You'll need to:
1. Log into each service (WhatsApp API, Amazon PA-API, Cloudflare)
2. Regenerate API keys
3. Update `.env` with new keys

### **Keys not working?**

Run a test:
```bash
# Test with local environment
source .env
echo "WHAPI: ${WHAPI_API_KEY}"
echo "Amazon: ${AMAZON_PAAPI_ACCESS_KEY}"

# Should show your actual keys, not placeholders
```

---

## 🚀 **FINAL STEPS**

1. **Fill in .env**: Edit file with your actual API keys
2. **Verify**: Check that keys are correct (no placeholders)
3. **Test locally** (optional): `make run`
4. **Rebuild app**: `./rebuild_app.sh`
5. **Launch**: Open from Launchpad

**The app will now work perfectly!** 🎊
