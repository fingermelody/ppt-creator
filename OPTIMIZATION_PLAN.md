# PPT-RSD 腾讯云部署优化方案

## 一、优化目标

在现有腾讯云基础设施基础上，通过脚本和流程优化实现：

1. **性能提升**: 部署时间减少 30-40%
2. **可靠性**: 99.9% 成功率，自动化故障恢复
3. **安全性**: 完整的密钥管理、审计日志
4. **成本**: 优化资源利用率，降低月度 10-15%
5. **可维护性**: 清晰的流程，完善的文档

## 二、现有基础设施回顾

### 腾讯云资源清单

| 组件 | 配置 | 地域 |
|------|------|------|
| **TKE 集群** | EKS Serverless (cls-1lvwzqie) | 广州 7 区 |
| **MySQL** | TDSQL-C Serverless (10.6.1.13:3306) | 内网 |
| **Redis** | 256MB (10.6.1.42:6379) | 内网 |
| **对象存储** | COS (ppt-creator-store-1253851367) | 广州 |
| **镜像仓库** | TCR (ccr.ccs.tencentyun.com/codebuddy-ppt-creator) | 广州 |
| **向量搜索** | ES Serverless (space-k4t5xi0i) | 广州 |
| **VPC** | vpc-gjkbluhz | 广州 |

### 当前部署流程

```
1. 环境变量校验
2. 工具检查 (kubectl, docker, tccli)
3. TKE 凭证配置
4. 后端镜像构建 (sequential)
5. 后端镜像推送
6. 前端镜像构建 (sequential)
7. 前端镜像推送
8. K8s 部署更新
9. 等待 Rollout (300s)
10. 健康检查
```

**总耗时**: ~5-8 分钟（不含构建时间）

## 三、优化方案详解

### 3.1 镜像构建优化

#### 3.1.1 后端 Dockerfile 多阶段构建

**问题**: 构建依赖 (gcc, libpq-dev) 被包含在最终镜像中

**当前**:
```dockerfile
FROM python:3.11-slim
RUN apt-get install gcc libpq-dev  # 留在最终镜像
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
```

**优化后** (multi-stage):
```dockerfile
# 构建阶段
FROM python:3.11-slim AS builder
RUN apt-get install gcc libpq-dev
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 运行阶段 (仅包含运行时依赖)
FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
COPY app/ ./app
ENV PATH=/root/.local/bin:$PATH
```

**收益**:
- 镜像大小: 1GB → 400MB (-60%)
- 推送时间: -40% (更小的镜像)
- 拉取时间: -40% (不含编译工具)

#### 3.1.2 前端 Dockerfile 优化

**当前** (已是多阶段，但可优化):
```dockerfile
FROM node:18-alpine AS builder
# 构建会安装所有 devDependencies
RUN npm ci  # 包含 devDependencies

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

**优化点**:
1. 使用 npm ci --production 在最终阶段
2. 缩小基础镜像 (考虑 nginx:alpine-slim 或定制)
3. 合并 Nginx 配置到 Dockerfile (避免 COPY 多个文件)

#### 3.1.3 并行构建

**当前** (顺序执行): 
```bash
# deploy.sh 第 134-145 行
docker build -t backend ...  # 等待
docker push backend          # 等待
docker build -t frontend ... # 等待
docker push frontend         # 等待
```

**优化后** (并行执行):
```bash
# 后台启动后端构建
(docker build -t backend ... && docker push backend) &
BACKEND_PID=$!

# 后台启动前端构建
(docker build -t frontend ... && docker push frontend) &
FRONTEND_PID=$!

# 等待两个并行任务
wait $BACKEND_PID || handle_error
wait $FRONTEND_PID || handle_error
```

**收益**: 部署时间 -30% (5 分钟 → 3.5 分钟)

#### 3.1.4 Docker BuildKit 缓存

**当前**: 本地 deploy.sh 未使用 BuildKit

**优化**:
```bash
export DOCKER_BUILDKIT=1
export BUILDKIT_INLINE_CACHE=1

docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --cache-from ccr.ccs.tencentyun.com/.../backend:latest \
  -t backend ...
```

**收益**: 增量构建 -80% (有缓存命中)

### 3.2 部署可靠性增强

#### 3.2.1 部署前验证 (Pre-flight Checks)

**新增脚本**: `deployment/scripts/deploy-validate.sh`

验证项:
```bash
# 1. 集群连接性
kubectl cluster-info

# 2. 镜像存在性
docker manifest inspect $BACKEND_IMAGE

# 3. Namespace 就绪
kubectl get ns $NAMESPACE

# 4. 资源配额充足
kubectl describe resourcequota -n $NAMESPACE

# 5. 节点可用性
kubectl get nodes --no-headers

# 6. 存储卷就绪
kubectl get pvc -n $NAMESPACE

# 7. 环境变量完整性
verify_env_vars

# 8. Secret 存在性
kubectl get secret ppt-rsd-secrets -n $NAMESPACE

# 9. 数据库连接性
curl -X GET http://backend:8000/health || true

# 10. Redis 连接性
redis-cli -h $REDIS_HOST ping
```

#### 3.2.2 部署事务性

**问题**: 后端成功 + 前端失败 = 系统不一致

**解决方案** (deploy.sh):
```bash
# 准备阶段 (仅验证，不修改)
prepare_deployment() {
  kubectl set image deployment/ppt-backend \
    --dry-run=client backend=$BACKEND_IMAGE
  kubectl set image deployment/ppt-frontend \
    --dry-run=client frontend=$FRONTEND_IMAGE
}

# 提交阶段 (全部成功或全部回滚)
commit_deployment() {
  kubectl set image deployment/ppt-backend \
    backend=$BACKEND_IMAGE
  kubectl set image deployment/ppt-frontend \
    frontend=$FRONTEND_IMAGE
  
  # 等待两个都就绪
  kubectl rollout status deployment/ppt-backend ...
  kubectl rollout status deployment/ppt-frontend ...
}

# 回滚阶段
rollback_deployment() {
  kubectl rollout undo deployment/ppt-backend
  kubectl rollout undo deployment/ppt-frontend
}
```

#### 3.2.3 健康检查探针

**K8s 部署清单优化**:
```yaml
spec:
  template:
    spec:
      containers:
      - name: backend
        image: $BACKEND_IMAGE
        
        # 就绪探针 (启动 5s 后，每 10s 检查一次)
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          successThreshold: 1
          failureThreshold: 3
        
        # 存活探针 (启动 15s 后，每 30s 检查一次)
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        
        # 启动探针 (最多等待 60s 启动)
        startupProbe:
          httpGet:
            path: /health/startup
            port: 8000
          periodSeconds: 10
          failureThreshold: 6
        
        # 优雅关闭
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 15"]
        
        terminationGracePeriodSeconds: 30
```

#### 3.2.4 自动回滚

**新增脚本**: `deployment/scripts/deploy-canary.sh`

灰度部署策略:
```
第一阶段 (10% 流量):
  - 部署新版本到 1 个副本
  - 监控指标 (错误率、延迟)
  - 等待 3 分钟

第二阶段 (25% 流量):
  - 扩展到 2 个副本
  - 监控指标
  - 等待 5 分钟

第三阶段 (50% 流量):
  - 扩展到 3 个副本
  - 监控指标
  - 等待 5 分钟

第四阶段 (100% 流量):
  - 全量部署

如果任何阶段指标异常:
  - 立即回滚到上一版本
  - 发送告警
```

### 3.3 K8s 清单优化

**从嵌入式脚本迁移到版本控制的 YAML**:

```
deployment/
├── kustomize/
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   ├── configmap.yaml
│   │   └── service.yaml
│   ├── overlays/
│   │   ├── prod/
│   │   │   ├── kustomization.yaml
│   │   │   └── replicas-patch.yaml
│   │   └── test/
│   │       ├── kustomization.yaml
│   │       └── replicas-patch.yaml
│   └── app-resources.yaml
```

**优势**:
- 版本控制清晰
- 环境特定配置 (prod vs test)
- 易于审查和维护
- 支持 GitOps 工作流

### 3.4 腾讯云特定优化

#### 3.4.1 TCR 镜像加速

```bash
# 广州地域加速域名
TCR_ACCELERATE_DOMAIN="ccr.ccs.tencentyun.com"

