# 优化部署脚本使用指南

## 概述

新的部署脚本集提供了以下功能：

| 脚本 | 功能 | 场景 |
|------|------|------|
| `deploy-optimized.sh` | 主部署脚本（并行构建+自动回滚） | 生产和测试部署 |
| `deploy-validate.sh` | 部署前验证 | 部署前检查环境 |
| `deploy-rollback.sh` | 快速回滚 | 紧急回滚 |
| `deploy-canary.sh` | 灰度部署 | 风险规避部署 |

## 脚本详解

### 1. 部署前验证: `deploy-validate.sh`

**目的**: 检查所有部署前提条件，确保部署能顺利进行

**用法**:
```bash
./deployment/scripts/deploy-validate.sh
```

**检查项目** (25+ 项):
- ✓ 环境变量完整性
- ✓ Kubernetes 集群连接
- ✓ 节点可用性
- ✓ 命名空间
- ✓ 资源配额
- ✓ Docker daemon
- ✓ 磁盘空间
- ✓ 镜像仓库连接
- ✓ 数据库和缓存配置
- ✓ Git 仓库状态
- ✓ 部署清单完整性

**输出示例**:
```
✓ 环境变量已设置: TENCENT_SECRET_ID
✓ 环境变量已设置: TENCENT_SECRET_KEY
✓ Kubernetes 集群连接正常
✓ 找到 3 个可用节点
✓ 命名空间存在: ppt-rsd-prod
...
✓ 通过: 23
⚠ 警告: 2
✗ 失败: 0

✅ 所有关键检查都已通过!
```

### 2. 优化部署: `deploy-optimized.sh`

**目的**: 快速、安全地部署到 Kubernetes（并行构建 30% 快）

**用法**:
```bash
# 部署到生产环境
./deployment/scripts/deploy-optimized.sh prod

# 部署到测试环境
./deployment/scripts/deploy-optimized.sh test

# 干运行模式（不实际部署）
DRY_RUN=1 ./deployment/scripts/deploy-optimized.sh prod
```

**特性**:
- 🚀 **并行构建**: 后端和前端同时构建，节省 30-40% 时间
- ✅ **完整验证**: 部署前检查集群、环境、资源
- 📊 **详细日志**: 每次部署日志保存到 `deployment/logs/`
- 🔄 **自动回滚**: 部署失败自动回滚到前一版本
- 📈 **进度监控**: 实时显示构建、推送、部署进度
- ⏱️ **性能报告**: 显示各阶段耗时

**环境变量要求**:
```bash
export TENCENT_SECRET_ID="your-secret-id"
export TENCENT_SECRET_KEY="your-secret-key"
export TKE_CLUSTER_ID="cls-xxxxx"
export TCR_USERNAME="100000000000"
export TCR_PASSWORD="your-tcr-password"
export TCR_REGISTRY="ccr.ccs.tencentyun.com"  # 可选
export TCR_NAMESPACE="codebuddy-ppt-creator"  # 可选
```

**部署过程**:
```
1. 预部署验证 (环境、工具、凭证)
2. Docker 登录
3. 后端镜像构建 (并行)
4. 前端镜像构建 (并行)
5. 等待两个构建完成
6. 推送镜像到 TCR
7. 更新 K8s 部署
8. 等待 Pod 就绪 (300s 超时)
9. 验证健康状态
10. 打印部署摘要
```

**日志位置**:
```
deployment/logs/
├── deploy-20250318-143022.log    # 主日志
├── backend-build-1741011022.log  # 后端构建日志
└── frontend-build-1741011023.log # 前端构建日志
```

**监控已部署的应用**:
```bash
# 查看 Pod 状态
kubectl get pods -n ppt-rsd-prod

# 查看后端日志
kubectl logs -f deployment/ppt-backend -n ppt-rsd-prod

# 查看前端日志
kubectl logs -f deployment/ppt-frontend -n ppt-rsd-prod

# 描述部署
kubectl describe deployment/ppt-backend -n ppt-rsd-prod
```

### 3. 快速回滚: `deploy-rollback.sh`

**目的**: 快速回滚到前一版本（紧急情况下可在 1 分钟内完成）

**用法**:
```bash
# 交互式回滚（需要确认）
./deployment/scripts/deploy-rollback.sh prod

# 强制回滚（跳过确认）
./deployment/scripts/deploy-rollback.sh prod --force
```

**特性**:
- 📋 **显示历史**: 列出部署版本历史
- 🔄 **同步回滚**: 后端和前端同时回滚
- 💬 **交互确认**: 确保不会误操作
- ⏱️ **快速完成**: 通常 30-60 秒

**工作原理**:
```
1. 显示当前部署信息
2. 显示部署版本历史
3. 请求用户确认
4. 执行后端回滚 (kubectl rollout undo)
5. 执行前端回滚
6. 等待新 Pod 就绪
7. 显示最终状态
```

**何时使用**:
- 新版本有严重 bug
- 发现性能问题
- 用户报告功能故障

### 4. 灰度部署: `deploy-canary.sh`

