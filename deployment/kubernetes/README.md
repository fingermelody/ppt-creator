# PPT-RSD Kubernetes 部署指南

## 📋 前置条件

1. 已安装 Docker
2. 已配置 kubectl 连接到 TKE 集群
3. 已开通腾讯云容器镜像服务 (TCR)

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    腾讯云 TKE                            │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │           Ingress (nginx-ingress)                │  │
│  │           api.ppt.bottlepeace.com                │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                  │
│  ┌────────────────────▼─────────────────────────────┐  │
│  │        Service (ppt-rsd-backend)                 │  │
│  │               ClusterIP:8000                     │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                  │
│  ┌────────────────────▼─────────────────────────────┐  │
│  │        Deployment (ppt-rsd-backend)              │  │
│  │           Replicas: 2                            │  │
│  │           Image: ccr.../backend:latest           │  │
│  └────────────────────┬─────────────────────────────┘  │
│                       │                                  │
└───────────────────────┼──────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼─────┐ ┌───────▼──────┐
│  TDSQL-C     │ │   Redis   │ │     COS      │
│  (MySQL)     │ │           │ │  (Storage)   │
│  内网连接    │ │  内网连接 │ │  公网访问    │
└──────────────┘ └───────────┘ └──────────────┘
```

## 🚀 快速部署

### 方式一：一键部署（推荐）

```bash
# 进入部署目录
cd deployment/kubernetes

# 执行完整部署（构建镜像 + 推送 + 部署）
./deploy.sh all
```

### 方式二：分步部署

```bash
# 1. 构建 Docker 镜像
./deploy.sh build

# 2. 推送到镜像仓库
./deploy.sh push

# 3. 部署到 Kubernetes
./deploy.sh deploy
```

## 📝 详细步骤

### 1. 配置镜像仓库

登录腾讯云容器镜像服务：

```bash
# 登录 TCR
docker login --username=<your-account> ccr.ccs.tencentyun.com

# 或使用腾讯云 CLI
tccli cr login
```

### 2. 更新配置

编辑 `configmap.yaml`，更新数据库和 Redis 连接信息：

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ppt-rsd-config
data:
  DATABASE_HOST: "your-mysql-host"
  DATABASE_PORT: "3306"
  DATABASE_NAME: "ppt_rsd"
  # ...
```

编辑 `configmap.yaml` 中的 Secret，更新敏感信息：

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ppt-rsd-secrets
type: Opaque
stringData:
  DATABASE_USER: "your-username"
  DATABASE_PASSWORD: "your-password"
  SECRET_KEY: "your-secret-key"
  # ...
```

### 3. 构建和推送镜像

```bash
# 设置镜像标签
export IMAGE_TAG=v1.0.0

# 构建
./deploy.sh build

# 推送
./deploy.sh push
```

### 4. 部署到集群

```bash
# 部署
./deploy.sh deploy

# 查看状态
./deploy.sh status
```

## 🔧 管理命令

### 查看部署状态

```bash
./deploy.sh status
```

或使用 kubectl：

```bash
# 查看 Pod 状态
kubectl get pods -l app=ppt-rsd-backend

# 查看服务
kubectl get svc ppt-rsd-backend

# 查看 Ingress
kubectl get ingress ppt-rsd-ingress

# 查看日志
kubectl logs -f deployment/ppt-rsd-backend
```

### 扩容/缩容

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

### 回滚部署

```bash
# 回滚到上一个版本
./deploy.sh rollback

# 或使用 kubectl
kubectl rollout undo deployment/ppt-rsd-backend

# 回滚到指定版本
kubectl rollout undo deployment/ppt-rsd-backend --to-revision=2
```

### 删除部署

```bash
./deploy.sh delete
```

## 🔍 故障排查

### Pod 无法启动

```bash
# 查看 Pod 状态
kubectl describe pod <pod-name>

# 查看日志
kubectl logs <pod-name>

