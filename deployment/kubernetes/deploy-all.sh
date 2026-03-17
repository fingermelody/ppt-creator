#!/bin/bash

# Deploy frontend and backend to TKE
# Usage: bash deploy-all.sh

set -e

echo "======================================"
echo "Deploying PPT-RSD to TKE"
echo "======================================"

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Check docker
if ! command -v docker &> /dev/null; then
    echo "Error: docker is not installed"
    exit 1
fi

# Configuration
FRONTEND_IMAGE="ccr.ccs.tencentyun.com/ppt-rsd/frontend:latest"
BACKEND_IMAGE="ccr.ccs.tencentyun.com/ppt-rsd/backend:latest"

# Build and push backend
echo ""
echo "📦 Building backend image..."
cd backend
docker build -t "${BACKEND_IMAGE}" .
docker push "${BACKEND_IMAGE}"
cd ..

# Build and push frontend
echo ""
echo "📦 Building frontend image..."
cd frontend
docker build -t "${FRONTEND_IMAGE}" .
docker push "${FRONTEND_IMAGE}"
cd ..

# Deploy to Kubernetes
echo ""
echo "🚀 Deploying to Kubernetes..."
cd deployment/kubernetes

# Apply configurations
kubectl apply -f configmap.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f ingress.yaml

# Wait for deployments
echo ""
echo "⏳ Waiting for deployments..."
kubectl rollout status deployment/ppt-rsd-backend --timeout=300s
kubectl rollout status deployment/ppt-rsd-frontend --timeout=300s

# Show status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "Frontend: https://ppt.bottlepeace.com"
echo "Backend API: https://api.ppt.bottlepeace.com"
echo ""
kubectl get pods -l 'app in (ppt-rsd-backend,ppt-rsd-frontend)'
kubectl get ingress
