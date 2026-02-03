# Scrapula API - What We Found

## API Documentation Analyzed

**Base URL:** `https://api.datapipeplatform.com`  
**Authentication:** `X-API-KEY` header  
**Your API Key:** `ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA`

---

## How Scrapula API Works

### Task-Based Architecture

Scrapula uses an **async task system**:

1. **Create Task** → Returns task ID
2. **Poll for Results** → Check task status
3. **Get Results** → Fetch completed data

### Key Endpoints

```
POST /tasks              → Create scraping task
GET  /tasks/{taskId}     → Get task status & results
GET  /requests/{reqId}   → Get request results
DELETE /tasks/{taskId}   → Terminate task
```

---

## What We Need to Find

### Missing Information: Amazon Service Name

The documentation shows how to create tasks but doesn't specify the **service_name** for Amazon product scraping.

**Examples from docs:**
- Google Maps: `google_maps_service_v2`
- Google Reviews: `google_maps_reviews_service_v3`
- Amazon: `???` ← **Need this!**

### Where to Find It

**Option 1: Scrapula Dashboard**
1. Login to: https://datapipeplatform.cloud
2. Look for **"Services"** or **"Available Services"** section
3. Find Amazon product scraping service
4. Note the `service_name` (e.g., `amazon_product_service`, `amazon_scraper_v2`)

**Option 2: Create Task UI**
1. Go to dashboard
2. Click **"Create New Task"**
3. Select **"Amazon"** from service dropdown
4. Inspect the form or network requests to see the service_name being sent

**Option 3: Support/Examples**
1. Check if dashboard has **"Examples"** or **"API Examples"**
2. Look for Amazon product scraping example
3. Copy the service_name from the example

---

## API Structure (From Documentation)

### Create Task Request

```bash
curl -X POST "https://api.datapipeplatform.com/tasks" \
  -H "X-API-KEY: ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "AMAZON_SERVICE_NAME_HERE",
    "queries": ["B06XGWGGD8"],
    "settings": {
      "marketplace": "es"
    }
  }'
```

### Get Task Results

```bash
curl -X GET "https://api.datapipeplatform.com/tasks/TASK_ID" \
  -H "X-API-KEY: ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA"
```

Response:
```json
{
  "id": "TASK_ID",
  "status": "SUCCESS",
  "results": [
    {
      "name": "Product Title",
      "asin": "B06XGWGGD8",
      "price_parsed": 63.14,
      "currency": "€",
      "image_1": "https://...",
      ...
    }
  ]
}
```

---

## Integration Plan

### Once We Have the Service Name

```python
# 1. Create Task
response = requests.post(
    "https://api.datapipeplatform.com/tasks",
    headers={"X-API-KEY": api_key},
    json={
        "service_name": "amazon_product_service",  # ← Need this
        "queries": [asin],
        "settings": {"marketplace": "es"}
    }
)
task_id = response.json()["id"]

# 2. Wait for completion (poll)
while True:
    result = requests.get(
        f"https://api.datapipeplatform.com/tasks/{task_id}",
        headers={"X-API-KEY": api_key}
    ).json()
    
    if result["status"] == "SUCCESS":
        products = result["results"]
        break
    elif result["status"] == "FAILURE":
        # Handle error
        break
    
    time.sleep(2)  # Wait before polling again

# 3. Parse results
product_data = products[0]  # Get first result
```

---

## Alternative: Synchronous Endpoint?

**Some platforms offer sync endpoints for single products:**

Possible patterns to try:
```
GET  /amazon/product?asin=B06XGWGGD8&marketplace=es
POST /amazon/scrape {"asin": "B06XGWGGD8", "marketplace": "es"}
POST /scrape {"url": "https://www.amazon.es/dp/B06XGWGGD8"}
```

These might work directly without task polling.

---

## What to Check in Dashboard

### Look for these sections:

1. **Services List**
   - Available scraping services
   - Amazon product service name

2. **API Examples**
   - Code snippets
   - Service names for each platform

3. **Service Documentation**
   - Amazon-specific docs
   - Parameters and options

4. **Recent Tasks**
   - If you've used Amazon scraping before
   - Inspect the task to see service_name used

---

## Next Steps

### Step 1: Find Service Name
```
Login → Dashboard → Services → Amazon → Copy service_name
```

### Step 2: Test Task Creation
```bash
curl -X POST "https://api.datapipeplatform.com/tasks" \
  -H "X-API-KEY: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "FOUND_SERVICE_NAME",
    "queries": ["B06XGWGGD8"]
  }'
```

### Step 3: Check Results
```bash
curl -X GET "https://api.datapipeplatform.com/tasks/RETURNED_TASK_ID" \
  -H "X-API-KEY: YOUR_KEY"
```

If this returns product data matching the demo Excel structure, we're good to integrate!

---

## Summary

| What We Have | Status |
|--------------|--------|
| **API Base URL** | ✅ `https://api.datapipeplatform.com` |
| **Authentication** | ✅ `X-API-KEY` header |
| **Your API Key** | ✅ Have it |
| **API Structure** | ✅ Task-based (create → poll → results) |
| **Response Format** | ✅ Matches demo Excel |
| **Service Name** | ❌ **Need this for Amazon scraping** |

**Once you provide the Amazon service_name, I can complete the integration in 30 minutes!**

---

## Quick Reference

**Create Task:**
```
POST https://api.datapipeplatform.com/tasks
Header: X-API-KEY: ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA
Body: {"service_name": "???", "queries": ["ASIN"]}
```

**Get Results:**
```
GET https://api.datapipeplatform.com/tasks/{taskId}
Header: X-API-KEY: ZHAjMDk0ZmQ3NGVhNDQ3NDA3MmI3ZThiMWEwM2U1MzgwNmF8YjhkZWZkOTFmZA
```

**Find service_name in:** Dashboard → Services → Amazon