# 查看事件
kubectl get events --sort-by=.metadata.creationTimestamp
```

### 数据库连接失败

1. 检查 ConfigMap 中的数据库地址是否正确
2. 检查 Secret 中的用户名密码是否正确
3. 检查安全组是否允许 TKE 集群访问数据库

```bash
# 测试数据库连接
kubectl run mysql-client --rm -it --image=mysql:8.0 -- \
  mysql -h <DATABASE_HOST> -u <DATABASE_USER> -p<DATABASE_PASSWORD>
```

### 镜像拉取失败

```bash
# 检查镜像是否存在
docker pull ccr.ccs.tencentyun.com/ppt-rsd/backend:latest

# 检查镜像仓库认证
kubectl get secrets -n default
```

### Ingress 无法访问

1. 检查 Ingress Controller 是否正常运行
2. 检查域名解析是否指向 LoadBalancer IP
3. 检查 SSL 证书配置（如需 HTTPS）

```bash
# 查看 Ingress 详情
kubectl describe ingress ppt-rsd-ingress

# 查看 Ingress Controller 日志
kubectl logs -n kube-system deployment/nginx-ingress-controller
```

## 📊 监控和日志

### 查看日志

```bash
# 实时查看日志
kubectl logs -f deployment/ppt-rsd-backend

# 查看最近 100 行日志
kubectl logs deployment/ppt-rsd-backend --tail=100

# 查看指定 Pod 的日志
kubectl logs <pod-name>
```

### 监控指标

Kubernetes 内置监控：

```bash
# 查看 Pod 资源使用
kubectl top pods

# 查看节点资源使用
kubectl top nodes
```

## 🔐 安全配置

### 1. Secret 管理

**不要**将 Secret 提交到 Git 仓库。使用以下方式管理：

```bash
# 从文件创建 Secret
kubectl create secret generic ppt-rsd-secrets \
  --from-literal=DATABASE_USER=username \
  --from-literal=DATABASE_PASSWORD=password \
  --from-literal=SECRET_KEY=secret-key

# 或从 .env 文件创建
kubectl create secret generic ppt-rsd-secrets --from-env-file=.env
```

### 2. 网络安全

确保 TKE 集群和数据库在同一 VPC：

```bash
# 检查 VPC 配置
kubectl get nodes -o wide
```

### 3. RBAC 配置（可选）

为应用创建专用 ServiceAccount：

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ppt-rsd-backend
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ppt-rsd-backend
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get", "list"]
```

## 🌐 域名配置

### 1. DNS 解析

在 DNS 服务商处添加 A 记录：

```
api.ppt.bottlepeace.com -> <LoadBalancer-IP>
```

### 2. HTTPS 配置（可选）

使用 cert-manager 自动管理 SSL 证书：

```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: ppt-rsd-cert
spec:
  secretName: ppt-rsd-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.ppt.bottlepeace.com
```

更新 Ingress：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ppt-rsd-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.ppt.bottlepeace.com
    secretName: ppt-rsd-tls
  rules:
  - host: api.ppt.bottlepeace.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ppt-rsd-backend
            port:
              number: 8000
```

## 📚 相关文档

- [TKE 产品文档](https://cloud.tencent.com/document/product/457)
- [容器镜像服务 TCR](https://cloud.tencent.com/document/product/1141)
- [Kubernetes 官方文档](https://kubernetes.io/docs/)

## 🆘 常见问题

### Q: 如何查看应用是否正常运行？

A: 访问健康检查端点：

```bash
curl http://api.ppt.bottlepeace.com/health
```

### Q: 如何更新配置？

A: 修改 ConfigMap 后重启 Pod：

```bash
kubectl rollout restart deployment/ppt-rsd-backend
```

### Q: 如何查看容器内的文件？

A: 使用 kubectl exec：

```bash
kubectl exec -it deployment/ppt-rsd-backend -- /bin/bash
```

### Q: 如何备份数据库？

A: 使用 mysqldump：

```bash
kubectl run mysql-client --rm -it --image=mysql:8.0 -- \
  mysqldump -h <DATABASE_HOST> -u <DATABASE_USER> -p<DATABASE_PASSWORD> \
  ppt_rsd > backup.sql
```
