#!/bin/bash

# ============================================
# PPT-RSD 优化版部署脚本 (腾讯云 TKE)
# 特性: 并行构建, 完整验证, 自动回滚
# 用法: ./deploy-optimized.sh [prod|test] [--dry-run] [--canary]
# ============================================

set -o pipefail

# ============================================
# 配置部分
# ============================================

ENVIRONMENT=${1:-prod}
DRY_RUN=${DRY_RUN:-}
CANARY_MODE=${CANARY_MODE:-}
DEPLOYMENT_START_TIME=$(date +%s)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/../logs"
DEPLOY_LOG="${LOG_DIR}/deploy-$(date +%Y%m%d-%H%M%S).log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================
# 日志和输出函数
# ============================================

mkdir -p "$LOG_DIR"

log() {
    echo "$@" | tee -a "$DEPLOY_LOG"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$DEPLOY_LOG"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$DEPLOY_LOG"
}

print_error() {
    echo -e "${RED}[✗ ERROR]${NC} $1" | tee -a "$DEPLOY_LOG"
}

print_warn() {
    echo -e "${YELLOW}[⚠ WARN]${NC} $1" | tee -a "$DEPLOY_LOG"
}

print_step() {
    echo -e "\n${CYAN}========== $1 ==========${NC}\n" | tee -a "$DEPLOY_LOG"
}

# ============================================
# 错误处理
# ============================================

handle_error() {
    local line_no=$1
    print_error "脚本在第 $line_no 行出错"
    log "详情: $BASH_COMMAND"
    cleanup_on_error
    exit 1
}

cleanup_on_error() {
    print_warn "执行清理操作..."
    
    # 杀死后台进程
    if [ ! -z "$BACKEND_BUILD_PID" ] && kill -0 "$BACKEND_BUILD_PID" 2>/dev/null; then
        kill $BACKEND_BUILD_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_BUILD_PID" ] && kill -0 "$FRONTEND_BUILD_PID" 2>/dev/null; then
        kill $FRONTEND_BUILD_PID 2>/dev/null || true
    fi
    
    print_warn "已中断 $(get_elapsed_time) 后"
}

trap 'handle_error ${LINENO}' ERR
trap cleanup_on_error EXIT INT TERM

# ============================================
# 工具函数
# ============================================

get_elapsed_time() {
    local end_time=$(date +%s)
    local elapsed=$((end_time - DEPLOYMENT_START_TIME))
    echo "$((elapsed / 60))m $((elapsed % 60))s"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "未找到命令: $1"
        print_info "请安装: $2"
        exit 1
    fi
}

validate_env_var() {
    local var_name=$1
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ]; then
        print_error "环境变量缺失: $var_name"
        return 1
    fi
    return 0
}

check_kubernetes_ready() {
    print_info "检查 Kubernetes 集群..."
    
    if ! kubectl cluster-info &>/dev/null; then
        print_error "无法连接到 Kubernetes 集群"
        return 1
    fi
    
    print_success "Kubernetes 集群就绪"
    
    # 获取集群信息
    CLUSTER_VERSION=$(kubectl version --short 2>/dev/null | grep Server | awk '{print $3}')
    print_info "集群版本: $CLUSTER_VERSION"
}

check_namespace_exists() {
    if kubectl get namespace "$NAMESPACE" &>/dev/null; then
        print_success "命名空间存在: $NAMESPACE"
        return 0
    else
        print_warn "命名空间不存在，将创建: $NAMESPACE"
        kubectl create namespace "$NAMESPACE"
        return $?
    fi
}

check_docker_daemon() {
    print_info "检查 Docker daemon..."
    
    if ! docker info &>/dev/null; then
        print_error "Docker daemon 未运行"
        return 1
    fi
    
    DOCKER_VERSION=$(docker version --format '{{.Server.Version}}')
    print_success "Docker 就绪 (版本 $DOCKER_VERSION)"
}

# ============================================
# 预部署验证
# ============================================

