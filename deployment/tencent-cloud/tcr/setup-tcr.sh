#!/bin/bash
# ============================================
# TCR 镜像仓库配置脚本
# PPT-Creator 项目
# ============================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  TCR 镜像仓库配置脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 配置信息
REGISTRY_ID="tcr-3295r2dx"
REGISTRY_DOMAIN="ppt-creator-registry.tencentcloudcr.com"
NAMESPACE="ppt-creator"
REPOS=("frontend" "backend" "worker")

echo -e "${YELLOW}TCR 实例信息:${NC}"
echo "  Registry ID: $REGISTRY_ID"
echo "  Registry Domain: $REGISTRY_DOMAIN"
echo "  Namespace: $NAMESPACE"
echo ""

# 检查 tccli
echo -e "${YELLOW}检查腾讯云 CLI...${NC}"
if ! command -v tccli &> /dev/null; then
    echo -e "${RED}错误: 未安装 tccli${NC}"
    echo "请先安装: pip install tccli"
    exit 1
fi
echo -e "${GREEN}✓ tccli 已安装${NC}"
echo ""

# 等待 TCR 实例就绪
echo -e "${YELLOW}检查 TCR 实例状态...${NC}"
while true; do
    STATUS=$(tccli tcr DescribeInstances --output json 2>/dev/null | grep -o '"Status": "[^"]*"' | head -1 | cut -d'"' -f4)
    if [ "$STATUS" = "Running" ]; then
        echo -e "${GREEN}✓ TCR 实例已就绪${NC}"
        break
    else
        echo "  当前状态: $STATUS, 等待中..."
        sleep 10
    fi
done
echo ""

# 创建镜像仓库
echo -e "${YELLOW}创建镜像仓库...${NC}"
for repo in "${REPOS[@]}"; do
    echo "  创建仓库: $NAMESPACE/$repo"
    tccli tcr CreateRepository \
        --RegistryId $REGISTRY_ID \
        --NamespaceName $NAMESPACE \
        --RepositoryName $repo \
        --BriefDescription "PPT-Creator $repo service" \
        --IsPublic true \
        > /dev/null 2>&1 || echo "    仓库已存在或创建中"
done
echo -e "${GREEN}✓ 镜像仓库创建完成${NC}"
echo ""

# 获取登录凭证
echo -e "${YELLOW}获取登录凭证...${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  TCR 登录信息${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "  登录地址: $REGISTRY_DOMAIN"
echo "  用户名:   100000763815 (腾讯云账号ID)"
echo "  命名空间: $NAMESPACE"
echo ""
echo "  登录命令:"
echo "    docker login $REGISTRY_DOMAIN -u 100000763815"
echo ""
echo "  镜像地址格式:"
echo "    $REGISTRY_DOMAIN/$NAMESPACE/frontend:latest"
echo "    $REGISTRY_DOMAIN/$NAMESPACE/backend:latest"
echo "    $REGISTRY_DOMAIN/$NAMESPACE/worker:latest"
echo ""
echo -e "${GREEN}========================================${NC}"
echo ""

# 更新环境变量
echo -e "${YELLOW}更新环境变量配置...${NC}"
if [ -f ".env" ]; then
    # 备份原文件
    cp .env .env.backup.$(date +%Y%m%d%H%M%S)
    
    # 更新 TCR 相关配置
    sed -i '' "s|TCR_REGISTRY=.*|TCR_REGISTRY=$REGISTRY_DOMAIN|g" .env 2>/dev/null || sed -i "s|TCR_REGISTRY=.*|TCR_REGISTRY=$REGISTRY_DOMAIN|g" .env
    
    echo -e "${GREEN}✓ 已更新 .env 文件${NC}"
else
    echo -e "${YELLOW}警告: 未找到 .env 文件${NC}"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  TCR 配置完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "下一步操作:"
echo "  1. 在腾讯云控制台获取临时登录密码"
echo "     https://console.cloud.tencent.com/tcr/repository"
echo ""
echo "  2. 本地登录 TCR:"
echo "     docker login $REGISTRY_DOMAIN -u 100000763815"
echo ""
echo "  3. 构建并推送镜像:"
echo "     docker build -t $REGISTRY_DOMAIN/$NAMESPACE/frontend:latest -f deployment/docker/Dockerfile.frontend ."
echo "     docker push $REGISTRY_DOMAIN/$NAMESPACE/frontend:latest"
echo ""
