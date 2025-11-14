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
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com --quiet

# Build frontend
echo "🔨 Building frontend..."
cd web_ui/frontend
npm install
npm run build
cd ../..

# Build and push Docker image
echo "🐳 Building Docker image..."
gcloud builds submit --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 10 \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_CLOUD_LOCATION=${REGION},GOOGLE_GENAI_USE_VERTEXAI=true"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo "📊 Health check: $SERVICE_URL/health"
echo ""