pre_deployment_checks() {
    print_step "预部署验证"
    
    # 检查工具
    print_info "检查所需工具..."
    check_command "kubectl" "https://kubernetes.io/docs/tasks/tools/"
    check_command "docker" "https://www.docker.com/products/docker-desktop/"
    check_command "git" "https://git-scm.com/"
    print_success "所有必需工具已安装"
    
    # 检查环境变量
    print_info "检查环境变量..."
    local required_vars=(
        "TENCENT_SECRET_ID"
        "TENCENT_SECRET_KEY"
        "TKE_CLUSTER_ID"
        "TCR_USERNAME"
        "TCR_PASSWORD"
    )
    
    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! validate_env_var "$var"; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_error "缺少环境变量:"
        printf '%s\n' "${missing_vars[@]}" | sed 's/^/  - /'
        return 1
    fi
    
    print_success "所有环境变量已设置"
    
    # 检查 Docker
    check_docker_daemon || return 1
    
    # 检查 Kubernetes
    check_kubernetes_ready || return 1
    
    # 检查命名空间
    check_namespace_exists || return 1
    
    # 验证 Git 信息
    print_info "验证 Git 信息..."
    local git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    local git_commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    print_info "  分支: $git_branch"
    print_info "  提交: $git_commit"
    
    return 0
}

# ============================================
# 镜像构建 (并行)
# ============================================

build_and_push_backend() {
    print_info "[后端] 开始构建和推送..."
    
    local backend_build_log="${LOG_DIR}/backend-build-$(date +%s).log"
    
    (
        {
            docker build \
                --build-arg BUILDKIT_INLINE_CACHE=1 \
                -t "$BACKEND_IMAGE" \
                -f deployment/docker/Dockerfile.backend \
                ./backend \
                2>&1
            
            if [ $? -ne 0 ]; then
                print_error "[后端] 构建失败"
                exit 1
            fi
            
            print_info "[后端] 构建完成，推送到镜像仓库..."
            
            docker push "$BACKEND_IMAGE" 2>&1
            
            if [ $? -eq 0 ]; then
                print_success "[后端] 推送完成: $BACKEND_IMAGE"
            else
                print_error "[后端] 推送失败"
                exit 1
            fi
        } >> "$backend_build_log" 2>&1
    ) &
    
    BACKEND_BUILD_PID=$!
}

build_and_push_frontend() {
    print_info "[前端] 开始构建和推送..."
    
    local frontend_build_log="${LOG_DIR}/frontend-build-$(date +%s).log"
    
    (
        {
            docker build \
                --build-arg BUILDKIT_INLINE_CACHE=1 \
                -t "$FRONTEND_IMAGE" \
                -f deployment/docker/Dockerfile.frontend \
                . \
                2>&1
            
            if [ $? -ne 0 ]; then
                print_error "[前端] 构建失败"
                exit 1
            fi
            
            print_info "[前端] 构建完成，推送到镜像仓库..."
            
            docker push "$FRONTEND_IMAGE" 2>&1
            
            if [ $? -eq 0 ]; then
                print_success "[前端] 推送完成: $FRONTEND_IMAGE"
            else
                print_error "[前端] 推送失败"
                exit 1
            fi
        } >> "$frontend_build_log" 2>&1
    ) &
    
    FRONTEND_BUILD_PID=$!
}

wait_for_builds() {
    print_step "等待镜像构建和推送完成"
    
    local backend_status=0
    local frontend_status=0
    
    print_info "后端构建 PID: $BACKEND_BUILD_PID"
    print_info "前端构建 PID: $FRONTEND_BUILD_PID"
    
    wait $BACKEND_BUILD_PID
    backend_status=$?
    
    wait $FRONTEND_BUILD_PID
    frontend_status=$?
    
    if [ $backend_status -ne 0 ]; then
        print_error "后端镜像构建或推送失败"
        return 1
    fi
    
    if [ $frontend_status -ne 0 ]; then
        print_error "前端镜像构建或推送失败"
        return 1
    fi
    
    print_success "所有镜像已成功构建和推送"
}

