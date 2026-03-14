#!/bin/bash
set -e

# ============================================
# PPT-RSD 生产环境部署脚本
# 独立云资源架构（TKE + TDSQL-C + Redis）
# 用法: ./deploy.sh [environment]
#   environment: prod | test (默认: prod)
# ============================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 参数解析
ENVIRONMENT=${1:-prod}

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# ============================================
# 环境配置
# ============================================
case $ENVIRONMENT in
    prod)
        NAMESPACE="ppt-rsd-prod"
        DOMAIN="ppt.bottlepeace.com"
        ;;
    test)
        NAMESPACE="ppt-rsd-test"
        DOMAIN="test.ppt.bottlepeace.com"
        ;;
    *)
        print_error "未知环境: $ENVIRONMENT"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "  PPT-RSD 部署脚本 (独立云资源)"
echo "=========================================="
echo ""
print_info "部署环境: $ENVIRONMENT"
print_info "Kubernetes Namespace: $NAMESPACE"
print_info "域名: $DOMAIN"
echo ""

# ============================================
# 检查环境变量
# ============================================
print_info "检查环境变量..."

required_vars=(
    "TENCENT_SECRET_ID"
    "TENCENT_SECRET_KEY"
    "TKE_CLUSTER_ID"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -gt 0 ]; then
    print_error "缺少以下环境变量:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

print_success "环境变量检查通过"

# ============================================
# 检查工具
# ============================================
print_info "检查部署工具..."

# 检查 kubectl
if ! command -v kubectl &> /dev/null; then
    print_error "未安装 kubectl"
    print_info "安装: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    print_error "未安装 Docker"
    exit 1
fi

print_success "部署工具检查通过"

# ============================================
# 配置 TKE 凭证
# ============================================
print_info "配置 TKE 集群凭证..."

# 使用腾讯云 CLI 配置 kubectl
if command -v tccli &> /dev/null; then
    tccli configure set secretId "$TENCENT_SECRET_ID"
    tccli configure set secretKey "$TENCENT_SECRET_KEY"
    tccli configure set region "${TKE_REGION:-ap-guangzhou}"
fi

print_success "TKE 凭证配置完成"

# ============================================
# 构建并推送镜像
# ============================================
print_info "========== 构建镜像 =========="
echo ""

# 生成镜像标签
IMAGE_TAG="$(date +%Y%m%d%H%M%S)-$(git rev-parse --short HEAD 2>/dev/null || echo 'local')"
TCR_REGISTRY="${TCR_REGISTRY:-ccr.ccs.tencentyun.com}"
TCR_NAMESPACE="${TCR_NAMESPACE:-codebuddy-ppt-creator}"

# 登录镜像仓库
print_info "登录镜像仓库..."
if [ -n "$TCR_PASSWORD" ]; then
    echo "$TCR_PASSWORD" | docker login "$TCR_REGISTRY" -u "${TCR_USERNAME:-100000763815}" --password-stdin
fi

# 构建后端镜像
print_info "构建后端镜像..."
BACKEND_IMAGE="${TCR_REGISTRY}/${TCR_NAMESPACE}/backend:${IMAGE_TAG}"
docker build -t "$BACKEND_IMAGE" -f deployment/docker/Dockerfile.backend ./backend
docker push "$BACKEND_IMAGE"
print_success "后端镜像推送完成: $BACKEND_IMAGE"

# 构建前端镜像
print_info "构建前端镜像..."
FRONTEND_IMAGE="${TCR_REGISTRY}/${TCR_NAMESPACE}/frontend:${IMAGE_TAG}"
docker build -t "$FRONTEND_IMAGE" -f deployment/docker/Dockerfile.frontend .
docker push "$FRONTEND_IMAGE"
print_success "前端镜像推送完成: $FRONTEND_IMAGE"

# ============================================
# 部署到 TKE
# ============================================
print_info "========== 部署到 TKE =========="
echo ""

# 检查 namespace 是否存在
kubectl get namespace "$NAMESPACE" 2>/dev/null || kubectl create namespace "$NAMESPACE"

# 创建/更新部署
print_info "更新后端部署..."
kubectl set image deployment/ppt-backend \
    backend="$BACKEND_IMAGE" \
    -n "$NAMESPACE" 2>/dev/null || {
    print_warn "部署不存在，创建新部署..."
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ppt-backend
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ppt-backend
  template:
    metadata:
      labels:
        app: ppt-backend
    spec:
      containers:
      - name: backend
        image: $BACKEND_IMAGE
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ppt-rsd-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: ppt-rsd-secrets
              key: redis-url
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
EOF
}

print_info "更新前端部署..."
kubectl set image deployment/ppt-frontend \
    frontend="$FRONTEND_IMAGE" \
    -n "$NAMESPACE" 2>/dev/null || {
    print_warn "部署不存在，创建新部署..."
    kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ppt-frontend
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ppt-frontend
  template:
    metadata:
      labels:
        app: ppt-frontend
    spec:
      containers:
      - name: frontend
        image: $FRONTEND_IMAGE
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
EOF
}

# 等待部署完成
print_info "等待部署完成..."
kubectl rollout status deployment/ppt-backend -n "$NAMESPACE" --timeout=300s
kubectl rollout status deployment/ppt-frontend -n "$NAMESPACE" --timeout=300s

# ============================================
# 健康检查
# ============================================
print_info "========== 健康检查 =========="
echo ""

kubectl get pods -n "$NAMESPACE"

# ============================================
# 部署总结
# ============================================
echo ""
echo "=========================================="
echo "  🎉 部署完成!"
echo "=========================================="
echo ""
echo "📌 访问地址:"
echo "   前端: https://${DOMAIN}"
echo "   API:  https://api.${DOMAIN}"
echo ""
echo "📊 监控命令:"
echo "   kubectl get pods -n $NAMESPACE"
echo "   kubectl logs -f deployment/ppt-backend -n $NAMESPACE"
echo ""
echo "📦 镜像标签: $IMAGE_TAG"
echo ""
