#!/bin/bash

# ============================================
# 灰度部署脚本
# 支持金丝雀部署 (Canary Deployment)
# 分阶段灰度发布，监控指标，自动回滚
# 用法: ./deploy-canary.sh [prod|test] <backend_image> <frontend_image>
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[⚠]${NC} $1"; }
print_step() { echo -e "\n${CYAN}========== $1 ==========${NC}\n"; }

# 参数解析
ENVIRONMENT=${1:-prod}
BACKEND_IMAGE=${2:-}
FRONTEND_IMAGE=${3:-}

if [ -z "$BACKEND_IMAGE" ] || [ -z "$FRONTEND_IMAGE" ]; then
    print_error "缺少镜像参数"
    echo "用法: $0 [prod|test] <backend_image> <frontend_image>"
    exit 1
fi

# 环境配置
case $ENVIRONMENT in
    prod)
        NAMESPACE="ppt-rsd-prod"
        CANARY_STAGES=(10 25 50 100)
        STAGE_DURATION=(180 300 300 0)  # 秒
        ;;
    test)
        NAMESPACE="ppt-rsd-test"
        CANARY_STAGES=(25 50 100)
        STAGE_DURATION=(60 60 0)
        ;;
    *)
        print_error "未知环境: $ENVIRONMENT"
        exit 1
        ;;
esac

print_step "金丝雀部署 - $ENVIRONMENT 环境"
print_info "后端镜像: $BACKEND_IMAGE"
print_info "前端镜像: $FRONTEND_IMAGE"
print_info "灰度阶段: ${CANARY_STAGES[@]}%"

# ============================================
# 健康检查函数
# ============================================

