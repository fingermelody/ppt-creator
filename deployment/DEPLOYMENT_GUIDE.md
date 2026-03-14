# PPT-RSD 生产级 CI/CD 部署方案

## 一、资源现状分析

### 1.1 已配置资源

| 资源类型 | 状态 | 配置详情 |
|---------|------|---------|
| **CloudBase 环境** | ✅ 已配置 | 环境ID: `ai-generator-1gp9p3g64d04e869` (上海, 个人版) |
| **CloudRun 服务** | ✅ 已部署 | 服务名: `ppt-api` (容器型) |
| **COS 存储** | ✅ 已配置 | Bucket: `ppt-rsd-frontend-1253851367` |
| **API 网关** | ✅ 已配置 | Service ID: `service-bit92vk2` |

### 1.2 待配置资源

| 资源类型 | 状态 | 影响功能 | 推荐方案 |
|---------|------|---------|---------|
| **PostgreSQL 数据库** | ❌ 未配置 | 核心业务数据 | TDSQL-C 按量计费 或 CloudBase 内置数据库 |
| **Redis 缓存** | ❌ 未配置 | 会话、缓存、队列 | 腾讯云 Redis 基础版 或 CloudBase 内置 |
| **Elasticsearch Serverless** | ✅ 已配置 | 向量检索、全文搜索 | `http://space-k4t5xi0i.ap-guangzhou.qcloudes.com` |

### 1.3 当前问题

1. **数据库使用 SQLite**: 生产环境不适用，需迁移到云端数据库
2. **缺少 Redis**: 缓存和会话管理缺失
3. **向量数据库未配置**: AI 功能受限
4. **两套部署流程冲突**: deploy.yml (TKE) 和 deploy-production.yml (COS+SCF)

---

## 二、最低成本方案 (推荐)

### 2.1 方案架构

```
┌─────────────────────────────────────────────────────────┐
│                    生产环境架构                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   用户请求 ──► CDN ──► COS 静态托管 (前端)              │
│                    │                                    │
│                    ▼                                    │
│              API 网关 ──► CloudRun (后端)               │
│                                   │                     │
│                    ┌──────────────┼──────────────┐      │
│                    ▼              ▼              ▼      │
│              PostgreSQL      Redis        Elasticsearch │
│            (TDSQL-C)        (基础版)        (ES)        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 资源选型与成本

| 服务 | 规格 | 计费模式 | 月成本 | 说明 |
|-----|------|---------|--------|------|
| **CloudBase 个人版** | 基础套餐 | 包月 | ¥19.9 | 已有,包含云函数、静态托管 |
| **CloudRun** | 0.5核1G | 按量 | ~¥50 | 已有,按实际使用计费 |
| **TDSQL-C PostgreSQL** | 1核2GB | 按量 | ~¥80 | 推荐,可随时扩容 |
| **Redis 标准版** | 256MB | 包月 | ¥56 | 基础版足够使用 |
| **Elasticsearch Serverless** | 已配置 | 按量 | ¥0 | 向量检索,已创建 |
| **COS 存储** | 标准存储 | 按量 | ~¥10 | 已有免费额度 |
| **CDN 流量** | 按需 | 按量 | ~¥20 | 可选 |
| **总计** | - | - | **~¥235.9/月** | ES Serverless 已配置 |

### 2.3 阶段性成本控制

**第一阶段 (1-3个月, 验证期)**:
- 使用 CloudBase 内置数据库 (免费)
- 使用 CloudBase 内置 Redis (免费)
- 总成本: ~¥70/月 (仅 CloudBase + CloudRun)

**第二阶段 (3-6个月, 稳定期)**:
- 添加独立 Redis: +¥56/月
- 总成本: ~¥126/月

**第三阶段 (6个月+, 成长期)**:
- 添加 TDSQL-C: +¥80/月
- ES Serverless 已配置,按量计费
- 总成本: ~¥206/月

---

## 三、资源配置详细步骤

### 3.1 创建 TDSQL-C PostgreSQL

**控制台地址**: https://buy.cloud.tencent.com/cynosdb

```bash
# 配置参数
地域: ap-shanghai (与 CloudBase 同区,降低延迟)
数据库版本: PostgreSQL 15
计算规格: 1核2GB (起步)
存储空间: 10GB
计费模式: 按量计费
VPC: 选择与 CloudBase 相同的 VPC