# 使用加速拉取
kubectl set image deployment/ppt-backend \
  backend="${TCR_ACCELERATE_DOMAIN}/...backup:tag@sha256:..."
```

#### 3.4.2 TKE 网络优化

```yaml
# 启用 CNI 高性能模式
apiVersion: tke.cloud.tencent.com/v1beta1
kind: ClusterAddon
metadata:
  name: network-optimization
spec:
  enableCNIEnhanced: true
  enableBPFForward: true
```

#### 3.4.3 成本优化标签

```yaml
# 为所有资源添加成本标签
metadata:
  labels:
    cost-center: "product"
    environment: "production"
    team: "ppt-platform"
    cost-optimization: "enabled"
```

### 3.5 GitHub Actions 优化

#### 3.5.1 测试并行化

**当前**: 顺序执行 (lint → test → security)

**优化**: 并行执行前端和后端 lint/test
```yaml
jobs:
  lint-frontend:
    runs-on: ubuntu-latest
  lint-backend:
    runs-on: ubuntu-latest
  test-backend:
    runs-on: ubuntu-latest
    needs: lint-backend
  security:
    runs-on: ubuntu-latest
    needs: [lint-backend, lint-frontend]
```

**收益**: CI 时间 -40%

#### 3.5.2 构建缓存优化

```yaml
- name: Build and push backend
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha,scope=backend
    cache-to: type=gha,mode=max,scope=backend
    
- name: Build and push frontend
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha,scope=frontend
    cache-to: type=gha,mode=max,scope=frontend
```

#### 3.5.3 部署批准流程

```yaml
deploy-prod:
  environment:
    name: production
    url: https://ppt.bottlepeace.com
    deployment-branch-policy:
      protected-branches: true
      custom-deployment-branches: false
  # 需要人工批准后才执行
```

#### 3.5.4 部署通知增强

```yaml
- name: Notify on Slack
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "🚀 PPT-RSD 生产部署",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "部署完成: ${{ needs.build.outputs.image_tag }}"
            }
          }
        ]
      }
```

## 四、数据库和缓存优化

### 4.1 连接池配置

**Backend 优化** (app/config.py):
```python
from sqlalchemy.pool import QueuePool

# SQLAlchemy 连接池
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,           # 连接池大小
    max_overflow=10,        # 最大溢出连接
    pool_pre_ping=True,     # 连接前验证
    pool_recycle=3600,      # 连接回收周期
    echo=False
)
```

**Redis 连接池**:
```python
import redis

redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=6379,
    db=0,
    max_connections=50,
    socket_keepalive=True,
    socket_keepalive_options=socket_options
)
```

### 4.2 查询优化

监控项:
- 慢查询日志 (MySQL 设置 long_query_time)
- Redis 命中率
- 连接池使用率

### 4.3 缓存策略

```python
# 缓存键规范
CACHE_KEYS = {
    "ppt_template": "ppt:template:{template_id}",
    "ppt_config": "ppt:config:{config_id}",
    "user_settings": "user:settings:{user_id}",
}

# TTL 配置
CACHE_TTL = {
    "template": 3600,      # 1 小时
    "config": 1800,        # 30 分钟
    "settings": 86400,     # 1 天
    "session": 604800,     # 7 天
}
```

## 五、监控和告警

### 5.1 关键指标

```yaml
# 部署成功率
deployment_success_rate: (成功部署 / 总部署) × 100%

# 部署时间
deployment_duration:
  - 镜像构建时间
  - 镜像推送时间
  - K8s 部署时间
  - 总时间

# 应用可用性
app_uptime: (在线时间 / 总时间) × 100%

# 错误率
error_rate: 错误请求 / 总请求