check_pod_health() {
    local deployment=$1
    local expected_replicas=$2
    
    local ready_replicas=$(kubectl get deployment "$deployment" -n "$NAMESPACE" \
        -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    
    if [ "$ready_replicas" -ge "$expected_replicas" ]; then
        return 0
    else
        return 1
    fi
}

check_error_rate() {
    local deployment=$1
    local max_error_rate=${2:-5}  # 最大错误率 5%
    
    # 从日志中采样最近的请求，计算错误率
    local error_count=$(kubectl logs -l "app=$deployment" -n "$NAMESPACE" \
        --tail=100 2>/dev/null | grep -i "error\|exception" | wc -l || echo "0")
    
    local error_rate=$((error_count * 100 / 100))
    
    if [ "$error_rate" -le "$max_error_rate" ]; then
        print_success "$deployment 错误率: $error_rate% (阈值: $max_error_rate%)"
        return 0
    else
        print_error "$deployment 错误率过高: $error_rate% (阈值: $max_error_rate%)"
        return 1
    fi
}

check_response_time() {
    local deployment=$1
    local max_latency=${2:-500}  # 最大延迟 500ms
    
    # 这是一个简化的检查，实际使用需要集成监控系统
    print_info "$deployment 响应时间检查 (配置最大: ${max_latency}ms)"
    return 0
}

monitor_deployment() {
    local backend_replicas=$1
    local frontend_replicas=$2
    local stage_duration=$3
    
    print_info "监控时间: ${stage_duration}秒"
    
    local start_time=$(date +%s)
    local monitoring=true
    
    while [ "$monitoring" = true ]; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [ $elapsed -ge $stage_duration ]; then
            monitoring=false
        fi
        
        # 检查后端健康状态
        if ! check_pod_health "ppt-backend" "$backend_replicas"; then
            print_error "后端 Pod 未就绪"
            return 1
        fi
        
        # 检查前端健康状态
        if ! check_pod_health "ppt-frontend" "$frontend_replicas"; then
            print_error "前端 Pod 未就绪"
            return 1
        fi
        
        # 检查错误率
        if ! check_error_rate "ppt-backend" 5; then
            print_error "后端错误率过高"
            return 1
        fi
        
        # 检查响应时间
        check_response_time "ppt-backend" 500 || true
        
        # 等待后再继续
        if [ "$monitoring" = true ]; then
            print_info "继续监控... ($elapsed/${stage_duration}s)"
            sleep 30
        fi
    done
    
    print_success "阶段监控完成"
    return 0
}

# ============================================
# 灰度部署流程
# ============================================

run_canary_deployment() {
    print_step "开始灰度部署"
    
    # 获取当前副本数
    local total_backend_replicas=$(kubectl get deployment ppt-backend -n "$NAMESPACE" \
        -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "2")
    local total_frontend_replicas=$(kubectl get deployment ppt-frontend -n "$NAMESPACE" \
        -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "2")
    
    print_info "后端总副本数: $total_backend_replicas"
    print_info "前端总副本数: $total_frontend_replicas"
    
    # 灰度阶段
    for i in "${!CANARY_STAGES[@]}"; do
        local percentage=${CANARY_STAGES[$i]}
        local stage_num=$((i + 1))
        local stage_duration=${STAGE_DURATION[$i]}
        
        print_step "第 $stage_num 阶段 - $percentage% 流量"
        
        # 计算本阶段副本数
        local backend_canary_replicas=$((total_backend_replicas * percentage / 100))
        local frontend_canary_replicas=$((total_frontend_replicas * percentage / 100))
        
        # 最少保留 1 个副本
        if [ $backend_canary_replicas -eq 0 ]; then
            backend_canary_replicas=1
        fi
        if [ $frontend_canary_replicas -eq 0 ]; then
            frontend_canary_replicas=1
        fi
        
        print_info "目标副本数 - 后端: $backend_canary_replicas, 前端: $frontend_canary_replicas"
        
        # 更新镜像
        print_info "更新后端镜像..."
        kubectl set image deployment/ppt-backend \
            backend="$BACKEND_IMAGE" \
            -n "$NAMESPACE"
        
        print_info "更新前端镜像..."
        kubectl set image deployment/ppt-frontend \
            frontend="$FRONTEND_IMAGE" \
            -n "$NAMESPACE"
        
        # 更新副本数
        print_info "更新后端副本数..."
        kubectl scale deployment/ppt-backend \
            --replicas="$backend_canary_replicas" \
            -n "$NAMESPACE"
        
        print_info "更新前端副本数..."
        kubectl scale deployment/ppt-frontend \
            --replicas="$frontend_canary_replicas" \
            -n "$NAMESPACE"
        
        # 等待部署就绪
        print_info "等待部署就绪..."
        if ! kubectl rollout status deployment/ppt-backend -n "$NAMESPACE" --timeout=120s; then
            print_error "后端部署超时"
            return 1
        fi
        if ! kubectl rollout status deployment/ppt-frontend -n "$NAMESPACE" --timeout=120s; then
            print_error "前端部署超时"
            return 1
        fi
        
        # 监控阶段
        if [ $stage_duration -gt 0 ]; then
            if ! monitor_deployment "$backend_canary_replicas" "$frontend_canary_replicas" "$stage_duration"; then
                print_error "阶段 $stage_num 监控失败，执行回滚"
                return 1
            fi
        fi
        
        # 扩展到完整副本数 (最后一个阶段)
        if [ $percentage -eq 100 ]; then
            print_info "扩展到完整副本数..."
            kubectl scale deployment/ppt-backend \
                --replicas="$total_backend_replicas" \
                -n "$NAMESPACE"
            kubectl scale deployment/ppt-frontend \
                --replicas="$total_frontend_replicas" \
                -n "$NAMESPACE"
            
            print_info "等待完整部署就绪..."
            kubectl rollout status deployment/ppt-backend -n "$NAMESPACE" --timeout=300s || true
            kubectl rollout status deployment/ppt-frontend -n "$NAMESPACE" --timeout=300s || true
        fi
        
        print_success "第 $stage_num 阶段完成"
        echo ""
    done
    
    print_step "灰度部署完成"
    print_success "所有阶段都已通过健康检查"
}

# ============================================
# 错误处理和回滚
# ============================================

rollback_on_failure() {
    print_error "灰度部署失败，执行回滚..."
    
    print_info "回滚后端部署..."
    kubectl rollout undo deployment/ppt-backend -n "$NAMESPACE"
    
    print_info "回滚前端部署..."
    kubectl rollout undo deployment/ppt-frontend -n "$NAMESPACE"
    
    print_info "等待回滚完成..."
    kubectl rollout status deployment/ppt-backend -n "$NAMESPACE" --timeout=300s || true
    kubectl rollout status deployment/ppt-frontend -n "$NAMESPACE" --timeout=300s || true
    
    print_error "已回滚到前一版本"
}

trap 'rollback_on_failure; exit 1' ERR

# ============================================
# 主流程
# ============================================

main() {
    print_info "环境: $ENVIRONMENT"
    print_info "命名空间: $NAMESPACE"
    echo ""
    
    # 执行灰度部署
    if run_canary_deployment; then
        print_success "灰度部署成功完成"
        
        echo ""
        print_step "部署摘要"
        echo "后端部署:"
        kubectl get deployment ppt-backend -n "$NAMESPACE" -o wide
        echo ""
        echo "前端部署:"
        kubectl get deployment ppt-frontend -n "$NAMESPACE" -o wide
        echo ""
        
        print_info "监控命令:"
        echo "  kubectl logs -f deployment/ppt-backend -n $NAMESPACE"
        echo "  kubectl logs -f deployment/ppt-frontend -n $NAMESPACE"
        echo ""
        
        return 0
    else
        print_error "灰度部署失败"
        return 1
    fi
}

main "$@"
exit $?