# ============================================
# 部署到 Kubernetes
# ============================================

deploy_to_kubernetes() {
    print_step "部署到 Kubernetes"
    
    if [ ! -z "$DRY_RUN" ]; then
        print_warn "DRY-RUN 模式: 不会实际部署"
        print_info "将使用以下镜像:"
        print_info "  后端: $BACKEND_IMAGE"
        print_info "  前端: $FRONTEND_IMAGE"
        return 0
    fi
    
    # 更新后端镜像
    print_info "更新后端部署..."
    if kubectl set image deployment/ppt-backend \
        backend="$BACKEND_IMAGE" \
        -n "$NAMESPACE" 2>/dev/null; then
        print_success "后端部署已更新"
    else
        print_warn "后端部署不存在，将从 Kustomize 清单创建..."
        if ! kubectl apply -k deployment/kustomize/overlays/$ENVIRONMENT -n "$NAMESPACE"; then
            print_error "无法创建后端部署"
            return 1
        fi
    fi
    
    # 更新前端镜像
    print_info "更新前端部署..."
    if kubectl set image deployment/ppt-frontend \
        frontend="$FRONTEND_IMAGE" \
        -n "$NAMESPACE" 2>/dev/null; then
        print_success "前端部署已更新"
    else
        print_warn "前端部署不存在，将从 Kustomize 清单创建..."
        if ! kubectl apply -k deployment/kustomize/overlays/$ENVIRONMENT -n "$NAMESPACE"; then
            print_error "无法创建前端部署"
            return 1
        fi
    fi
}

# ============================================
# 部署监控和验证
# ============================================

wait_for_rollout() {
    print_step "等待部署就绪"
    
    local timeout=300
    local start_time=$(date +%s)
    
    print_info "监控后端部署 (超时: ${timeout}s)..."
    if ! kubectl rollout status deployment/ppt-backend \
        -n "$NAMESPACE" \
        --timeout=${timeout}s; then
        print_error "后端部署超时"
        return 1
    fi
    
    print_success "后端部署就绪"
    
    print_info "监控前端部署 (超时: ${timeout}s)..."
    if ! kubectl rollout status deployment/ppt-frontend \
        -n "$NAMESPACE" \
        --timeout=${timeout}s; then
        print_error "前端部署超时"
        return 1
    fi
    
    print_success "前端部署就绪"
    
    local end_time=$(date +%s)
    local elapsed=$((end_time - start_time))
    print_info "总等待时间: $((elapsed / 60))m $((elapsed % 60))s"
}