# 响应延迟 (P50, P95, P99)
response_latency_p95: < 200ms (目标)

# 资源利用率
cpu_usage: < 70% (告警 > 80%)
memory_usage: < 75% (告警 > 85%)
```

### 5.2 Tencent Cloud Monitor 集成

```bash
# 发送自定义指标
tccli monitor PutMonitorData \
  --Namespace "PPT-RSD" \
  --MetricData.0.MetricName "DeploymentDuration" \
  --MetricData.0.Value 240 \
  --MetricData.0.Timestamp $UNIX_TIMESTAMP
```

## 六、安全加固

### 6.1 密钥管理

**当前** (不推荐):
```bash
echo "$TCR_PASSWORD" | docker login
```

**优化后** (使用腾讯云密钥管理):
```bash
# 从 TCS (腾讯云密钥管理服务) 获取密钥
SECRET=$(tccli kms GetSecretValue \
  --SecretId "ppt-tcr-password" \
  --VersionId "current")

echo "$SECRET" | docker login
```

### 6.2 RBAC 配置

```yaml
# K8s ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ppt-deployment
  namespace: ppt-rsd-prod

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ppt-deployment
  namespace: ppt-rsd-prod
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "patch", "update"]
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ppt-deployment
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ppt-deployment
subjects:
- kind: ServiceAccount
  name: ppt-deployment
```

### 6.3 审计日志

```yaml
# 启用审计日志
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  verbs: ["create", "patch", "update", "delete"]
  resources: ["deployments", "services"]
```

## 七、成本分析

### 7.1 优化前成本 (月度)

| 组件 | 成本 |
|------|------|
| EKS Serverless | ¥0 (共享) |
| TDSQL-C | ¥30-80 |
| Redis 256MB | ¥56 |
| ES Serverless | ¥0 (共享) |
| COS | ¥10 |
| **合计** | **¥96-146** |

### 7.2 优化后成本 (预期)

通过以下措施:
1. 镜像大小 -60% → 存储费 -10%
2. 自动扩缩容 → 不需扩容 (保持现状)
3. Redis 监控 → 可能升级或降级
4. 数据库连接优化 → 可能减少超额费用

**预期总成本**: ¥86-136 (-10%)

## 八、实施计划

### Phase 1: 基础优化 (第 1-2 周)

- [x] 分析现有脚本 ✓
- [ ] 后端 Dockerfile 多阶段化
- [ ] 前端 Dockerfile 优化
- [ ] 并行构建脚本
- [ ] 部署前验证脚本

### Phase 2: 可靠性增强 (第 3-4 周)

- [ ] 健康检查探针配置
- [ ] 事务性部署实现
- [ ] 自动回滚逻辑
- [ ] Kustomize 清单迁移

### Phase 3: 监控和安全 (第 5-6 周)

- [ ] Tencent Cloud Monitor 集成
- [ ] 审计日志配置
- [ ] 密钥管理优化
- [ ] 告警规则配置

### Phase 4: 文档和培训 (第 7-8 周)

- [ ] 部署最佳实践文档
- [ ] 故障排查指南
- [ ] 团队培训

## 九、成功指标

部署优化完成后的验收标准:

| 指标 | 目标 | 当前 |
|------|------|------|
| 部署时间 | < 3 分钟 | 5-8 分钟 |
| 成功率 | > 99% | ~95% |
| 回滚时间 | < 1 分钟 | 手动 |
| 镜像大小 | < 500MB | 1GB+ |
| 健康检查 | 自动化 | 手动 |
| 监控覆盖 | 100% | 50% |

## 十、风险评估和缓解

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 并行构建失败 | 低 | 高 | 添加错误处理和回滚 |
| 灰度部署卡住 | 低 | 中 | 手动干预选项 |
| 数据库连接池溢出 | 中 | 中 | 监控和自动扩展 |
| 镜像推送失败 | 低 | 高 | 重试机制和备用仓库 |

---

**文档版本**: v1.0
**最后更新**: 2025-03-18
**作者**: CodeBuddy
**状态**: 待审批
