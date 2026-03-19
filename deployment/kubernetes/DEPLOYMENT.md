# PPT-RSD TKE 部署文档

## 部署概览

本项目使用腾讯云 TKE (Tencent Kubernetes Engine) 进行容器化部署。

### 架构

```
┌─────────────────────────────────────────┐
│          Ingress (nginx-ingress)         │
│          api.ppt.bottlepeace.com         │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Service (ppt-rsd-backend)           │
│              ClusterIP:8000              │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│      Deployment (ppt-rsd-backend)        │
│          Replicas: 2                     │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐  ┌───▼───┐  ┌────▼────┐
│ MySQL │  │ Redis │  │   COS   │
└───────┘  └───────┘  └─────────┘
```

## 部署步骤

### 1. 准备工作

确保已安装：
- Docker
- kubectl
- 腾讯云 CLI (可选)

### 2. 配置镜像仓库

```bash
# 登录腾讯云容器镜像服务
docker login --username=<账号> ccr.ccs.tencentyun.com
```

### 3. 配置 Kubernetes

```bash
# 配置 kubectl 连接到 TKE 集群
# 方式1: 从 TKE 控制台下载 kubeconfig
# 方式2: 使用腾讯云 CLI
tke region set ap-guangzhou
tke cluster credentials <cluster-id>
```

### 4. 更新配置

编辑 `deployment/kubernetes/configmap.yaml`，更新以下配置：

```yaml
# 数据库配置
DATABASE_HOST: "your-mysql-host"
DATABASE_USER: "your-username"  # 在 Secret 中
DATABASE_PASSWORD: "your-password"  # 在 Secret 中

# Redis 配置
REDIS_HOST: "your-redis-host"

# COS 配置
COS_BUCKET: "your-bucket-name"
```

### 5. 构建和推送镜像

```bash
# 使用部署脚本
cd deployment/kubernetes
./deploy.sh all

# 或手动执行
./deploy.sh build
./deploy.sh push
```

### 6. 部署到 TKE

```bash
./deploy.sh deploy
```

### 7. 验证部署

```bash
# 查看部署状态
kubectl get pods -l app=ppt-rsd-backend

# 查看服务
kubectl get svc

# 查看 Ingress
kubectl get ingress

# 查看日志
kubectl logs -f deployment/ppt-rsd-backend
```

## 文件说明

```
deployment/kubernetes/
├── configmap.yaml           # ConfigMap 和 Secret 配置
├── backend-deployment.yaml  # 后端 Deployment
├── service-ingress.yaml     # Service 和 Ingress
├── deploy.sh                # 部署脚本
├── quick-build.sh           # 快速构建脚本
└── README.md                # 部署文档
```

## 常用命令

### 查看状态

```bash
# 查看 Pod 状态
kubectl get pods -l app=ppt-rsd-backend

# 查看详细信息
kubectl describe pod <pod-name>

# 查看日志
kubectl logs -f deployment/ppt-rsd-backend

# 查看事件
kubectl get events --sort-by=.metadata.creationTimestamp
```

### 扩缩容

```bash
# 扩容到 3 个副本
kubectl scale deployment ppt-rsd-backend --replicas=3

# 缩容到 1 个副本
kubectl scale deployment ppt-rsd-backend --replicas=1
```

### 更新部署

```bash
# 更新镜像
kubectl set image deployment/ppt-rsd-backend \
  backend=ccr.ccs.tencentyun.com/ppt-rsd/backend:new-tag

# 查看更新状态
kubectl rollout status deployment/ppt-rsd-backend
```

### 回滚

```bash
# 回滚到上一个版本
kubectl rollout undo deployment/ppt-rsd-backend

# 查看历史版本
kubectl rollout history deployment/ppt-rsd-backend

# 回滚到指定版本
kubectl rollout undo deployment/ppt-rsd-backend --to-revision=2
```

## CI/CD 配置

### GitHub Actions

1. 在 GitHub 仓库设置中添加以下 Secrets:
   - `TCR_USERNAME`: 腾讯云镜像仓库用户名
   - `TCR_PASSWORD`: 腾讯云镜像仓库密码
   - `KUBE_CONFIG`: Base64 编码的 kubeconfig 文件

2. 推送到 main 分支会自动触发部署

### 获取 kubeconfig

```bash
# 从 TKE 控制台下载 kubeconfig 文件
# 然后进行 Base64 编码
cat kubeconfig | base64 > kubeconfig.b64

# 将 kubeconfig.b64 的内容设置为 GitHub Secret
```

## 故障排查

### Pod 无法启动

```bash
# 查看 Pod 状态
kubectl describe pod <pod-name>

# 查看日志
kubectl logs <pod-name>

# 进入容器调试
kubectl exec -it <pod-name> -- /bin/bash
```

### 数据库连接失败

1. 检查 ConfigMap 和 Secret 配置
2. 检查网络连通性（安全组、VPC）
3. 检查数据库用户权限

```bash
# 测试数据库连接
kubectl run mysql-client --rm -it --image=mysql:8.0 -- \
  mysql -h <host> -u <user> -p<password>
```

### 镜像拉取失败

```bash
# 检查镜像是否存在
docker pull ccr.ccs.tencentyun.com/ppt-rsd/backend:latest

# 检查 imagePullSecrets
kubectl get secrets
```

## 监控和日志

### 日志查看

```bash
# 实时日志
kubectl logs -f deployment/ppt-rsd-backend

# 最近 100 行
kubectl logs deployment/ppt-rsd-backend --tail=100

# 多容器日志
kubectl logs -l app=ppt-rsd-backend
```

### 资源监控

```bash
# Pod 资源使用
kubectl top pods

# 节点资源使用
kubectl top nodes
```

## 安全建议

1. **不要提交 Secret 到 Git**
2. 使用腾讯云密钥管理服务 (KMS) 管理敏感信息
3. 配置网络策略限制 Pod 间通信
4. 定期更新基础镜像版本
5. 启用容器镜像扫描

## 成本优化

1. 合理设置副本数（建议 2-3 个）
2. 使用合适的资源限制
3. 配置 HPA (Horizontal Pod Autoscaler)
4. 使用 Spot 实例降低成本

## 联系支持

如有问题，请联系：
- 技术支持: support@bottlepeace.com
- 文档维护: PPT-RSD Team
