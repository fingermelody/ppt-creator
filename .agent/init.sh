#!/usr/bin/env bash
# PPT-RSD 项目启动脚本
# 用于标准化开发环境启动流程

set -e

echo "🚀 PPT-RSD 开发环境启动中..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 项目根目录: $PROJECT_ROOT"

# 1. 检查 Python 环境
echo ""
echo "🐍 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
else
    echo -e "${RED}✗ Python3 未安装${NC}"
    exit 1
fi

# 2. 检查并安装 Python 依赖
echo ""
echo "📦 检查后端依赖..."
if [ -f "backend/requirements.txt" ]; then
    cd backend
    if [ ! -d "venv" ]; then
        echo "创建虚拟环境..."
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt --quiet
    echo -e "${GREEN}✓${NC} 后端依赖已安装"
    cd ..
fi

# 3. 检查 Node.js 环境
echo ""
echo "📦 检查前端依赖..."
if [ -f "frontend/package.json" ]; then
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "安装前端依赖..."
        npm install
    else
        echo -e "${GREEN}✓${NC} 前端依赖已存在"
    fi
    cd ..
fi

# 4. 检查环境变量
echo ""
echo "🔐 检查环境变量..."
if [ -f "backend/.env" ]; then
    echo -e "${GREEN}✓${NC} 后端 .env 文件存在"
else
    echo -e "${YELLOW}⚠${NC} 后端 .env 文件不存在，请参考 backend/.env.example 创建"
fi

# 5. 启动后端服务
echo ""
echo "🔧 启动后端服务..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
echo -e "${GREEN}✓${NC} 后端服务已启动 (PID: $BACKEND_PID)"
cd ..

# 等待后端启动
sleep 3

# 6. 启动前端服务
echo ""
echo "🌐 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}✓${NC} 前端服务已启动 (PID: $FRONTEND_PID)"
cd ..

# 7. 健康检查
echo ""
echo "🏥 执行健康检查..."
sleep 5

# 检查后端
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 后端服务健康"
else
    echo -e "${YELLOW}⚠${NC} 后端健康检查失败 (可能端点不存在)"
fi

# 检查前端
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 前端服务健康"
else
    echo -e "${YELLOW}⚠${NC} 前端健康检查失败"
fi

# 8. 显示服务信息
echo ""
echo "======================================"
echo -e "${GREEN}✅ 开发环境启动完成！${NC}"
echo ""
echo "📍 服务地址:"
echo "   前端: http://localhost:3000"
echo "   后端: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "📝 进程信息:"
echo "   后端 PID: $BACKEND_PID"
echo "   前端 PID: $FRONTEND_PID"
echo ""
echo "🛑 停止服务: kill $BACKEND_PID $FRONTEND_PID"
echo "======================================"

# 保持脚本运行
wait
