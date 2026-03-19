# GitHub Actions 流水线配置

## 所需 Secrets 配置

在 GitHub 仓库 Settings -> Secrets and variables -> Actions 中添加以下 secrets：

| Secret Name | 说明 | 获取方式 |
|------------|------|---------|
| `TENCENT_SECRET_ID` | 腾讯云 SecretId | 腾讯云控制台 - API密钥管理 |
| `TENCENT_SECRET_KEY` | 腾讯云 SecretKey | 腾讯云控制台 - API密钥管理 |
| `TCR_USERNAME` | TCR 用户名 | 腾讯云容器镜像服务 |
| `TCR_PASSWORD` | TCR 密码 | 腾讯云容器镜像服务 |
| `TKE_CLUSTER_ID` | TKE 集群 ID | 腾讯云容器服务控制台 |

## 流水线流程

```
代码提交
    │
    ├──→ 前端构建 (build-frontend)
    │
    ├──→ 后端测试 (test-backend)
    │
    └──→ 镜像构建与推送 (build-and-push)
                │
                └──→ 部署到 TKE (deploy-to-tke)
```

## 环境说明

- **develop 分支**: 触发测试流程，不部署
- **main 分支**: 触发完整流程并部署到生产环境
