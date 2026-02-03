#!/bin/bash
# Complete DealBot Deployment Script
# Run this to deploy DealBot to Google Cloud

set -e

echo "=========================================="
echo "🚀 DealBot Cloud Deployment"
echo "=========================================="
echo ""

# Configuration
PROJECT_ID="dealbot-478714"
REGION="europe-west1"
SERVICE_NAME="dealbot-daemon"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker not found"
    echo "Install from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Prerequisites checked"
echo ""

# Step 1: Set project and enable APIs
echo "📋 Step 1: Configuring Google Cloud Project..."
gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com
echo "✅ APIs enabled"
echo ""

# Step 2: Create secrets
echo "🔐 Step 2: Creating secrets in Secret Manager..."

# Check if secrets exist, create only if missing
create_secret_if_missing() {
    local secret_name=$1
    local secret_value=$2

    if gcloud secrets describe $secret_name --project=$PROJECT_ID &>/dev/null; then
        echo "   ⏭️  Secret $secret_name already exists"
    else
        echo -n "$secret_value" | gcloud secrets create $secret_name \
            --data-file=- \
            --project=$PROJECT_ID
        echo "   ✅ Created secret: $secret_name"
    fi
}

# Read from .env file
echo "   Reading credentials from .env..."
WHAPI_KEY=$(grep WHAPI_API_KEY .env | cut -d '=' -f2)
PAAPI_ACCESS=$(grep AMAZON_PAAPI_ACCESS_KEY .env | cut -d '=' -f2)
PAAPI_SECRET=$(grep AMAZON_PAAPI_SECRET_KEY .env | cut -d '=' -f2)
ASSOCIATE_TAG=$(grep AMAZON_ASSOCIATE_TAG .env | cut -d '=' -f2)
SCRAPULA_KEY=$(grep SCRAPULA_API_KEY .env | cut -d '=' -f2)
GDRIVE_FOLDER=$(grep GOOGLE_DRIVE_FOLDER_ID .env | cut -d '=' -f2)

create_secret_if_missing "whapi-api-key" "$WHAPI_KEY"
create_secret_if_missing "amazon-paapi-access-key" "$PAAPI_ACCESS"
create_secret_if_missing "amazon-paapi-secret-key" "$PAAPI_SECRET"
create_secret_if_missing "amazon-associate-tag" "$ASSOCIATE_TAG"
create_secret_if_missing "scrapula-api-key" "$SCRAPULA_KEY"
create_secret_if_missing "gdrive-folder-id" "$GDRIVE_FOLDER"

# Google Drive credentials file
if gcloud secrets describe gdrive-credentials --project=$PROJECT_ID &>/dev/null; then
    echo "   ⏭️  Secret gdrive-credentials already exists"
else
    gcloud secrets create gdrive-credentials \
        --data-file="dealbot-478714-dbfd05501682.json" \
        --project=$PROJECT_ID
    echo "   ✅ Created secret: gdrive-credentials"
fi

echo "✅ Secrets created"
echo ""

# Step 2.5: Grant secret access to Cloud Run service account
echo "🔐 Step 2.5: Granting secret access permissions..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

echo "✅ Permissions granted to ${COMPUTE_SA}"
echo ""

# Step 3: Build Docker image
echo "🐳 Step 3: Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .
echo "✅ Image built"
echo ""

# Step 4: Push to GCR
echo "📤 Step 4: Pushing image to Google Container Registry..."
docker push ${IMAGE_NAME}:latest
echo "✅ Image pushed"
echo ""

# Step 5: Deploy to Cloud Run
echo "☁️  Step 5: Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region $REGION \
    --memory 1Gi \
    --cpu 1 \
    --timeout 3600 \
    --no-allow-unauthenticated \
    --set-env-vars "TZ=Europe/Madrid" \
    --set-secrets "WHAPI_API_KEY=whapi-api-key:latest,AMAZON_PAAPI_ACCESS_KEY=amazon-paapi-access-key:latest,AMAZON_PAAPI_SECRET_KEY=amazon-paapi-secret-key:latest,AMAZON_ASSOCIATE_TAG=amazon-associate-tag:latest,SCRAPULA_API_KEY=scrapula-api-key:latest,GOOGLE_DRIVE_FOLDER_ID=gdrive-folder-id:latest,GOOGLE_DRIVE_CREDENTIALS=gdrive-credentials:latest" \
    --project=$PROJECT_ID

echo "✅ Deployed to Cloud Run"
echo ""

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --project=$PROJECT_ID \
    --format 'value(status.url)')

echo "📍 Service URL: $SERVICE_URL"
echo ""

# Step 6: Grant invoker permission
echo "🔐 Step 6: Granting Cloud Run invoker permission..."
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --region=$REGION \
    --member=serviceAccount:dealbot-service@dealbot-478714.iam.gserviceaccount.com \
    --role=roles/run.invoker \
    --project=$PROJECT_ID
echo "✅ Permissions granted"
echo ""

# Step 7: Create Cloud Scheduler jobs
echo "⏰ Step 7: Creating Cloud Scheduler jobs..."

# Morning job (6am)
if gcloud scheduler jobs describe dealbot-morning --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo "   ⏭️  Morning job already exists"
else
    gcloud scheduler jobs create http dealbot-morning \
        --location=$REGION \
        --schedule="0 6 * * *" \
        --time-zone="Europe/Madrid" \
        --uri="$SERVICE_URL" \
        --http-method=GET \
        --oidc-service-account-email=dealbot-service@dealbot-478714.iam.gserviceaccount.com \
        --description="DealBot morning run at 6am CET" \
        --project=$PROJECT_ID
    echo "   ✅ Created morning job (6am CET)"
fi

# Evening job (6pm)
if gcloud scheduler jobs describe dealbot-evening --location=$REGION --project=$PROJECT_ID &>/dev/null; then
    echo "   ⏭️  Evening job already exists"
else
    gcloud scheduler jobs create http dealbot-evening \
        --location=$REGION \
        --schedule="0 18 * * *" \
        --time-zone="Europe/Madrid" \
        --uri="$SERVICE_URL" \
        --http-method=GET \
        --oidc-service-account-email=dealbot-service@dealbot-478714.iam.gserviceaccount.com \
        --description="DealBot evening run at 6pm CET" \
        --project=$PROJECT_ID
    echo "   ✅ Created evening job (6pm CET)"
fi

echo "✅ Scheduler jobs created"
echo ""

echo "=========================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "✅ Service deployed: $SERVICE_NAME"
echo "✅ Region: $REGION"
echo "✅ URL: $SERVICE_URL"
echo "✅ Schedule: 6am & 6pm CET daily"
echo ""
echo "📊 Next steps:"
echo "1. Test deployment:"
echo "   gcloud scheduler jobs run dealbot-morning --location=$REGION --project=$PROJECT_ID"
echo ""
echo "2. View logs:"
echo "   gcloud run logs tail $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"
echo ""
echo "3. Monitor status: Check WhatsApp for status updates"
echo ""