**目的**: 安全的分阶段发布，自动监控和回滚

**用法**:
```bash
# 获取镜像标签（从最新部署）
IMAGE_TAG="20250318143022-abc123"

# 灰度部署到生产
./deployment/scripts/deploy-canary.sh prod \
  ccr.ccs.tencentyun.com/codebuddy-ppt-creator/backend:$IMAGE_TAG \
  ccr.ccs.tencentyun.com/codebuddy-ppt-creator/frontend:$IMAGE_TAG

# 灰度部署到测试（更快的阶段）
./deployment/scripts/deploy-canary.sh test \
  ccr.ccs.tencentyun.com/codebuddy-ppt-creator/backend:$IMAGE_TAG \
  ccr.ccs.tencentyun.com/codebuddy-ppt-creator/frontend:$IMAGE_TAG
```

**灰度阶段** (生产环境):
- **第 1 阶段 (10% 流量)**: 3 分钟监控
  - 1 个后端 Pod, 1 个前端 Pod
  - 关键指标监控
  - 任何异常立即回滚

- **第 2 阶段 (25% 流量)**: 5 分钟监控
  - 部分用户切换到新版本
  - 继续监控

- **第 3 阶段 (50% 流量)**: 5 分钟监控
  - 一半用户使用新版本
  - 冷却期观察

- **第 4 阶段 (100% 流量)**: 全量发布
  - 所有用户使用新版本

**监控指标**:
- ✓ Pod 就绪状态
- ✓ 错误率 (< 5%)
- ✓ 响应时间
- ✓ 重启次数

**自动回滚条件**:
- Pod 无法就绪 (>120s)
- 错误率超过 5%
- 响应时间超过设定值
- 任何异常监控到

**测试环境灰度阶段**:
- 第 1 阶段: 25%, 1 分钟
- 第 2 阶段: 50%, 1 分钟
- 第 3 阶段: 100% (快速验证)

## 完整部署工作流

### 标准部署流程

```bash
# 1. 进入项目目录
cd /path/to/ppt-rsd

# 2. 验证环境
./deployment/scripts/deploy-validate.sh

# 3. 设置环境变量（如果未设置）
export TENCENT_SECRET_ID="..."
export TENCENT_SECRET_KEY="..."
export TKE_CLUSTER_ID="..."
export TCR_USERNAME="..."
export TCR_PASSWORD="..."

# 4. 执行部署（生产环境）
./deployment/scripts/deploy-optimized.sh prod

# 5. 监控部署
kubectl get pods -n ppt-rsd-prod -w

# 6. 验证应用可用性
curl https://ppt.bottlepeace.com/health
```

### 金丝雀部署流程（推荐用于大功能发布）

```bash
# 1-3. 同上

# 4. 构建新版本
./deployment/scripts/deploy-optimized.sh prod --dry-run

# 5. 执行灰度部署
IMAGE_TAG="20250318143022-abc123"
./deployment/scripts/deploy-canary.sh prod \
  ccr.ccs.tencentyun.com/codebuddy-ppt-creator/backend:$IMAGE_TAG \
  ccr.ccs.tencentyun.com/codebuddy-ppt-creator/frontend:$IMAGE_TAG

# 6. 如果监控失败，自动回滚；成功则全量发布

# 7. 验证最终状态
kubectl get pods -n ppt-rsd-prod
```

### 紧急回滚流程

```bash
# 检查当前状态
kubectl get pods -n ppt-rsd-prod

# 查看最近的部署
./deployment/scripts/deploy-rollback.sh prod

# 强制回滚（跳过确认）
./deployment/scripts/deploy-rollback.sh prod --force

# 验证回滚完成
kubectl logs -f deployment/ppt-backend -n ppt-rsd-prod
```

## 环境变量设置

### 推荐方法 1: 在 Shell 配置中设置

编辑 `~/.bashrc` 或 `~/.zshrc`:
```bash
export TENCENT_SECRET_ID="your-secret-id"
export TENCENT_SECRET_KEY="your-secret-key"
export TKE_CLUSTER_ID="cls-xxxxx"
export TCR_USERNAME="100000000000"
export TCR_PASSWORD="your-tcr-password"
```

然后重新加载:
```bash
source ~/.bashrc  # 或 source ~/.zshrc
```

### 推荐方法 2: 使用 .env 文件

创建 `deployment/.env.deployment`:
```bash
export TENCENT_SECRET_ID="your-secret-id"
export TENCENT_SECRET_KEY="your-secret-key"
export TKE_CLUSTER_ID="cls-xxxxx"
export TCR_USERNAME="100000000000"
export TCR_PASSWORD="your-tcr-password"
export TCR_REGISTRY="ccr.ccs.tencentyun.com"
export TCR_NAMESPACE="codebuddy-ppt-creator"
```

使用时:
```bash
source deployment/.env.deployment
./deployment/scripts/deploy-optimized.sh prod
```

### 推荐方法 3: 使用 direnv