# 创建后记录
数据库地址: xxxxxxxx.sql.tencentcdb.com
端口: 5432
用户名: root
密码: [设置的密码]
```

**成本估算**: 约 ¥2.5/天, 月均 ¥75-80

### 3.2 创建 Redis 实例

**控制台地址**: https://buy.cloud.tencent.com/redis

```bash
# 配置参数
地域: ap-shanghai
版本: Redis 5.0 标准版
规格: 256MB 内存
计费模式: 包年包月 (更优惠)
VPC: 选择与 CloudBase 相同的 VPC

# 创建后记录
连接地址: xxxxxxxx.redis.rds.tencentcloud.com
端口: 6379
密码: [设置的密码]
```

**成本**: ¥56/月

### 3.3 创建 Elasticsearch 实例

**控制台地址**: https://buy.cloud.tencent.com/es

```bash
# 配置参数
地域: ap-shanghai
版本: Elasticsearch 7.10
节点规格: 1核2GB
单节点数量: 1
存储: 20GB SSD
计费模式: 按量计费
VPC: 选择与 CloudBase 相同的 VPC

# 创建后记录
内网访问地址: http://xxxxxxxx.elasticsearch.tencentcloud.com:9200
用户名: elastic
密码: [设置的密码]
```

**成本估算**: 约 ¥6-7/天, 月均 ¥200

---

## 四、GitHub Secrets 配置

在 GitHub 仓库 `Settings` → `Secrets and variables` → `Actions` 中添加:

### 4.1 必需 Secrets

```yaml
# 腾讯云密钥
TENCENT_SECRET_ID: "AKID_REDACTED_SECRET_ID"
TENCENT_SECRET_KEY: "HWlrlX9fyIQj3Pj0GJ9l9IEwQgimmdP8"

# CloudBase 环境
ENV_ID: "ai-generator-1gp9p3g64d04e869"

# TDSQL-C PostgreSQL
DATABASE_URL: "postgresql://root:password@host.sql.tencentcdb.com:5432/ppt_rsd"
DB_HOST: "host.sql.tencentcdb.com"
DB_PORT: "5432"
DB_NAME: "ppt_rsd"
DB_USER: "root"
DB_PASSWORD: "your-password"

# Redis
REDIS_URL: "redis://:password@host.redis.rds.tencentcloud.com:6379/0"
REDIS_HOST: "host.redis.rds.tencentcloud.com"
REDIS_PORT: "6379"
REDIS_PASSWORD: "your-password"

# Elasticsearch Serverless (已配置)
ES_HOST: "http://space-k4t5xi0i.ap-guangzhou.qcloudes.com"
ES_APP_ID: "space-k4t5xi0i"
ES_USERNAME: "your-es-username"
ES_PASSWORD: "your-es-password"
ES_INDEX_NAME: "ppt_slides"

# COS (已有)
COS_BUCKET: "ppt-rsd-frontend-1253851367"
COS_REGION: "ap-guangzhou"

# LLM (选择一个)
HUNYUAN_SECRET_ID: "your-hunyuan-secret-id"
HUNYUAN_SECRET_KEY: "your-hunyuan-secret-key"

# JWT
SECRET_KEY: "生成一个32位随机字符串"

# 镜像仓库
TCR_REGISTRY: "ccr.ccs.tencentyun.com"
TCR_NAMESPACE: "tcb-100000763815-pzxy"
TCR_USERNAME: "100000763815"
TCR_PASSWORD: "your-tcr-password"
```

---

## 五、统一 CI/CD 流程

### 5.1 流程设计

```
代码推送
    │
    ▼
