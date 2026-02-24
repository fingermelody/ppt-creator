# 腾讯云 SCF 部署指南

本目录包含将 PPT-RSD 项目部署到腾讯云 SCF（Serverless Cloud Function）的配置文件。

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│                       用户访问                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │        CDN / 自定义域名         │
              └───────────────────────────────┘
                     │               │
                     ▼               ▼
        ┌────────────────┐   ┌────────────────┐
        │  COS 静态网站    │   │   API 网关      │
        │  (前端资源)      │   │  (后端 API)     │
        └────────────────┘   └────────────────┘
                                    │
                                    ▼
                          ┌────────────────┐
                          │  SCF Web 函数   │
                          │  (FastAPI)     │
                          └────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
             ┌──────────┐    ┌──────────┐    ┌──────────┐
             │  MySQL   │    │  Redis   │    │   COS    │
             └──────────┘    └──────────┘    └──────────┘
```

## 部署组件

| 组件 | 腾讯云服务 | 说明 |
|------|-----------|------|
| 前端 | COS + CDN | 静态网站托管 |
| 后端 API | SCF Web 函数 | FastAPI 应用 |
| 异步任务 | SCF 事件函数 | PPT 处理、向量化 |
| 数据库 | 云数据库 MySQL | 业务数据存储 |
| 缓存 | 云数据库 Redis | 会话和缓存 |
| 文件存储 | COS | PPT 文件存储 |

## 快速开始

### 1. 前提条件

- 腾讯云账号并开通相关服务
- Node.js >= 16
- Python >= 3.9
- Serverless Framework CLI

### 2. 安装 Serverless Framework

```bash
npm install -g serverless
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填写实际配置
vim .env
```

### 4. 部署

```bash
# 部署到开发环境
./deploy.sh deploy dev

# 部署到生产环境
./deploy.sh deploy prod
```

### 5. 查看部署信息

```bash
./deploy.sh info prod
```

## 环境变量说明

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `STAGE` | 部署环境 | `dev` / `test` / `prod` |
| `REGION` | 腾讯云地域 | `ap-guangzhou` |
| `DATABASE_URL` | MySQL 连接字符串 | `mysql+pymysql://user:pass@host:3306/db` |
| `REDIS_URL` | Redis 连接字符串 | `redis://:pass@host:6379/0` |
| `SECRET_KEY` | 应用密钥 | 随机字符串 |
| `COS_BUCKET` | COS 存储桶 | `bucket-appid` |
| `COS_REGION` | COS 地域 | `ap-guangzhou` |
| `COS_SECRET_ID` | COS 密钥 ID | - |
| `COS_SECRET_KEY` | COS 密钥 | - |
| `VPC_ID` | VPC ID（可选） | `vpc-xxx` |
| `SUBNET_ID` | 子网 ID（可选） | `subnet-xxx` |
| `TENCENT_SECRET_ID` | 腾讯云 API 密钥 ID | - |
| `TENCENT_SECRET_KEY` | 腾讯云 API 密钥 | - |

## CI/CD 集成

### CODING 持续集成

1. 在 CODING 项目中创建持续集成计划
2. 选择"自定义构建过程"
3. 使用 `coding-ci-scf.yaml` 配置
4. 在流水线设置中配置环境变量

### 触发条件

| 分支 | 触发条件 | 部署环境 |
|------|----------|----------|
| `feature/*` | Push | dev |
| `release/*` | Push | test |
| `master` | Push | prod |

## 文件结构

```
deployment/scf/
├── serverless.yml      # Serverless Framework 配置
├── .env.example        # 环境变量模板
├── deploy.sh           # 部署脚本
└── README.md           # 本文档
```

## 常见问题

### Q: 部署失败提示权限不足？

A: 确保腾讯云账号已开通以下服务权限：
- 云函数 SCF
- API 网关
- 对象存储 COS
- 私有网络 VPC

### Q: 函数冷启动时间过长？

A: 可以通过以下方式优化：
1. 使用预置并发
2. 减少依赖包大小
3. 使用 Layers 功能

### Q: 如何查看函数日志？

A: 登录腾讯云控制台 > 云函数 > 选择函数 > 日志查询

### Q: 如何配置自定义域名？

A: 在 `serverless.yml` 中取消 `hosts` 配置的注释，并填写域名和证书信息。

## 相关文档

- [腾讯云 SCF 文档](https://cloud.tencent.com/document/product/583)
- [Serverless Framework 文档](https://cloud.tencent.com/document/product/1154)
- [API 网关文档](https://cloud.tencent.com/document/product/628)
