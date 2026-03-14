#!/bin/bash
set -e

# ============================================
# PPT-RSD 生产环境部署脚本
# 用法: ./deploy.sh [stage] [service]
#   stage: dev | test | prod (默认: prod)
#   service: all | frontend | backend (默认: all)
# ============================================

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 参数解析
STAGE=${1:-prod}
SERVICE=${2:-all}

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# ============================================
# 环境配置
# ============================================
case $STAGE in
    prod)
        ENV_ID="ai-generator-1gp9p3g64d04e869"
        SERVICE_NAME="ppt-api"
        FRONTEND_DOMAIN="ppt.bottlepeace.com"
        API_DOMAIN="ppt-api-228212-9-1253851367.sh.run.tcloudbase.com"
        ;;
    test)
        ENV_ID="ai-generator-1gp9p3g64d04e869"
        SERVICE_NAME="ppt-api-test"
        FRONTEND_DOMAIN="test.ppt.bottlepeace.com"
        API_DOMAIN="ppt-api-test.sh.run.tcloudbase.com"
        ;;
    dev)
        ENV_ID="ai-generator-1gp9p3g64d04e869"
        SERVICE_NAME="ppt-api-dev"
        FRONTEND_DOMAIN="dev.ppt.bottlepeace.com"
        API_DOMAIN="ppt-api-dev.sh.run.tcloudbase.com"
        ;;
    *)
        print_error "未知环境: $STAGE"
        print_info "支持的环境: dev, test, prod"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "  PPT-RSD 部署脚本"
echo "=========================================="
echo ""
print_info "部署环境: $STAGE"
print_info "CloudBase 环境: $ENV_ID"
print_info "服务名称: $SERVICE_NAME"
print_info "部署目标: $SERVICE"
echo ""

# ============================================
# 检查环境变量
# ============================================
print_info "检查环境变量..."

required_vars=(
    "TENCENT_SECRET_ID"
    "TENCENT_SECRET_KEY"
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
    echo ""
    print_info "请设置环境变量后重试:"
    echo "  export TENCENT_SECRET_ID=your-secret-id"
    echo "  export TENCENT_SECRET_KEY=your-secret-key"
    exit 1
fi

print_success "环境变量检查通过"

# ============================================
# 检查项目目录
# ============================================
print_info "检查项目目录..."

if [ ! -d "backend" ]; then
    print_error "未找到 backend 目录"
    print_info "请在项目根目录运行此脚本"
    exit 1
fi

if [ ! -d "frontend" ]; then
    print_error "未找到 frontend 目录"
    print_info "请在项目根目录运行此脚本"
    exit 1
fi

print_success "项目目录检查通过"

# ============================================
# 安装依赖工具
# ============================================
print_info "检查部署工具..."

# 检查 Docker
if ! command -v docker &> /dev/null; then
    print_error "未安装 Docker"
    print_info "请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查并安装 tccli
if ! command -v tccli &> /dev/null; then
    print_info "安装 tccli..."
    pip install tccli -q
fi

# 检查并安装 coscmd
if ! command -v coscmd &> /dev/null; then
    print_info "安装 coscmd..."
    pip install coscmd -q
fi

print_success "部署工具准备完成"

# ============================================
# 配置腾讯云 CLI
# ============================================
print_info "配置腾讯云 CLI..."
tccli configure set secretId "$TENCENT_SECRET_ID"
tccli configure set secretKey "$TENCENT_SECRET_KEY"
tccli configure set region "ap-shanghai"

print_success "腾讯云 CLI 配置完成"

# ============================================
# 部署后端
# ============================================
if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "backend" ]; then
    echo ""
    print_info "========== 部署后端 =========="
    echo ""
    
    # 生成镜像标签
    IMAGE_TAG="${SERVICE_NAME}-$(date +%Y%m%d%H%M%S)"
    IMAGE_URL="ccr.ccs.tencentyun.com/tcb-100000763815-pzxy/ca-egweoedj_${SERVICE_NAME}:${IMAGE_TAG}"
    
    # 登录镜像仓库
    print_info "登录镜像仓库..."
    if [ -n "$TCR_PASSWORD" ]; then
        echo "$TCR_PASSWORD" | docker login ccr.ccs.tencentyun.com -u "${TCR_USERNAME:-100000763815}" --password-stdin 2>/dev/null || true
    else
        print_warn "未设置 TCR_PASSWORD, 将使用 Docker 已登录的凭证"
    fi
    
    # 构建镜像
    print_info "构建 Docker 镜像..."
    print_info "镜像标签: $IMAGE_TAG"
    
    cd backend
    docker build \
        -t "$IMAGE_URL" \
        -f ../deployment/docker/Dockerfile.backend \
        --build-arg PYTHON_VERSION=3.9 \
        .
    cd ..
    
    print_success "镜像构建完成"
    
    # 推送镜像
    print_info "推送镜像到 TCR (可能需要几分钟)..."
    docker push "$IMAGE_URL"
    
    print_success "镜像推送完成"
    
    # 部署到 CloudRun
    print_info "更新 CloudRun 服务..."
    
    # 使用 API 更新服务版本
    UPDATE_RESULT=$(tccli tcb ModifyCloudRunServerVersion \
        --EnvId "$ENV_ID" \
        --ServerName "$SERVICE_NAME" \
        --ImageUrl "$IMAGE_URL" \
        --Region "ap-shanghai" 2>&1) || {
        print_warn "直接更新失败, 尝试通过控制台更新"
        print_info "请访问: https://tcb.cloud.tencent.com/dev?envId=${ENV_ID}#/platform-run"
    }
    
    if echo "$UPDATE_RESULT" | grep -q "Success\|success"; then
        print_success "CloudRun 服务更新成功"
    fi
    
    echo ""
    print_success "后端部署完成"
    print_info "镜像地址: $IMAGE_URL"
    print_info "API 地址: https://${API_DOMAIN}"
