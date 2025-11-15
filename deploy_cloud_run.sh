#!/bin/bash
# Quick deploy script for Cloud Run

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-japanese-coach-458816}
REGION=${GOOGLE_CLOUD_LOCATION:-us-central1}
SERVICE_NAME="medical-triage-agent"

echo "🚀 Deploying Medical Triage Agent to Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set gcloud project
export PATH="$HOME/google-cloud-sdk/bin:$PATH"
gcloud config set project $PROJECT_ID

# Enable APIs
echo "📦 Enabling required APIs..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com storage-component.googleapis.com --quiet

# Build frontend
echo "🔨 Building frontend..."
cd web_ui/frontend
npm install
npm run build
cd ../..

# Setup Chroma Cloud Storage bucket
CHROMA_BUCKET="${PROJECT_ID}-chroma-db"
echo "📦 Setting up Chroma Cloud Storage bucket: ${CHROMA_BUCKET}"
if ! gsutil ls -b gs://${CHROMA_BUCKET} &>/dev/null; then
    echo "Creating Chroma bucket..."
    gsutil mb -p ${PROJECT_ID} -l ${REGION} gs://${CHROMA_BUCKET}
    echo "✅ Chroma bucket created"
else
    echo "✅ Chroma bucket already exists"
fi

# Upload local Chroma DB to Cloud Storage if it exists
if [ -d "chroma_db" ] && [ "$(ls -A chroma_db 2>/dev/null)" ]; then
    echo "📤 Uploading local Chroma DB to Cloud Storage..."
    gsutil -m cp -r chroma_db/* gs://${CHROMA_BUCKET}/chroma_db/ || echo "⚠️  Warning: Failed to upload Chroma DB (will be initialized on first startup)"
else
    echo "ℹ️  No local Chroma DB found. Will be initialized on first container startup."
fi

# Build and push Docker image
echo "🐳 Building Docker image..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
echo "⚠️  Note: First startup may take 10-12 minutes for Chroma initialization"
echo "📝 Chroma DB will be auto-initialized on first startup (non-blocking)"
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --cpu-boost \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=true,CHROMA_BUCKET_NAME=${CHROMA_BUCKET}"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📊 Health check: $SERVICE_URL/health"
echo ""

