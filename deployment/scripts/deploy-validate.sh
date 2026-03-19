#!/bin/bash

# ============================================
# 部署前验证脚本
# 检查所有部署前提条件
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
print_error() { echo -e "${RED}[✗ ERROR]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[⚠ WARN]${NC} $1"; }

# 计数器
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNED=0

check_passed() {
    print_success "$1"
    ((CHECKS_PASSED++))
}

check_failed() {
    print_error "$1"
    ((CHECKS_FAILED++))
}

check_warned() {
    print_warn "$1"
    ((CHECKS_WARNED++))
}

# ============================================
# 验证函数
# ============================================

check_environment_variables() {
    print_info "检查环境变量..."
    
    local required_vars=(
        "TENCENT_SECRET_ID"
        "TENCENT_SECRET_KEY"
        "TKE_CLUSTER_ID"
        "TCR_USERNAME"
        "TCR_PASSWORD"
    )
    
    local all_valid=true
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            check_failed "环境变量缺失: $var"
            all_valid=false
        else
            check_passed "环境变量已设置: $var"
        fi
    done
    
    return $([ "$all_valid" = true ] && echo 0 || echo 1)
}

check_kubernetes_connection() {
    print_info "检查 Kubernetes 连接..."
    
    if ! kubectl cluster-info &>/dev/null; then
        check_failed "无法连接到 Kubernetes 集群"
        return 1
    fi
    
    check_passed "Kubernetes 集群连接正常"
    
    # 显示集群信息
    local cluster_info=$(kubectl cluster-info | head -1)
    print_info "集群信息: $cluster_info"
    
    return 0
}

check_kubernetes_nodes() {
    print_info "检查 Kubernetes 节点..."
    
    local node_count=$(kubectl get nodes --no-headers | wc -l)
    if [ "$node_count" -eq 0 ]; then
        check_failed "没有可用的 Kubernetes 节点"
        return 1
    fi
    
    check_passed "找到 $node_count 个可用节点"
    
    # 检查节点状态
    if kubectl get nodes | grep -q "NotReady"; then
        check_warned "某些节点状态异常"
    else
        check_passed "所有节点状态正常"
    fi
    
    return 0
}

check_namespaces() {
    print_info "检查命名空间..."
    
    local namespaces=("ppt-rsd-prod" "ppt-rsd-test")
    for ns in "${namespaces[@]}"; do
        if kubectl get namespace "$ns" &>/dev/null; then
            check_passed "命名空间存在: $ns"
        else
            check_warned "命名空间不存在: $ns (可以自动创建)"
        fi
    done
    
    return 0
}

check_resource_quotas() {
    print_info "检查资源配额..."
    
    for ns in ppt-rsd-prod ppt-rsd-test; do
        if kubectl get resourcequota -n "$ns" &>/dev/null; then
            local quotas=$(kubectl get resourcequota -n "$ns" --no-headers | wc -l)
            check_passed "命名空间 $ns 有 $quotas 个资源配额"
        else
            check_warned "命名空间 $ns 未配置资源配额"
        fi
    done
    
    return 0
}

check_storage_classes() {
    print_info "检查存储类..."
    
    local sc_count=$(kubectl get storageclass --no-headers 2>/dev/null | wc -l)
    if [ "$sc_count" -eq 0 ]; then
        check_warned "集群中没有配置存储类"
    else
        check_passed "找到 $sc_count 个存储类"
    fi
    
    return 0
}

check_docker_connection() {
    print_info "检查 Docker 连接..."
    
    if ! docker info &>/dev/null; then
        check_failed "Docker daemon 未运行或无权限访问"
        return 1
    fi
    
    check_passed "Docker daemon 正常运行"
    
    local docker_version=$(docker version --format '{{.Server.Version}}')
    print_info "Docker 版本: $docker_version"
    
    return 0
}

check_docker_disk_space() {
    print_info "检查 Docker 磁盘空间..."
    
    local docker_disk=$(docker system df --format "table {{.Size}}" 2>/dev/null | tail -1 | sed 's/B.*//')
    print_info "Docker 使用空间: $docker_disk"
    
    # 检查剩余空间
    local available=$(df -h . | awk 'NR==2 {print $4}')
    print_info "当前目录剩余空间: $available"
    
    check_passed "磁盘空间检查完成"
    
    return 0
}

check_registry_connectivity() {
    print_info "检查镜像仓库连接..."
    
    local tcr_registry="${TCR_REGISTRY:-ccr.ccs.tencentyun.com}"
    
    if ! docker login "$tcr_registry" -u "${TCR_USERNAME:-}" -p "${TCR_PASSWORD:-}" &>/dev/null; then
        check_failed "无法连接到镜像仓库: $tcr_registry"
        return 1
    fi
    
    check_passed "镜像仓库连接正常: $tcr_registry"
    
    return 0
}

check_image_existence() {
    print_info "检查基础镜像..."
    
    local base_images=(
        "python:3.11-slim"
        "node:18-alpine"
        "nginx:alpine"
    )
    
    for image in "${base_images[@]}"; do
        if docker inspect "$image" &>/dev/null; then
            check_passed "基础镜像已存在: $image"
        else
            check_warned "基础镜像不存在 (会在构建时自动拉取): $image"
        fi
    done
    
    return 0
}

