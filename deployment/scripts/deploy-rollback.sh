#!/bin/bash

# ============================================
# 快速回滚脚本
# 用于快速回滚到前一个版本
# 用法: ./deploy-rollback.sh [prod|test] [--force]
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[⚠]${NC} $1"; }

# 参数解析
ENVIRONMENT=${1:-prod}
FORCE_FLAG=${2:-}

# 环境配置
case $ENVIRONMENT in
    prod)
        NAMESPACE="ppt-rsd-prod"
        ;;
    test)
        NAMESPACE="ppt-rsd-test"
        ;;
    *)
        print_error "未知环境: $ENVIRONMENT"
        exit 1
        ;;
esac

print_info "环境: $ENVIRONMENT"
print_info "命名空间: $NAMESPACE"
echo ""

# 显示当前部署信息
print_info "显示当前部署信息..."
echo ""

echo "后端部署:"
kubectl get deployment ppt-backend -n $NAMESPACE -o wide 2>/dev/null || echo "部署不存在"
echo ""

echo "前端部署:"
kubectl get deployment ppt-frontend -n $NAMESPACE -o wide 2>/dev/null || echo "部署不存在"
echo ""

# 显示部署历史
print_info "显示部署历史..."
echo ""

echo "后端部署历史:"
kubectl rollout history deployment/ppt-backend -n $NAMESPACE 2>/dev/null || echo "无历史记录"
echo ""

echo "前端部署历史:"
kubectl rollout history deployment/ppt-frontend -n $NAMESPACE 2>/dev/null || echo "无历史记录"
echo ""

# 确认回滚
if [ -z "$FORCE_FLAG" ]; then
    read -p "确认要回滚 $ENVIRONMENT 环境? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_warn "已取消回滚"
        exit 0
    fi
fi

# 执行回滚
print_warn "执行回滚..."
echo ""

print_info "回滚后端部署..."
if kubectl rollout undo deployment/ppt-backend -n $NAMESPACE; then
    print_success "后端部署已回滚"
else
    print_error "后端部署回滚失败"
    exit 1
fi

print_info "回滚前端部署..."
if kubectl rollout undo deployment/ppt-frontend -n $NAMESPACE; then
    print_success "前端部署已回滚"
else
    print_error "前端部署回滚失败"
    exit 1
fi

# 等待部署完成
print_info "等待部署完成..."
echo ""

print_info "监控后端部署..."
kubectl rollout status deployment/ppt-backend -n $NAMESPACE --timeout=300s || {
    print_error "后端部署超时"
    exit 1
}

print_info "监控前端部署..."
kubectl rollout status deployment/ppt-frontend -n $NAMESPACE --timeout=300s || {
    print_error "前端部署超时"
    exit 1
}

# 打印摘要
echo ""
echo "=========================================="
print_success "回滚完成!"
echo "=========================================="
echo ""

print_info "当前部署状态:"
kubectl get pods -n $NAMESPACE -l "app in (ppt-backend, ppt-frontend)" 2>/dev/null || true
echo ""

print_info "监控命令:"
echo "  kubectl logs -f deployment/ppt-backend -n $NAMESPACE"
echo "  kubectl logs -f deployment/ppt-frontend -n $NAMESPACE"
echo ""
