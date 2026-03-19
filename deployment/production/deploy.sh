#!/bin/bash

# ============================================
# PPT-RSD 生产环境一键部署脚本
# 域名: ppt.bottlepeace.com
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEPLOY_DIR="$PROJECT_ROOT/deployment/production"

# 加载配置
source "$DEPLOY_DIR/config.env"

# ============================================
# 1. 构建前端
# ============================================
build_frontend() {
    print_info "🔨 构建前端..."
    
    cd "$PROJECT_ROOT/frontend"
    
    # 创建生产环境配置
    cat > .env.production << EOF
VITE_API_URL=https://$API_DOMAIN
VITE_APP_TITLE=$APP_NAME
VITE_ENABLE_MOCK=false
EOF
    
    npm ci --silent
    npm run build
    
    print_success "前端构建完成"
}

# ============================================
# 2. 部署前端到 COS
# ============================================
deploy_frontend_to_cos() {
    print_info "📦 部署前端到 COS..."
    
    # 配置 coscmd
    coscmd config -a $COS_SECRET_ID -s $COS_SECRET_KEY -b $COS_BUCKET -r $COS_REGION
    
    # 清空旧文件
    coscmd delete -rf / 2>/dev/null || true
    
    # 上传新文件
    cd "$PROJECT_ROOT/frontend/dist"
    coscmd upload -rs . /
    
    # 设置静态网站
    coscmd putbucketwebsite --index index.html --error index.html
    
    print_success "前端已部署到 COS"
}

# ============================================
# 3. 部署后端到 SCF
# ============================================
deploy_backend_to_scf() {
    print_info "🚀 部署后端到 SCF..."
    
    cd "$PROJECT_ROOT"
    
    # 打包后端代码
    rm -rf /tmp/scf-backend
    mkdir -p /tmp/scf-backend
    cp -r backend/* /tmp/scf-backend/
    cd /tmp/scf-backend
    rm -rf __pycache__ tests .env* *.md .git
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -delete
    
    # 创建 ZIP 包
    zip -r /tmp/ppt-rsd-backend.zip . -x "*.pyc" -x "*__pycache__*"
    
    # 使用 tccli 部署
    # 先检查函数是否存在
    FUNC_EXISTS=$(tccli scf GetFunction --FunctionName $SCF_FUNCTION_NAME --Namespace default --region $REGION 2>&1 || echo "not_found")
    
    if echo "$FUNC_EXISTS" | grep -q "not_found\|ResourceNotFound"; then
        print_info "创建新函数..."
        tccli scf CreateFunction \
            --FunctionName $SCF_FUNCTION_NAME \
            --Runtime $SCF_RUNTIME \
            --Handler "app.main.handler" \
            --MemorySize $SCF_MEMORY \
            --Timeout $SCF_TIMEOUT \
            --Type Web \
            --region $REGION \
            --Code '{"ZipFile":"'$(base64 -i /tmp/ppt-rsd-backend.zip | tr -d '\n')'"}'
    else
        print_info "更新函数代码..."
        tccli scf UpdateFunctionCode \
            --FunctionName $SCF_FUNCTION_NAME \
            --ZipFile $(base64 -i /tmp/ppt-rsd-backend.zip | tr -d '\n') \
            --region $REGION
    fi
    
    print_success "后端已部署到 SCF"
}

# ============================================
# 4. 配置 API 网关
# ============================================
setup_api_gateway() {
    print_info "🌐 配置 API 网关..."
    
    # 此步骤通常在首次部署时手动完成
    # 或通过 Serverless Framework 自动配置
    
    print_warning "请在腾讯云控制台配置 API 网关绑定域名: $API_DOMAIN"
    print_success "API 网关配置提示完成"
}

# ============================================
# 5. 配置 CDN
# ============================================
setup_cdn() {
    print_info "🌍 配置 CDN..."
    
    # CDN 配置通常需要在控制台完成
    # 包括：添加域名、配置源站、HTTPS 证书等
    
    print_warning "请在腾讯云 CDN 控制台配置:"
    echo "  - 域名: $CDN_DOMAIN"
    echo "  - 源站: $CDN_ORIGIN"
    echo "  - 开启 HTTPS"
    
    print_success "CDN 配置提示完成"
}

# ============================================
# 显示部署信息
# ============================================
show_deploy_info() {
    echo ""
    echo "============================================"
    echo -e "${GREEN}✅ 部署完成！${NC}"
    echo "============================================"
    echo ""
    echo "📌 访问地址:"
    echo "   前端: https://$FRONTEND_DOMAIN"
    echo "   API:  https://$API_DOMAIN"
    echo ""
    echo "📌 DNS 配置（请在域名服务商处配置）:"
    echo "   $FRONTEND_DOMAIN -> CNAME -> $CDN_ORIGIN"
    echo "   $API_DOMAIN      -> CNAME -> <API网关域名>"
    echo ""
    echo "📌 端口说明（固定配置）:"
    echo "   前端: HTTPS 443 (通过 CDN)"
    echo "   后端: HTTPS 443 (通过 API 网关)"
    echo ""
}

# ============================================
# 主函数
# ============================================
main() {
    echo ""
    echo "============================================"
    echo "   PPT-RSD 生产环境部署"
    echo "   域名: ppt.bottlepeace.com"
    echo "============================================"
    echo ""
    
    case "$1" in
        frontend)
            build_frontend
            deploy_frontend_to_cos
            ;;
        backend)
            deploy_backend_to_scf
            setup_api_gateway
            ;;
        cdn)
            setup_cdn
            ;;
        all)
            build_frontend
            deploy_frontend_to_cos
            deploy_backend_to_scf
            setup_api_gateway
            setup_cdn
            show_deploy_info
            ;;
        info)
            show_deploy_info
            ;;
        *)
            echo "用法: $0 {frontend|backend|cdn|all|info}"
            echo ""
            echo "  frontend  - 构建并部署前端到 COS"
            echo "  backend   - 部署后端到 SCF"
            echo "  cdn       - 显示 CDN 配置指南"
            echo "  all       - 完整部署"
            echo "  info      - 显示部署信息"
            exit 1
            ;;
    esac
}

main "$@"
