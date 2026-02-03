# DealBot Cloud - Quick Start Guide

Transform your DealBot from manual desktop app to fully autonomous 24/7 cloud service!

---

## What Changed?

**Before:**
- ❌ Manual operation - you click files
- ❌ Desktop only - needs macOS
- ❌ Single-use - run when you remember

**After:**
- ✅ Fully autonomous - runs automatically
- ✅ Cloud-based - runs anywhere 24/7
- ✅ Scheduled - 6am & 6pm Spain time
- ✅ Smart filtering - only good deals published
- ✅ Status updates - know it's working
- ✅ Google Drive sync - auto-fetches new deals
- ✅ Free tier eligible - costs <$1/month

---

## 🚀 Quick Deploy (5 Steps)

### 1. Test Locally First

```bash
# Install dependencies
pip install -r requirements.txt

# Test with local files (no Google Drive)
python run_daemon.py --once --source-dir "/Users/m4owen/Library/CloudStorage/GoogleDrive-gunn0r@gmail.com/Shared drives/01.Player Clothing Team Drive/02. RetroShell/13. Articles and Data/09. Feed Finder/amazon_deals"
```

This will:
- Parse deals from the directory
- Apply smart filtering rules
- Publish qualifying deals to WhatsApp
- Send a status update

### 2. Set Up Google Drive API

Follow **Part 1** of `SETUP_GOOGLE_CLOUD.md`:
1. Create Google Cloud project
2. Enable Google Drive API
3. Create service account
4. Download credentials JSON
5. Share folder with service account
6. Get folder ID

### 3. Test with Google Drive

```bash
# Set credentials path
export GOOGLE_DRIVE_CREDENTIALS="/path/to/your-service-account-key.json"

# Test with Google Drive sync
python run_daemon.py --once --use-gdrive --folder-id "YOUR_FOLDER_ID"
```

### 4. Deploy to Cloud Run

```bash
# Set your project ID
export GCP_PROJECT_ID=your-project-id

# Deploy!
./deploy.sh
```

### 5. Set Up Scheduled Runs

Follow **Part 3** of `SETUP_GOOGLE_CLOUD.md` to create Cloud Scheduler jobs for 6am and 6pm.

---

## 📊 Smart Filtering Rules

Your new system only publishes deals that meet these criteria:

### ✅ Will Publish If:

1. **Price is cheaper** than TXT file
2. **Price within 10%** of TXT price AND discount is close (-10%)
3. **Discount ≥ 20%** from Amazon PVP
4. **Under €20** with at least 15% discount (impulse buys)

### ❌ Will Filter Out If:

1. **Out of stock** or unavailable
2. **Price increased** beyond 10% tolerance
3. **Discount dropped** significantly (>10% from TXT)
4. **No good deal criteria** met

---

## 📱 Status Updates

After each run, you'll receive a WhatsApp message like:

```
🤖 DealBot Status Update

✅ Processing complete
📁 Files processed: 2
🔍 Deals found: 29
📤 Published: 12
⏭️  Filtered: 17
🕐 18:05 CET
```

---

## 🔧 Local Testing Modes

### Test Once (No Schedule)
```bash
python run_daemon.py --once
```

### Test with Local Files
```bash
python run_daemon.py --once --source-dir "/path/to/deals"
```

### Test with Google Drive
```bash
export GOOGLE_DRIVE_CREDENTIALS="/path/to/credentials.json"
python run_daemon.py --once --use-gdrive --folder-id "YOUR_ID"
```

### Run Internal Scheduler (6am/6pm)
```bash
python run_daemon.py
# Will wait and run automatically at scheduled times
```

### Run HTTP Server (Cloud Run Mode)
```bash
export PORT=8080
python run_daemon.py --http
# Access http://localhost:8080 to trigger processing
```

---

## 📁 New Files Added

```
dealbot/
├── daemon.py           # Core autonomous processing logic
├── scheduler.py        # 6am/6pm scheduling
├── http_server.py      # Cloud Run HTTP endpoint
└── services/
    └── gdrive.py       # Google Drive API integration

run_daemon.py           # Main entry point
requirements.txt        # Updated dependencies
Dockerfile              # Container image
deploy.sh               # Deployment script
cloud-run.yaml          # Cloud Run config
SETUP_GOOGLE_CLOUD.md   # Full setup guide
QUICKSTART.md           # This file
```

---

## 🐛 Troubleshooting

### "No deals found"
- Check Google Drive folder has .txt files
- Verify folder is shared with service account
- Look at logs for parsing errors

### "Out of stock" for all deals
- Amazon PA-API might be rate-limited
- Check API credentials are valid
- Try again in a few minutes

### "Price increased beyond tolerance"
- Deal prices changed since TXT was created
- This is working correctly - prevents bad deals
- TXT file might be outdated

### Local test works, Cloud fails
- Check all secrets are created in Secret Manager
- Verify service account has Drive access
- Check Cloud Run logs: `gcloud run logs read dealbot-daemon`

---

## 💰 Cost Breakdown

**Google Cloud Run:**
- 2 runs/day × 30 days = 60 requests/month
- Free tier: 2 million requests/month
- **Cost: $0**

**Cloud Scheduler:**
- 2 jobs (morning + evening)
- Free tier: 3 jobs
- **Cost: $0**

**Secret Manager:**
- 7 secrets stored
- Free tier: 6 secrets
- **Cost: ~$0.06/month** (1 extra secret)

**Total: Under $1/month** (essentially free!)

---

## 🎯 Next Steps

1. ✅ Test locally with `--once` flag
2. ✅ Set up Google Drive API credentials
3. ✅ Test Google Drive sync
4. ✅ Deploy to Cloud Run
5. ✅ Configure Cloud Scheduler
6. ✅ Monitor first automatic run
7. ✅ Check WhatsApp for status updates

---

## 📞 Support

- **Full Guide:** `SETUP_GOOGLE_CLOUD.md`
- **Logs:** `gcloud run logs read dealbot-daemon --region=europe-west1`
- **Contact:** gunn0r@gmail.com

---

**Your DealBot is now a 24/7 autonomous deal-finding machine!** 🤖✨
