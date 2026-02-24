#!/bin/bash

# ============================================
# SCF 本地部署脚本
# 用于手动部署到腾讯云 SCF
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查环境
check_environment() {
    print_info "检查部署环境..."
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js 未安装，请先安装 Node.js"
        exit 1
    fi
    
    # 检查 Serverless Framework
    if ! command -v serverless &> /dev/null; then
        print_warning "Serverless Framework 未安装，正在安装..."
        npm install -g serverless
    fi
    
    # 检查 .env 文件
    if [ ! -f ".env" ]; then
        print_error ".env 文件不存在，请复制 .env.example 并填写配置"
        exit 1
    fi
    
    print_success "环境检查通过"
}

# 构建前端
build_frontend() {
    print_info "构建前端..."
    
    cd ../../frontend
    
    # 安装依赖
    if [ ! -d "node_modules" ]; then
        npm ci
    fi
    
    # 构建
    npm run build
    
    cd ../deployment/scf
    
    print_success "前端构建完成"
}

# 部署函数
deploy() {
    local stage=${1:-dev}
    
    print_info "开始部署到 ${stage} 环境..."
    
    # 设置环境变量
    export STAGE=$stage
    export SERVERLESS_PLATFORM_VENDOR=tencent
    
    # 加载 .env
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # 部署
    serverless deploy --stage $stage --debug
    
    print_success "部署完成！"
}

# 查看部署信息
info() {
    local stage=${1:-dev}
    
    print_info "获取 ${stage} 环境部署信息..."
    
    export STAGE=$stage
    export SERVERLESS_PLATFORM_VENDOR=tencent
    
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    serverless info --stage $stage
}

# 移除部署
remove() {
    local stage=${1:-dev}
    
    print_warning "即将移除 ${stage} 环境的所有资源！"
    read -p "确认继续？(y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        print_info "取消操作"
        exit 0
    fi
    
    export STAGE=$stage
    export SERVERLESS_PLATFORM_VENDOR=tencent
    
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    serverless remove --stage $stage --debug
    
    print_success "资源已移除"
}

# 显示帮助
show_help() {
    echo "
SCF 部署脚本

用法:
    ./deploy.sh <命令> [环境]

命令:
    deploy [stage]   部署到指定环境 (默认: dev)
    info [stage]     查看部署信息
    remove [stage]   移除部署资源
    build            仅构建前端
    help             显示此帮助

环境:
    dev              开发环境
    test             测试环境
    prod             生产环境

示例:
    ./deploy.sh deploy dev      # 部署到开发环境
    ./deploy.sh deploy prod     # 部署到生产环境
    ./deploy.sh info prod       # 查看生产环境信息
    ./deploy.sh remove dev      # 移除开发环境资源
"
}

# 主函数
main() {
    # 切换到脚本目录
    cd "$(dirname "$0")"
    
    case "$1" in
        deploy)
            check_environment
            build_frontend
            deploy "$2"
            ;;
        info)
            info "$2"
            ;;
        remove)
            remove "$2"
            ;;
        build)
            build_frontend
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
