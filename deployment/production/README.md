# PPT-RSD 生产环境部署指南

## 架构概览

```
                    ┌─────────────────────────────────────┐
                    │      ppt.bottlepeace.com (443)      │
                    │         用户访问入口                  │
                    └─────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                  │
                    ▼                                  ▼
        ┌───────────────────┐            ┌───────────────────┐
        │   CDN (前端)       │            │  API 网关 (后端)   │
        │   HTTPS :443      │            │   HTTPS :443      │
        └───────────────────┘            └───────────────────┘
                    │                                  │
                    ▼                                  ▼
        ┌───────────────────┐            ┌───────────────────┐
        │   COS 存储桶       │            │   SCF 云函数       │
        │   静态资源托管     │            │   FastAPI 后端     │
        └───────────────────┘            └───────────────────┘
```

## 固定配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 前端域名 | `ppt.bottlepeace.com` | 通过 CDN 访问 |
| API 域名 | `api.ppt.bottlepeace.com` | 通过 API 网关访问 |
| 前端端口 | `443` (HTTPS) | 固定，不会变化 |
| 后端端口 | `443` (HTTPS) | 固定，不会变化 |
| 地域 | `ap-guangzhou` | 广州 |

## 部署步骤

### 1. 前置条件

#### 1.1 腾讯云资源准备

在腾讯云控制台创建以下资源：

1. **COS 存储桶**
   - 名称: `ppt-rsd-frontend-<AppID>`
   - 地域: 广州
   - 权限: 公有读私有写
   - 开启静态网站托管

2. **CDN 加速域名**
   - 域名: `ppt.bottlepeace.com`
   - 源站: COS 存储桶域名
   - 开启 HTTPS（需要 SSL 证书）

3. **SCF 云函数**
   - 名称: `ppt-rsd-backend`
   - 类型: Web 函数
   - 运行时: Python 3.9
   - 内存: 512MB
   - 超时: 30s

4. **API 网关**
   - 服务名: `ppt-rsd-api`
   - 绑定云函数
   - 自定义域名: `api.ppt.bottlepeace.com`

#### 1.2 DNS 配置

在域名服务商处添加以下 CNAME 记录：

```
ppt.bottlepeace.com     -> CNAME -> <CDN加速域名>.cdn.dnsv1.com
api.ppt.bottlepeace.com -> CNAME -> <API网关域名>.apigw.tencentcs.com
```

#### 1.3 SSL 证书

为以下域名申请 SSL 证书（可使用腾讯云免费证书）：
- `ppt.bottlepeace.com`
- `api.ppt.bottlepeace.com`

### 2. 手动部署

```bash
# 进入部署目录
cd deployment/production

# 部署前端
./deploy.sh frontend

# 部署后端
./deploy.sh backend

# 查看部署信息
./deploy.sh info
```

### 3. CI/CD 自动部署

#### 3.1 配置 Secrets

在 GitHub 仓库或 CODING 项目中配置以下 Secrets：

| Secret 名称 | 说明 |
|-------------|------|
| `TENCENT_SECRET_ID` | 腾讯云 API SecretId |
| `TENCENT_SECRET_KEY` | 腾讯云 API SecretKey |

#### 3.2 触发部署

- **自动触发**: 推送代码到 `main` 或 `master` 分支
- **手动触发**: 在 GitHub Actions 页面点击 "Run workflow"

## 配置文件说明

```
deployment/production/
├── config.env          # 环境变量配置
├── deploy.sh           # 部署脚本
└── README.md           # 本文档

.github/workflows/
└── deploy-production.yml  # CI/CD 流水线配置
```

## 环境变量

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `STAGE` | `prod` | 部署环境 |
| `REGION` | `ap-guangzhou` | 腾讯云地域 |
| `FRONTEND_DOMAIN` | `ppt.bottlepeace.com` | 前端域名 |
| `API_DOMAIN` | `api.ppt.bottlepeace.com` | API 域名 |

## 访问地址

| 服务 | URL |
|------|-----|
| 前端 | https://ppt.bottlepeace.com |
| API | https://api.ppt.bottlepeace.com |
| API 文档 | https://api.ppt.bottlepeace.com/docs |
| 健康检查 | https://api.ppt.bottlepeace.com/health |

## 常见问题

### Q: 前端访问显示 403？
A: 检查 COS 存储桶权限是否为"公有读"，检查静态网站托管是否开启。

### Q: API 返回 502？
A: 检查 SCF 函数日志，可能是代码错误或依赖缺失。

### Q: HTTPS 证书错误？
A: 检查 SSL 证书是否正确配置，域名是否匹配。

### Q: DNS 解析不生效？
A: DNS 记录可能需要几分钟到几小时生效，请耐心等待。

## 监控与日志

- **SCF 函数日志**: 腾讯云控制台 > 云函数 > 日志查询
- **CDN 日志**: 腾讯云控制台 > CDN > 日志管理
- **API 网关日志**: 腾讯云控制台 > API 网关 > 运行监控
