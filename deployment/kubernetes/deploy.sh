#!/bin/bash

# PPT-RSD Kubernetes Deployment Script
# Usage: bash deploy.sh [action]

set -e

# Configuration
NAMESPACE="default"
IMAGE_REGISTRY="ccr.ccs.tencentyun.com/ppt-rsd"
IMAGE_NAME="backend"
IMAGE_TAG="${IMAGE_TAG:-latest}"
FULL_IMAGE="${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is installed
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    log_info "kubectl found: $(kubectl version --client --short 2>/dev/null || kubectl version --client 2>&1 | head -1)"
}

# Check if docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "docker is not installed. Please install docker first."
        exit 1
    fi
    log_info "docker found: $(docker --version)"
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    cd backend
    docker build -t "${FULL_IMAGE}" .
    cd ..
    log_info "Image built successfully: ${FULL_IMAGE}"
}

# Push Docker image to registry
push_image() {
    log_info "Pushing image to registry..."
    docker push "${FULL_IMAGE}"
    log_info "Image pushed successfully: ${FULL_IMAGE}"
}

# Deploy to Kubernetes
deploy_k8s() {
    log_info "Deploying to Kubernetes..."
    
    # Apply ConfigMap and Secret
    kubectl apply -f deployment/kubernetes/configmap.yaml
    
    # Apply Deployment
    kubectl apply -f deployment/kubernetes/backend-deployment.yaml
    
    # Apply Service and Ingress
    kubectl apply -f deployment/kubernetes/service-ingress.yaml
    
    log_info "Deployment completed!"
    
    # Show deployment status
    kubectl get pods -l app=ppt-rsd-backend
    kubectl get svc ppt-rsd-backend
    kubectl get ingress ppt-rsd-ingress
}

# Rollback deployment
rollback() {
    log_warn "Rolling back deployment..."
    kubectl rollout undo deployment/ppt-rsd-backend
    log_info "Rollback completed!"
}

# Check deployment status
status() {
    log_info "Checking deployment status..."
    echo ""
    echo "=== Pods ==="
    kubectl get pods -l app=ppt-rsd-backend
    echo ""
    echo "=== Services ==="
    kubectl get svc ppt-rsd-backend
    echo ""
    echo "=== Ingress ==="
    kubectl get ingress ppt-rsd-ingress
    echo ""
    echo "=== Logs (last 20 lines) ==="
    kubectl logs -l app=ppt-rsd-backend --tail=20
}

# Delete deployment
delete() {
    log_warn "Deleting deployment..."
    kubectl delete -f deployment/kubernetes/service-ingress.yaml --ignore-not-found
    kubectl delete -f deployment/kubernetes/backend-deployment.yaml --ignore-not-found
    kubectl delete -f deployment/kubernetes/configmap.yaml --ignore-not-found
    log_info "Deployment deleted!"
}

# Main function
main() {
    local action="${1:-help}"
    
    case "$action" in
        build)
            check_docker
            build_image
            ;;
        push)
            check_docker
            push_image
            ;;
        deploy)
            check_kubectl
            deploy_k8s
            ;;
        all)
            check_docker
            check_kubectl
            build_image
            push_image
            deploy_k8s
            ;;
        rollback)
            check_kubectl
            rollback
            ;;
        status)
            check_kubectl
            status
            ;;
        delete)
            check_kubectl
            delete
            ;;
        help|*)
            echo "Usage: $0 {build|push|deploy|all|rollback|status|delete}"
            echo ""
            echo "Commands:"
            echo "  build     - Build Docker image"
            echo "  push      - Push Docker image to registry"
            echo "  deploy    - Deploy to Kubernetes"
            echo "  all       - Build, push, and deploy"
            echo "  rollback  - Rollback deployment"
            echo "  status    - Check deployment status"
            echo "  delete    - Delete deployment"
            echo ""
            echo "Environment Variables:"
            echo "  IMAGE_TAG - Image tag (default: latest)"
            ;;
    esac
}

main "$@"
