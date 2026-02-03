# DealBot - Google Cloud Setup Guide

Complete guide for deploying DealBot as a 24/7 autonomous service on Google Cloud.

---

## Prerequisites

- Google Cloud account (free tier available)
- Google Drive with deal files
- Existing API keys (Whapi, Amazon PA-API, Scrapula)

---

## Part 1: Google Drive API Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **Select a project** → **New Project**
3. Name it `dealbot` (or your choice)
4. Click **Create**

### Step 2: Enable Google Drive API

1. In your project, go to **APIs & Services** → **Library**
2. Search for "Google Drive API"
3. Click **Enable**

### Step 3: Create Service Account

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **Service Account**
3. Fill in details:
   - **Name**: `dealbot-service`
   - **Description**: `DealBot service account for accessing Google Drive`
4. Click **Create and Continue**
5. Skip role assignment (click **Continue**)
6. Click **Done**

### Step 4: Create Service Account Key

1. Click on the service account you just created
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** format
5. Click **Create**
6. **Save the downloaded JSON file** - you'll need this!

### Step 5: Share Google Drive Folder

1. Open the Google Drive folder containing your deals:
   ```
   /Shared drives/01.Player Clothing Team Drive/02. RetroShell/13. Articles and Data/09. Feed Finder/amazon_deals
   ```

2. Click **Share** button

3. Add the service account email as a viewer:
   - Email will look like: `dealbot-service@your-project.iam.gserviceaccount.com`
   - You can find this in the service account details page
   - Set permission to **Viewer**

4. Click **Share**

### Step 6: Get Folder ID

1. Open the Google Drive folder in your browser
2. Look at the URL - it will look like:
   ```
   https://drive.google.com/drive/folders/1AbCdEfGhIjKlMnOpQrStUvWxYz
   ```
3. Copy the ID after `/folders/` (e.g., `1AbCdEfGhIjKlMnOpQrStUvWxYz`)
4. Save this - you'll need it for deployment!

---

## Part 2: Google Cloud Run Setup

### Step 1: Install Google Cloud CLI

**macOS:**
```bash
brew install google-cloud-sdk
```

**Or download from:** https://cloud.google.com/sdk/docs/install

### Step 2: Authenticate

```bash
gcloud auth login
gcloud config set project your-project-id
```

### Step 3: Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
```

### Step 4: Create Secrets

Store your API keys securely in Google Secret Manager:

```bash
# Whapi API Key
echo -n "your_whapi_key" | gcloud secrets create whapi-api-key --data-file=-

# Amazon PA-API Access Key
echo -n "your_access_key" | gcloud secrets create amazon-paapi-access-key --data-file=-

# Amazon PA-API Secret Key
echo -n "your_secret_key" | gcloud secrets create amazon-paapi-secret-key --data-file=-

# Amazon Associate Tag
echo -n "your_tag-21" | gcloud secrets create amazon-associate-tag --data-file=-

# Scrapula API Key
echo -n "your_scrapula_key" | gcloud secrets create scrapula-api-key --data-file=-

# Google Drive Folder ID
echo -n "your_folder_id" | gcloud secrets create gdrive-folder-id --data-file=-

# Google Drive Service Account Credentials (the JSON file)
gcloud secrets create gdrive-credentials --data-file=/path/to/your-service-account-key.json
```

### Step 5: Build and Deploy

```bash
# Set your project ID
export GCP_PROJECT_ID=your-project-id

# Make deploy script executable
chmod +x deploy.sh

# Deploy!
./deploy.sh
```

This will:
- Build the Docker image
- Push to Google Container Registry
- Deploy to Cloud Run
- Configure with 512MB memory and 1 CPU

---

## Part 3: Cloud Scheduler Setup (6am & 6pm Runs)

### Create Scheduler Jobs

**Morning job (6am CET):**
```bash
gcloud scheduler jobs create http dealbot-morning \
    --location=europe-west1 \
    --schedule="0 6 * * *" \
    --time-zone="Europe/Madrid" \
    --uri="https://dealbot-daemon-xxxxx-ew.a.run.app?trigger=scheduled" \
    --http-method=GET \
    --oidc-service-account-email=dealbot-service@your-project.iam.gserviceaccount.com \
    --description="DealBot morning run at 6am CET"
