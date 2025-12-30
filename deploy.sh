#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
REPO_NAME="brand-agent-repo"
BACKEND_IMAGE="gcr.io/$PROJECT_ID/brand-backend"
FRONTEND_IMAGE="gcr.io/$PROJECT_ID/brand-frontend"

echo "Using Project: $PROJECT_ID"

# 1. Build Backend
echo "Building Backend..."
docker build -t $BACKEND_IMAGE -f backend/Dockerfile backend/

# 2. Build Frontend
echo "Building Frontend..."
docker build -t $FRONTEND_IMAGE -f frontend/Dockerfile frontend/

# 3. Push Images
echo "Pushing Images..."
docker push $BACKEND_IMAGE
docker push $FRONTEND_IMAGE

# 4. Deploy Backend
echo "Deploying Backend..."
gcloud run deploy brand-backend \
    --image $BACKEND_IMAGE \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8000

# Get Backend URL
BACKEND_URL=$(gcloud run services describe brand-backend --platform managed --region $REGION --format 'value(status.url)')
echo "Backend URL: $BACKEND_URL"

# 5. Deploy Frontend
echo "Deploying Frontend..."
gcloud run deploy brand-frontend \
    --image $FRONTEND_IMAGE \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars NEXT_PUBLIC_API_URL=$BACKEND_URL \
    --port 3000

echo "Deployment Complete!"
