# Scrapula API Integration Guide

## Current Status

✅ **API Key configured:** `ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA`  
⚠️ **Need API documentation** to complete integration

---

## What We Need From Scrapula Documentation

To complete the integration, we need to find these details from the Scrapula API docs:

### 1. API Endpoint URL

**Current guess:** `https://datapipeplatform.cloud/api/scrape`  
**Need to verify:** What's the exact endpoint for Amazon product scraping?

Examples we need to check:
- `/api/scrape`
- `/api/amazon/product`
- `/api/v1/scrape`
- Something else?

### 2. Authentication Format

**Current guess:** `Authorization: Bearer YOUR_API_KEY`  
**Need to verify:** How should the API key be sent?

Common patterns:
- `Authorization: Bearer API_KEY`
- `X-API-Key: API_KEY`
- `api-key: API_KEY`
- In query parameter: `?api_key=API_KEY`

### 3. Request Format

**Need to know:** What does a scrape request look like?

Example possibilities:
```json
// Option A: POST with URL
{
  "url": "https://www.amazon.es/dp/B06XGWGGD8"
}

// Option B: POST with ASIN
{
  "asin": "B06XGWGGD8",
  "marketplace": "es"
}

// Option C: GET with parameters
GET /api/scrape?asin=B06XGWGGD8&marketplace=es
```

### 4. Response Format

**Need to know:** What fields does Scrapula return?

Example response we need:
```json
{
  "title": "Product Name",
  "price": 63.14,
  "list_price": 170.00,  // PVP/original price
  "image": "https://...",
  "currency": "EUR",
  "availability": "In Stock"
}
```

**Field names to look for:**
- Title: `title`, `product_title`, `name`?
- Current Price: `price`, `current_price`, `sale_price`?
- List Price (PVP): `list_price`, `original_price`, `pvp`, `was_price`?
- Image: `image`, `image_url`, `main_image`?
- Availability: `availability`, `in_stock`, `stock_status`?

---

## How to Find This Information

### Step 1: Access Scrapula Dashboard

1. Go to: **https://datapipeplatform.cloud**
2. Log in with your account
3. Look for:
   - **"API Documentation"** tab/link
   - **"Docs"** section
   - **"API"** menu item
   - **"Getting Started"** guide

### Step 2: Find API Examples

Look for sections like:
- **Quick Start**
- **Example Requests**
- **API Reference**
- **Product Scraping**
- **Amazon Integration**

### Step 3: Copy Example Request

Find an example that shows:
```bash
curl https://api.example.com/scrape \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"url": "https://www.amazon.com/dp/ASIN"}'
```

### Step 4: Check Response Example

Find what a successful response looks like:
```json
{
  "success": true,
  "data": {
    "title": "...",
    "price": ...
  }
}
```

---

## Once You Have the Information

### Option 1: Provide Details to Me

Send me:
1. **Endpoint URL:** `https://...`
2. **Auth header format:** `Authorization: Bearer` or `X-API-Key`?
3. **Request example:** Copy-paste from docs
4. **Response example:** Copy-paste from docs

I'll update the code immediately.

### Option 2: Test Manually

Run this test with the correct format:

```bash
cd "/Users/m4owen/01. Apps/07. Windsurf/03. Claude/DealBot"

# Update this with correct endpoint and format
curl "https://datapipeplatform.cloud/api/CORRECT_ENDPOINT" \
  -H "Authorization: Bearer ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.amazon.es/dp/B06XGWGGD8"}' \
  | jq .
```

If that works, share the output!

---

## What I've Already Created

✅ **Scrapula service:** `dealbot/services/scrapula.py`
- Template ready
- Needs API details filled in
- Marked with `# TODO:` comments

✅ **Test scripts:**
- `test_scrapula_api.py` - Basic endpoint testing
- `test_scrapula_detailed.py` - Detailed response inspection

---

## Alternative: Contact Scrapula Support

If documentation isn't clear:

**Email/Support:**
- Check https://datapipeplatform.cloud for support contact
- Ask for:
  - Amazon product scraping endpoint
  - Example request/response
  - Authentication header format

**Provide them:**
- Your API key
- What you're trying to do: "Scrape Amazon product price, PVP, and image"

---

## Next Steps

1. **Log into Scrapula dashboard** → Find API docs
2. **Copy example request** → Provide to me
3. **I'll update the code** → Test integration
4. **Update DealBot** → Replace PA-API with Scrapula
5. **Rebuild app** → Working with Scrapula!

---

## Expected Timeline

- **5 minutes:** Find API docs
- **10 minutes:** Update code with correct format
- **5 minutes:** Test and verify
- **5 minutes:** Integrate into DealBot
- **Total: ~25 minutes** to have Scrapula working!

---

**Status:** Ready to integrate as soon as we have the correct API format from Scrapula docs! 🚀