```

**Evening job (6pm CET):**
```bash
gcloud scheduler jobs create http dealbot-evening \
    --location=europe-west1 \
    --schedule="0 18 * * *" \
    --time-zone="Europe/Madrid" \
    --uri="https://dealbot-daemon-xxxxx-ew.a.run.app?trigger=scheduled" \
    --http-method=GET \
    --oidc-service-account-email=dealbot-service@your-project.iam.gserviceaccount.com \
    --description="DealBot evening run at 6pm CET"
```

**Note:** Replace `dealbot-daemon-xxxxx-ew.a.run.app` with your actual Cloud Run service URL.

### Verify Scheduler Jobs

```bash
gcloud scheduler jobs list --location=europe-west1
```

---

## Part 4: Update Cloud Run Configuration

The service needs to be triggered by Cloud Scheduler. Update `run_daemon.py` to handle HTTP requests:

```bash
# Grant Scheduler permission to invoke Cloud Run
gcloud run services add-iam-policy-binding dealbot-daemon \
    --region=europe-west1 \
    --member=serviceAccount:dealbot-service@your-project.iam.gserviceaccount.com \
    --role=roles/run.invoker
```

---

## Testing

### Test Locally

1. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys

   # Add Google Drive credentials path
   export GOOGLE_DRIVE_CREDENTIALS=/path/to/service-account-key.json
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run once (without Google Drive sync):**
   ```bash
   python run_daemon.py --once --source-dir "/path/to/local/deals"
   ```

4. **Run once (with Google Drive sync):**
   ```bash
   python run_daemon.py --once --use-gdrive --folder-id "your_folder_id"
   ```

5. **Run on schedule (continuous):**
   ```bash
   python run_daemon.py
   ```
   This will wait for 6am/6pm and run automatically.

### Test Cloud Deployment

```bash
# Trigger a manual run
gcloud scheduler jobs run dealbot-morning --location=europe-west1

# View logs
gcloud run logs read dealbot-daemon --region=europe-west1 --limit=50
```

---

## Monitoring

### View Logs

```bash
# Real-time logs
gcloud run logs tail dealbot-daemon --region=europe-west1

# Recent logs
gcloud run logs read dealbot-daemon --region=europe-west1 --limit=100
```

### Check Status

You'll receive WhatsApp status updates after each run showing:
- Files processed
- Deals found
- Deals published
- Deals filtered out
- Any errors

---

## Cost Estimate (Free Tier)

**Cloud Run:**
- Free tier: 2 million requests/month
- Your usage: ~60 requests/month (2 per day)
- **Cost: $0** (well within free tier)

**Cloud Scheduler:**
- Free tier: 3 jobs
- Your usage: 2 jobs
- **Cost: $0**

**Secret Manager:**
- Free tier: 6 active secrets
- Your usage: 7 secrets
- **Cost: ~$0.06/month** (1 secret above free tier)

**Total estimated cost: <$1/month**

---

## Troubleshooting

### Google Drive Access Issues

**Problem:** Service account can't access files

**Solution:**
1. Verify service account email is correct
2. Check folder is shared with service account (as Viewer)
3. Try accessing a regular folder (not Shared Drive) first to test
4. For Shared Drives, ensure domain-wide delegation if required

### Cloud Run Timeout

**Problem:** Processing takes too long

**Solution:**
- Increase timeout: `--timeout 3600` (already set)
- Reduce batch size in code
- Split into multiple runs

### Secrets Not Found

**Problem:** Environment variables not available

**Solution:**
```bash
# List secrets
gcloud secrets list

# Verify secret content (without exposing value)
gcloud secrets describe whapi-api-key

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding SECRET_NAME \
    --member=serviceAccount:SERVICE_ACCOUNT_EMAIL \
    --role=roles/secretmanager.secretAccessor
```

---

## Updating the Service

### Deploy New Version

```bash
# Make your code changes, then:
./deploy.sh
```

### Update Secrets

```bash
# Update a secret
echo -n "new_value" | gcloud secrets versions add SECRET_NAME --data-file=-
```

### View Service Details

```bash
gcloud run services describe dealbot-daemon --region=europe-west1
```

---

## Next Steps

1. ✅ Complete Google Drive API setup
2. ✅ Deploy to Cloud Run
3. ✅ Set up Cloud Scheduler
4. ✅ Test with a manual trigger
5. ✅ Monitor first automatic run (6am or 6pm)
6. ✅ Check WhatsApp for status updates

---

## Support

For issues or questions:
- Check logs: `gcloud run logs read dealbot-daemon`
- Review [Cloud Run documentation](https://cloud.google.com/run/docs)
- Contact: gunn0r@gmail.com