创建 `.envrc` (在项目根目录):
```bash
export TENCENT_SECRET_ID="your-secret-id"
export TENCENT_SECRET_KEY="your-secret-key"
export TKE_CLUSTER_ID="cls-xxxxx"
export TCR_USERNAME="100000000000"
export TCR_PASSWORD="your-tcr-password"
```

然后:
```bash
direnv allow
# 进入项目目录时自动加载环境变量
```

## 故障排查

### 问题 1: "未找到命令: kubectl"

**解决方案**:
```bash
# 安装 kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/darwin/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

### 问题 2: "缺少环境变量"

**解决方案**:
```bash
# 检查环境变量
echo $TENCENT_SECRET_ID
echo $TCR_PASSWORD

# 设置缺失的环境变量
export TENCENT_SECRET_ID="xxx"
```

### 问题 3: "Docker daemon 未运行"

**解决方案**:
```bash
# macOS
open -a Docker

# 等待 Docker 启动
sleep 30

# 验证
docker ps
```

### 问题 4: "镜像仓库连接失败"

**解决方案**:
```bash
# 测试镜像仓库连接
curl -I https://ccr.ccs.tencentyun.com

# 测试 Docker 登录
echo $TCR_PASSWORD | docker login ccr.ccs.tencentyun.com -u $TCR_USERNAME --password-stdin

# 验证登录
cat ~/.docker/config.json | grep ccr.ccs.tencentyun.com
```

### 问题 5: "部署超时"

**原因和解决方案**:
- **镜像拉取慢**: 检查网络，使用加速域名
- **Pod 启动慢**: 增加超时时间，或检查应用日志
- **资源不足**: 增加集群资源或优化应用

```bash
# 查看 Pod 启动日志
kubectl describe pod <pod-name> -n ppt-rsd-prod

# 查看 Pod 事件
kubectl get events -n ppt-rsd-prod --sort-by='.lastTimestamp'
```

### 问题 6: "部署失败自动回滚"

**排查步骤**:
```bash
# 1. 查看回滚后的 Pod
kubectl get pods -n ppt-rsd-prod

# 2. 查看旧版本
kubectl rollout history deployment/ppt-backend -n ppt-rsd-prod

# 3. 查看失败的 Pod 日志
kubectl logs <failed-pod> -n ppt-rsd-prod

# 4. 检查镜像是否存在
docker manifest inspect <backend-image>

# 5. 手动检查新镜像
docker run --rm <backend-image> /bin/sh -c "python -c 'from app.main import app; print(\"OK\")'"
```

## 性能优化

### 构建时间优化

**使用 Docker BuildKit 缓存**:
```bash
export DOCKER_BUILDKIT=1
export BUILDKIT_INLINE_CACHE=1
```

**清理 Docker 镜像缓存**:
```bash
# 清理所有未使用的镜像
docker image prune -a

# 清理构建缓存
docker builder prune
```

### 镜像推送优化

**使用 TCR 加速域名**:
```bash
# 广州地域加速
export TCR_REGISTRY="ccr.ccs.tencentyun.com"

# 或使用特定地域镜像加速
# export TCR_REGISTRY="ccr-gz.tencentyun.com"
```

### 部署监控优化

**实时监控 Pod 状态**:
```bash
# 监听 Pod 变化
kubectl get pods -n ppt-rsd-prod -w

# 查看实时资源使用
kubectl top pods -n ppt-rsd-prod

# 查看 Pod 描述（包含事件）
kubectl describe pod <pod-name> -n ppt-rsd-prod
```

## 最佳实践

1. **总是先验证**: 运行 `deploy-validate.sh` 在实际部署前
2. **从测试开始**: 先部署到测试环境，验证成功后再部署生产
3. **使用灰度部署**: 对于大功能发布，使用 `deploy-canary.sh`
4. **保持日志**: 所有部署日志自动保存，用于问题排查
5. **监控应用**: 部署后立即检查应用日志和指标
6. **文档化更改**: 记录每次部署的原因和结果

## 常用命令参考

```bash
# 检查部署状态
kubectl get deployments -n ppt-rsd-prod

# 查看 Pod 详情
kubectl describe pod -n ppt-rsd-prod

# 查看实时日志
kubectl logs -f deployment/ppt-backend -n ppt-rsd-prod

# 进入 Pod 交互式 shell
kubectl exec -it <pod-name> -n ppt-rsd-prod -- /bin/bash

# 检查 Pod 资源使用
kubectl top pod -n ppt-rsd-prod

# 获取部署资源 YAML
kubectl get deployment ppt-backend -n ppt-rsd-prod -o yaml

# 编辑部署配置
kubectl edit deployment ppt-backend -n ppt-rsd-prod

# 查看部署事件
kubectl get events -n ppt-rsd-prod --sort-by='.lastTimestamp'
```

## 联系和支持

如有问题或建议，请参考：
- 部署日志: `deployment/logs/`
- 优化计划: `OPTIMIZATION_PLAN.md`
- 分析报告: `deployment/DEPLOYMENT_STANDALONE.md`

---

**文档版本**: v1.0
**最后更新**: 2025-03-18
**脚本版本**: 优化版 (Parallel, Reliable, Observability)
