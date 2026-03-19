#!/bin/bash

# ============================================
# PPT-RSD 测试运行脚本
# 本地运行测试用例
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

# 解析参数
TEST_TYPE="${1:-all}"  # all, unit, integration, docker

case "$TEST_TYPE" in
    unit)
        info "运行单元测试..."
        cd backend
        
        # 检查虚拟环境
        if [ ! -d "venv" ]; then
            warning "创建虚拟环境..."
            python3 -m venv venv
        fi
        
        source venv/bin/activate
        
        # 安装依赖
        pip install -r requirements.txt -q
        pip install pytest pytest-cov pytest-asyncio httpx faker -q
        
        # 运行测试
        pytest ../tests/ -v --tb=short \
            --cov=app \
            --cov-report=term-missing \
            --cov-report=html:../coverage_html
        
        success "单元测试完成！覆盖率报告: coverage_html/index.html"
        ;;
        
    integration)
        info "运行集成测试（Docker Compose）..."
        
        # 启动测试环境
        docker compose -f deployment/docker/docker-compose.test.yml up -d mysql-test redis-test
        
        info "等待服务就绪..."
        sleep 20
        
        # 运行测试
        docker compose -f deployment/docker/docker-compose.test.yml up --exit-code-from test-runner test-runner
        
        # 收集结果
        docker compose -f deployment/docker/docker-compose.test.yml cp test-runner:/app/results ./test-results 2>/dev/null || true
        
        # 清理
        docker compose -f deployment/docker/docker-compose.test.yml down -v
        
        success "集成测试完成！结果保存在 test-results/"
        ;;
        
    docker)
        info "构建并运行 Docker 测试环境..."
        
        # 构建镜像
        docker compose -f deployment/docker/docker-compose.test.yml build
        
        # 启动全部服务
        docker compose -f deployment/docker/docker-compose.test.yml up -d
        
        info "等待服务就绪..."
        sleep 30
        
        # 检查服务状态
        info "检查后端服务..."
        curl -f http://localhost:8001/api/v1/health && success "后端服务正常" || error "后端服务异常"
        
        info "检查前端服务..."
        curl -f http://localhost:3001/health && success "前端服务正常" || warning "前端健康检查失败（可能正常）"
        
        echo ""
        info "测试环境已启动！"
        echo "  - 前端: http://localhost:3001"
        echo "  - 后端 API: http://localhost:8001/api/v1"
        echo "  - API 文档: http://localhost:8001/docs"
        echo ""
        info "停止测试环境: docker compose -f deployment/docker/docker-compose.test.yml down -v"
        ;;
        
    all)
        info "运行所有测试..."
        
        # 运行单元测试
        $0 unit
        
        echo ""
        info "=============================="
        echo ""
        
        # 运行集成测试
        $0 integration
        
        success "所有测试完成！"
        ;;
        
    *)
        echo "用法: $0 [unit|integration|docker|all]"
        echo ""
        echo "  unit        - 运行后端单元测试"
        echo "  integration - 运行 Docker 集成测试"
        echo "  docker      - 启动 Docker 测试环境"
        echo "  all         - 运行所有测试（默认）"
        exit 1
        ;;
esac
