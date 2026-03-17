#!/bin/bash

# Quick build and push script for local development
# Usage: bash quick-build.sh [tag]

set -e

TAG=${1:-latest}
IMAGE_REGISTRY="ccr.ccs.tencentyun.com/ppt-rsd"
IMAGE_NAME="backend"
FULL_IMAGE="${IMAGE_REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "======================================"
echo "Building and pushing Docker image"
echo "Image: ${FULL_IMAGE}"
echo "======================================"

# Build
echo "📦 Building image..."
cd backend
docker build -t "${FULL_IMAGE}" .

# Push
echo "📤 Pushing image..."
docker push "${FULL_IMAGE}"

echo "✅ Done!"
echo ""
echo "To deploy, run:"
echo "  kubectl set image deployment/ppt-rsd-backend backend=${FULL_IMAGE}"