verify_deployment_health() {
    print_step "验证部署健康状态"
    
    print_info "检查 Pod 状态..."
    if ! kubectl get pods -n "$NAMESPACE" | grep -q "Running"; then
        print_error "没有运行中的 Pod"
        return 1
    fi
    
    # 检查后端 Pod
    print_info "检查后端 Pod..."
    local backend_pods=$(kubectl get pods -n "$NAMESPACE" -l app=ppt-backend -o jsonpath='{.items[*].metadata.name}')
    if [ -z "$backend_pods" ]; then
        print_error "找不到后端 Pod"
        return 1
    fi
    
    for pod in $backend_pods; do
        local status=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
        if [ "$status" != "Running" ]; then
            print_error "后端 Pod 状态异常: $pod ($status)"
            return 1
        fi
        print_success "后端 Pod 就绪: $pod"
    done
    
    # 检查前端 Pod
    print_info "检查前端 Pod..."
    local frontend_pods=$(kubectl get pods -n "$NAMESPACE" -l app=ppt-frontend -o jsonpath='{.items[*].metadata.name}')
    if [ -z "$frontend_pods" ]; then
        print_error "找不到前端 Pod"
        return 1
    fi
    
    for pod in $frontend_pods; do
        local status=$(kubectl get pod "$pod" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
        if [ "$status" != "Running" ]; then
            print_error "前端 Pod 状态异常: $pod ($status)"
            return 1
        fi
        print_success "前端 Pod 就绪: $pod"
    done
    
    print_success "所有 Pod 健康状态良好"
}

# ============================================
# 部署摘要
# ============================================

print_deployment_summary() {
    print_step "部署完成"
    
    local elapsed_time=$(get_elapsed_time)
    
    echo -e "\n${GREEN}🎉 部署成功!${NC}\n"
    
    echo -e "${CYAN}部署信息:${NC}"
    echo "  环境: $ENVIRONMENT"
    echo "  命名空间: $NAMESPACE"
    echo "  后端镜像: $BACKEND_IMAGE"
    echo "  前端镜像: $FRONTEND_IMAGE"
    echo "  总耗时: $elapsed_time"
    echo ""
    
    echo -e "${CYAN}部署日志:${NC}"
    echo "  $DEPLOY_LOG"
    echo ""
    
    echo -e "${CYAN}监控命令:${NC}"
    echo "  kubectl get pods -n $NAMESPACE"
    echo "  kubectl logs -f deployment/ppt-backend -n $NAMESPACE"
    echo "  kubectl logs -f deployment/ppt-frontend -n $NAMESPACE"
    echo ""
    
    echo -e "${CYAN}有用资源:${NC}"
    echo "  Dashboard: https://console.cloud.tencent.com/tke2/clusters"
    echo "  镜像仓库: https://console.cloud.tencent.com/tcr/repositories"
    echo ""
}

# ============================================
# 主流程
# ============================================

main() {
    print_step "PPT-RSD 优化部署"
    
    # 参数验证
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
            echo "用法: $0 [prod|test] [--dry-run]"
            exit 1
            ;;
    esac
    
    print_info "部署环境: $ENVIRONMENT"
    print_info "命名空间: $NAMESPACE"
    
    # 生成镜像标签
    IMAGE_TAG="$(date +%Y%m%d%H%M%S)-$(git rev-parse --short HEAD 2>/dev/null || echo 'local')"
    TCR_REGISTRY="${TCR_REGISTRY:-ccr.ccs.tencentyun.com}"
    TCR_NAMESPACE="${TCR_NAMESPACE:-codebuddy-ppt-creator}"
    
    BACKEND_IMAGE="${TCR_REGISTRY}/${TCR_NAMESPACE}/backend:${IMAGE_TAG}"
    FRONTEND_IMAGE="${TCR_REGISTRY}/${TCR_NAMESPACE}/frontend:${IMAGE_TAG}"
    
    print_info "镜像标签: $IMAGE_TAG"
    
    # 预部署检查
    if ! pre_deployment_checks; then
        print_error "预部署检查失败"
        exit 1
    fi
    
    # Docker 登录
    print_step "Docker 仓库认证"
    print_info "登录到 TCR..."
    if echo "$TCR_PASSWORD" | docker login "$TCR_REGISTRY" -u "$TCR_USERNAME" --password-stdin &>/dev/null; then
        print_success "Docker 登录成功"
    else
        print_error "Docker 登录失败"
        exit 1
    fi
    
    # 构建和推送镜像 (并行)
    print_step "构建和推送镜像 (并行)"
    build_and_push_backend
    build_and_push_frontend
    wait_for_builds || exit 1
    
    # 部署
    deploy_to_kubernetes || exit 1
    
    # 等待部署完成
    wait_for_rollout || {
        print_error "部署失败，执行回滚..."
        kubectl rollout undo deployment/ppt-backend -n "$NAMESPACE"
        kubectl rollout undo deployment/ppt-frontend -n "$NAMESPACE"
        exit 1
    }
    
    # 健康检查
    verify_deployment_health || {
        print_error "健康检查失败"
        exit 1
    }
    
    # 打印摘要
    print_deployment_summary
    
    print_info "部署日志已保存到: $DEPLOY_LOG"
    
    return 0
}

# 运行主流程
main "$@"
exit $?