check_tencent_cli() {
    print_info "检查腾讯云 CLI..."
    
    if command -v tccli &>/dev/null; then
        local version=$(tccli --version)
        check_passed "腾讯云 CLI 已安装: $version"
    else
        check_warned "腾讯云 CLI (tccli) 未安装 (可选)"
    fi
    
    return 0
}

check_database_connectivity() {
    print_info "检查数据库连接..."
    
    # 从 K8s secret 获取数据库配置
    if kubectl get secret ppt-rsd-secrets -n ppt-rsd-prod &>/dev/null; then
        check_passed "数据库 Secret 存在"
        
        # 尝试获取数据库 URL
        local db_url=$(kubectl get secret ppt-rsd-secrets -n ppt-rsd-prod \
            -o jsonpath='{.data.database-url}' 2>/dev/null | base64 -d 2>/dev/null || echo "")
        
        if [ ! -z "$db_url" ]; then
            check_passed "找到数据库连接信息"
        else
            check_warned "无法解析数据库连接信息"
        fi
    else
        check_warned "数据库 Secret 不存在 (需要手动创建)"
    fi
    
    return 0
}

check_redis_connectivity() {
    print_info "检查 Redis 连接..."
    
    if kubectl get secret ppt-rsd-secrets -n ppt-rsd-prod &>/dev/null; then
        local redis_url=$(kubectl get secret ppt-rsd-secrets -n ppt-rsd-prod \
            -o jsonpath='{.data.redis-url}' 2>/dev/null | base64 -d 2>/dev/null || echo "")
        
        if [ ! -z "$redis_url" ]; then
            check_passed "找到 Redis 连接信息"
        else
            check_warned "无法解析 Redis 连接信息"
        fi
    else
        check_warned "缓存 Secret 不存在"
    fi
    
    return 0
}

check_git_status() {
    print_info "检查 Git 仓库..."
    
    if ! git rev-parse --git-dir &>/dev/null; then
        check_failed "当前目录不是 Git 仓库"
        return 1
    fi
    
    check_passed "Git 仓库正常"
    
    local branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    local commit=$(git rev-parse --short HEAD 2>/dev/null)
    print_info "当前分支: $branch"
    print_info "当前提交: $commit"
    
    # 检查是否有未提交的更改
    if ! git diff --quiet; then
        check_warned "工作目录有未提交的更改"
    else
        check_passed "工作目录清洁"
    fi
    
    return 0
}

check_deployment_manifests() {
    print_info "检查部署清单..."
    
    local manifest_files=(
        "deployment/kustomize/base/kustomization.yaml"
        "deployment/kustomize/overlays/prod/kustomization.yaml"
        "deployment/docker/Dockerfile.backend"
        "deployment/docker/Dockerfile.frontend"
    )
    
    local all_exist=true
    for file in "${manifest_files[@]}"; do
        if [ -f "$file" ]; then
            check_passed "部署清单存在: $file"
        else
            check_warned "部署清单不存在: $file"
            all_exist=false
        fi
    done
    
    return $([ "$all_exist" = true ] && echo 0 || echo 1)
}

# ============================================
# 打印摘要
# ============================================

print_summary() {
    echo ""
    echo "=========================================="
    echo "  验证摘要"
    echo "=========================================="
    echo ""
    echo -e "${GREEN}✓ 通过: $CHECKS_PASSED${NC}"
    echo -e "${YELLOW}⚠ 警告: $CHECKS_WARNED${NC}"
    echo -e "${RED}✗ 失败: $CHECKS_FAILED${NC}"
    echo ""
    
    if [ $CHECKS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ 所有关键检查都已通过!${NC}"
        echo ""
        echo "可以继续部署。"
        echo ""
        echo "部署命令:"
        echo "  ./deployment/scripts/deploy-optimized.sh prod"
        echo "  ./deployment/scripts/deploy-optimized.sh test"
        echo ""
        return 0
    else
        echo -e "${RED}❌ 有 $CHECKS_FAILED 个关键检查失败!${NC}"
        echo ""
        echo "请修复上述问题后重试。"
        echo ""
        return 1
    fi
}

# ============================================
# 主流程
# ============================================

main() {
    echo ""
    echo "=========================================="
    echo "  PPT-RSD 部署前验证"
    echo "=========================================="
    echo ""
    
    # 执行所有检查
    check_environment_variables || true
    echo ""
    
    check_kubernetes_connection || true
    check_kubernetes_nodes || true
    check_namespaces || true
    check_resource_quotas || true
    check_storage_classes || true
    echo ""
    
    check_docker_connection || true
    check_docker_disk_space || true
    check_registry_connectivity || true
    check_image_existence || true
    echo ""
    
    check_tencent_cli || true
    check_database_connectivity || true
    check_redis_connectivity || true
    echo ""
    
    check_git_status || true
    check_deployment_manifests || true
    echo ""
    
    # 打印摘要
    print_summary
}

main "$@"
exit $?
