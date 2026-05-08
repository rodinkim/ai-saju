#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

PROJECT_ID="saju-494604"
SERVICE_NAME="tojung-api"
REGION="asia-northeast3"
REPO_NAME="tojung-repo"
IMAGE_NAME="tojung-api"
IMAGE_TAG="${1:-latest}"

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"

SECRETS="ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,DATABASE_URL=DATABASE_URL:latest,JWT_SECRET_KEY=JWT_SECRET_KEY:latest,NAVER_CLIENT_ID=NAVER_CLIENT_ID:latest,NAVER_CLIENT_SECRET=NAVER_CLIENT_SECRET:latest,NAVER_REDIRECT_URI=NAVER_REDIRECT_URI:latest,KAKAO_CLIENT_ID=KAKAO_CLIENT_ID:latest,KAKAO_CLIENT_SECRET=KAKAO_CLIENT_SECRET:latest,KAKAO_REDIRECT_URI=KAKAO_REDIRECT_URI:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,GOOGLE_REDIRECT_URI=GOOGLE_REDIRECT_URI:latest,TOSS_CLIENT_KEY=TOSS_CLIENT_KEY:latest,TOSS_SECRET_KEY=TOSS_SECRET_KEY:latest,FRONTEND_URL=FRONTEND_URL:latest"

echo "[1/2] Build image: ${IMAGE_URI}"
gcloud builds submit "${ROOT_DIR}/backend" \
  --tag "${IMAGE_URI}" \
  --project "${PROJECT_ID}"

echo "[2/2] Deploy Cloud Run service: ${SERVICE_NAME}"
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE_URI}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --min-instances 1 \
  --timeout 300 \
  --add-cloudsql-instances "${PROJECT_ID}:${REGION}:tojung-db" \
  --set-secrets="${SECRETS}" \
  --project "${PROJECT_ID}"

echo "Deploy complete: ${SERVICE_NAME} (${REGION})"