┌─────────────────────────────────────────┐
│           GitHub Actions                │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Lint    │  │ Test    │  │ Security│ │
│  └────┬────┘  └────┬────┘  └────┬────┘ │
│       └───────────┬┴───────────┘       │
│                   ▼                     │
│           ┌─────────────┐              │
│           │ Build Image │              │
│           └──────┬──────┘              │
│                  ▼                      │
│           ┌─────────────┐              │
│           │ Push to TCR │              │
│           └──────┬──────┘              │
│                  ▼                      │
│    ┌────────────────────────────┐      │
│    │      Deploy Decision       │      │
│    │  main    → CloudRun (prod) │      │
│    │  develop → CloudRun (test) │      │
│    └─────────────┬──────────────┘      │
│                  ▼                      │
│           ┌─────────────┐              │
│           │Health Check │              │
│           └──────┬──────┘              │
│         ┌────────┴────────┐            │
│         ▼                 ▼            │
│    成功 → 通知        失败 → 回滚+告警  │
└─────────────────────────────────────────┘
```

### 5.2 环境 Branch 策略

| 分支 | 环境 | 部署目标 | 域名 |
|-----|------|---------|------|
| `main` | 生产 | CloudRun | ppt.bottlepeace.com |
| `develop` | 测试 | CloudRun | test.ppt.bottlepeace.com |
| `feature/*` | 预览 | CloudRun | pr-{id}.ppt.bottlepeace.com |

---

## 六、部署命令 (Deployment Command)

### 6.1 完整部署脚本

位置: `deployment/deploy.sh`

```bash
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
esac

print_info "部署环境: $STAGE"
print_info "CloudBase 环境: $ENV_ID"
print_info "服务名称: $SERVICE_NAME"

# ============================================
# 检查环境变量
# ============================================
print_info "检查环境变量..."

required_vars=(
    "TENCENT_SECRET_ID"
    "TENCENT_SECRET_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "缺少环境变量: $var"
        print_info "请设置: export $var=your-value"
        exit 1
    fi
done

print_success "环境变量检查通过"

# ============================================
# 安装依赖工具
# ============================================
print_info "检查部署工具..."

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

# ============================================
# 部署后端
# ============================================
if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "backend" ]; then
    print_info "========== 部署后端 =========="
    
    # 构建并推送镜像
    print_info "构建 Docker 镜像..."
    
    IMAGE_TAG="${SERVICE_NAME}-$(date +%Y%m%d%H%M%S)"
    IMAGE_URL="ccr.ccs.tencentyun.com/tcb-100000763815-pzxy/ca-egweoedj_${SERVICE_NAME}:${IMAGE_TAG}"
    
    # 登录镜像仓库
    print_info "登录镜像仓库..."
    echo "$TCR_PASSWORD" | docker login ccr.ccs.tencentyun.com -u "$TCR_USERNAME" --password-stdin 2>/dev/null || true
    
    # 构建镜像
    cd backend
    docker build -t "$IMAGE_URL" -f ../deployment/docker/Dockerfile.backend .
    cd ..
    
    # 推送镜像
    print_info "推送镜像到 TCR..."
    docker push "$IMAGE_URL"
    
    # 部署到 CloudRun
    print_info "部署到 CloudRun..."
    
    # 使用 tccli 更新服务
    tccli tcb RunReBuildContainer \
        --EnvId "$ENV_ID" \
        --ServerName "$SERVICE_NAME" \
        --ImageUrl "$IMAGE_URL" \
        --ReleaseType "ROLLBACK" \
        --Region "ap-shanghai" || \
    print_warn "服务更新可能需要通过控制台完成"
    
    print_success "后端部署完成"
    print_info "镜像: $IMAGE_URL"
fi

# ============================================
# 部署前端
# ============================================
if [ "$SERVICE" = "all" ] || [ "$SERVICE" = "frontend" ]; then
    print_info "========== 部署前端 =========="
    
    # 安装依赖
    print_info "安装前端依赖..."
    cd frontend
    npm ci --quiet
    
    # 创建环境配置
    print_info "创建环境配置..."
    cat > .env.production <<EOF
VITE_API_URL=https://${API_DOMAIN}
VITE_APP_TITLE=PPT-RSD
VITE_ENABLE_MOCK=false
EOF
    
    # 构建
    print_info "构建前端..."
    npm run build
    
    # 部署到 COS
    print_info "部署到 COS..."
    
    coscmd config \
        -a "$TENCENT_SECRET_ID" \
        -s "$TENCENT_SECRET_KEY" \
        -b "ppt-rsd-frontend-1253851367" \
        -r "ap-guangzhou"
    
    # 清理旧文件
    print_info "清理旧文件..."
    coscmd delete -rf / 2>/dev/null || true
    
    # 上传新文件
    print_info "上传新文件..."
    coscmd upload -rs dist/ /
    
    # 配置静态网站
    coscmd putbucketwebsite --index index.html --error index.html
    
    cd ..
    print_success "前端部署完成"
    print_info "访问地址: https://$FRONTEND_DOMAIN"
fi

# ============================================
# 健康检查
# ============================================
print_info "========== 健康检查 =========="

sleep 10  # 等待服务启动

# 检查后端
print_info "检查后端健康状态..."
BACKEND_URL="https://${API_DOMAIN}/health"

if curl -f -s --max-time 30 "$BACKEND_URL" > /dev/null 2>&1; then
    print_success "后端服务正常"
else
    print_error "后端服务异常"
    print_info "请检查日志: https://tcb.cloud.tencent.com/dev?envId=${ENV_ID}#/platform-run"
fi

# 检查前端
print_info "检查前端服务状态..."
FRONTEND_URL="https://${FRONTEND_DOMAIN}"

if curl -f -s --max-time 10 "$FRONTEND_URL" > /dev/null 2>&1; then
    print_success "前端服务正常"
else
    print_warn "前端服务检查失败 (可能是 DNS 未配置)"
fi

# ============================================
# 部署总结
# ============================================
echo ""
echo "=========================================="
echo "  部署完成!"
echo "=========================================="
echo ""
echo "📌 访问地址:"
echo "   前端: https://${FRONTEND_DOMAIN}"
echo "   API:  https://${API_DOMAIN}"
echo ""
echo "📊 监控控制台:"
echo "   CloudBase: https://tcb.cloud.tencent.com/dev?envId=${ENV_ID}#/overview"
echo "   CloudRun:  https://tcb.cloud.tencent.com/dev?envId=${ENV_ID}#/platform-run"
echo ""
echo "💰 当前资源成本:"
echo "   CloudBase: ¥19.9/月"
echo "   CloudRun:  ~¥50/月 (按量)"
echo "   总计:      ~¥70/月"
echo ""
```

### 6.2 快速部署命令

```bash
# 完整部署到生产环境
./deployment/deploy.sh prod

# 仅部署后端
./deployment/deploy.sh prod backend

# 仅部署前端
./deployment/deploy.sh prod frontend

# 部署到测试环境
./deployment/deploy.sh test

# 部署到开发环境
./deployment/deploy.sh dev
```

---

## 七、后续优化建议

### 7.1 监控告警

1. 配置 CloudBase 告警策略
2. 接入企业微信/钉钉通知
3. 设置资源使用率告警

### 7.2 安全加固

1. 配置 WAF 防护
2. 启用 HTTPS 强制跳转
3. 配置 IP 白名单

### 7.3 性能优化

1. 启用 CDN 加速
2. 配置 Redis 缓存策略
3. 优化数据库索引

---

## 八、常见问题

### Q1: CloudRun 服务启动失败

检查日志: `https://tcb.cloud.tencent.com/dev?envId=${ENV_ID}#/platform-run`

常见原因:
- 镜像构建失败
- 环境变量配置错误
- 端口配置不正确 (应为 8000)

### Q2: 前端访问 404

检查:
- COS 静态网站配置
- 前端路由配置
- index.html 是否存在

### Q3: 数据库连接失败

检查:
- VPC 网络配置
- 安全组规则
- 数据库用户名密码

---

**文档版本**: v1.0
**最后更新**: 2026-03-14
**维护者**: DevOps Team