fi

# ============================================
# 部署前端
# ============================================
if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "frontend" ]; then
    echo ""
    print_info "========== 部署前端 =========="
    echo ""
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        print_error "未安装 Node.js"
        exit 1
    fi
    
    # 安装依赖
    print_info "安装前端依赖..."
    cd frontend
    npm ci --quiet 2>/dev/null || npm install --quiet
    cd ..
    
    # 创建环境配置
    print_info "创建生产环境配置..."
    cat > frontend/.env.production <<EOF
VITE_API_URL=https://${API_DOMAIN}
VITE_APP_TITLE=PPT-RSD
VITE_ENABLE_MOCK=false
EOF
    
    # 构建
    print_info "构建前端应用..."
    cd frontend
    npm run build
    cd ..
    
    if [ ! -d "frontend/dist" ]; then
        print_error "前端构建失败, 未找到 dist 目录"
        exit 1
    fi
    
    print_success "前端构建完成"
    
    # 配置 COS
    print_info "配置 COS..."
    coscmd config \
        -a "$TENCENT_SECRET_ID" \
        -s "$TENCENT_SECRET_KEY" \
        -b "ppt-rsd-frontend-1253851367" \
        -r "ap-guangzhou"
    
    # 清理旧文件
    print_info "清理旧文件..."
    coscmd delete -rf / 2>/dev/null || true
    
    # 上传新文件
    print_info "上传前端文件到 COS..."
    cd frontend/dist
    coscmd upload -rs . / --ignore "*.map"
    cd ../..
    
    # 配置静态网站
    print_info "配置静态网站..."
    coscmd putbucketwebsite --index index.html --error index.html 2>/dev/null || true
    
    echo ""
    print_success "前端部署完成"
    print_info "访问地址: https://${FRONTEND_DOMAIN}"
    print_info "COS 地址: http://ppt-rsd-frontend-1253851367.cos-website.ap-guangzhou.myqcloud.com"
fi

# ============================================
# 健康检查
# ============================================
echo ""
print_info "========== 健康检查 =========="
echo ""

sleep 5  # 等待服务启动

# 检查后端
if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "backend" ]; then
    print_info "检查后端健康状态..."
    BACKEND_URL="https://${API_DOMAIN}/health"
    
    MAX_RETRIES=3
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f -s --max-time 30 "$BACKEND_URL" > /dev/null 2>&1; then
            print_success "后端服务正常"
            break
        else
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                print_warn "后端服务检查失败, 等待重试... ($RETRY_COUNT/$MAX_RETRIES)"
                sleep 10
            else
                print_error "后端服务异常"
                print_info "请检查日志: https://tcb.cloud.tencent.com/dev?envId=${ENV_ID}#/platform-run"
            fi
        fi
    done
fi

# 检查前端
if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "frontend" ]; then
    print_info "检查前端服务状态..."
    FRONTEND_URL="http://ppt-rsd-frontend-1253851367.cos-website.ap-guangzhou.myqcloud.com"
    
    if curl -f -s --max-time 10 "$FRONTEND_URL" > /dev/null 2>&1; then
        print_success "前端服务正常"
    else
        print_warn "前端服务检查失败"
    fi
fi

# ============================================
# 部署总结
# ============================================
echo ""
echo "=========================================="
echo "  🎉 部署完成!"
echo "=========================================="
echo ""
echo "📌 访问地址:"
echo "   前端: https://${FRONTEND_DOMAIN}"
echo "   API:  https://${API_DOMAIN}"
echo "   COS:  http://ppt-rsd-frontend-1253851367.cos-website.ap-guangzhou.myqcloud.com"
echo ""
echo "📊 监控控制台:"
echo "   CloudBase 概览: https://tcb.cloud.tencent.com/dev?envId=${ENV_ID}#/overview"
echo "   CloudRun 服务:  https://tcb.cloud.tencent.com/dev?envId=${ENV_ID}#/platform-run"
echo "   云函数:         https://tcb.cloud.tencent.com/dev?envId=${ENV_ID}#/scf"
echo ""
echo "💰 当前资源成本 (预估):"
echo "   CloudBase 个人版: ¥19.9/月"
echo "   CloudRun:         ~¥50/月 (按量计费)"
echo "   COS 存储:         ~¥10/月 (按量计费)"
echo "   ────────────────────────"
echo "   总计:             ~¥80/月"
echo ""
echo "📝 后续操作:"
echo "   1. 配置自定义域名 DNS 解析"
echo "   2. 开启 CDN 加速"
echo "   3. 配置监控告警"
echo ""
