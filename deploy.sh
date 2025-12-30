#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
REPO_NAME="brand-agent-repo"
BACKEND_IMAGE="gcr.io/$PROJECT_ID/brand-backend"
FRONTEND_IMAGE="gcr.io/$PROJECT_ID/brand-frontend"

echo "Using Project: $PROJECT_ID"

# 1. Deploy Backend from Source
echo "Deploying Backend from source..."
gcloud run deploy brand-backend \
    --source backend/ \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8000 \
    --memory 2Gi \
    --cpu 1 \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION

# Get Backend URL
BACKEND_URL=$(gcloud run services describe brand-backend --platform managed --region $REGION --format 'value(status.url)')
echo "Backend URL: $BACKEND_URL"

# 4. Deploy Frontend from Source
echo "Deploying Frontend from source..."
gcloud run deploy brand-frontend \
    --source frontend/ \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars NEXT_PUBLIC_API_URL=$BACKEND_URL \
    --set-build-env-vars NEXT_PUBLIC_API_URL=$BACKEND_URL \
    --port 3000

echo "Deployment Complete!"
