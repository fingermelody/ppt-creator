# PPT-RSD 生产级部署方案（独立云资源版）

> 放弃 CloudBase，使用独立的腾讯云资源构建生产级架构

## 一、架构概览

| Component | Status | Details |
|-----------|--------|---------|
| **CloudBase** | ❌ 放弃 | 不再使用 |
| **TKE 容器集群** | ✅ 新增 | 托管 Kubernetes 集群 |
| **TDSQL-C MySQL** | ✅ 新增 | 云原生数据库 |
| **Redis** | ✅ 新增 | 云数据库缓存 |
| **COS** | ✅ 保留 | 对象存储 |
| **CLB** | ✅ 新增 | 负载均衡 |
| **ES Serverless** | ✅ 已有 | 向量检索 |
| **TCR** | ✅ 保留 | 容器镜像仓库 |

## 二、资源配置详情

### 2.1 TKE 容器集群（腾讯云 Kubernetes）
- **控制台**: https://console.cloud.tencent.com/tke2
- **推荐配置**:
  - 集群类型: 标准集群（托管 Master）
  - 地域: ap-guangzhou（广州）
  - 节点配置: 2核4GB * 2（最小高可用）
  - 计费模式: 按量计费
- **月成本**: ~¥300-500/月

### 2.2 TDSQL-C MySQL Serverless
- **控制台**: https://console.cloud.tencent.com/cynosdb
- **推荐配置**:
  - 地域: ap-guangzhou
  - 版本: MySQL 8.0
  - 计费模式: Serverless 按量计费
  - 规格: 0.25-0.5 核
  - 存储: 20GB
- **月成本**: ~¥30-80/月（按实际使用量）

### 2.3 云数据库 Redis
- **控制台**: https://console.cloud.tencent.com/redis
- **推荐配置**:
  - 地域: ap-guangzhou
  - 版本: Redis 5.0 标准版
  - 规格: 256MB 内存
  - 计费模式: 包年包月
- **月成本**: ¥56/月

### 2.4 对象存储 COS
- **控制台**: https://console.cloud.tencent.com/cos
- **配置**:
  - 地域: ap-guangzhou
  - 存储桶: ppt-rsd-files
  - 用途: 文件存储、前端静态资源
- **月成本**: ~¥10-20/月

### 2.5 负载均衡 CLB
- **控制台**: https://console.cloud.tencent.com/clb
- **推荐配置**:
  - 地域: ap-guangzhou
  - 类型: 应用型负载均衡
  - 网络: 公网
- **月成本**: ~¥40-60/月

### 2.6 Elasticsearch Serverless（已有）
- **控制台**: https://console.cloud.tencent.com/es
- **配置**:
  - 访问地址: http://space-k4t5xi0i.ap-guangzhou.qcloudes.com
  - 用户名: elastic
  - 密码: caonidaye@123
- **月成本**: 按量计费

## 三、成本估算
| 资源 | 配置 | 月成本 |
|-----|-----|--------|
| TKE 容器集群 | 2节点 | ¥300-500 |
| TDSQL-C MySQL | Serverless | ¥30-80 |
| Redis | 256MB | ¥56 |
| COS | 按量 | ¥10-20 |
| 负载均衡 CLB | 应用型 | ¥40-60 |
| ES Serverless | 已有 | 按量 |
| **总计** | - | **¥436-716/月** |
## 四、创建步骤

### 步骤 1: 创建 VPC 网络
```
控制台: https://console.cloud.tencent.com/vpc

配置:
- 地域: 广州
- 名称: ppt-rsd-vpc
- CIDR: 10.0.0.0/16
- 子网: 10.0.0.0/24
```

### 步骤 2: 创建 TDSQL-C MySQL
```
控制台: https://buy.cloud.tencent.com/cynosdb

1. 选择 MySQL
2. 选择 Serverless
3. 地域: 广州
4. VPC: 选择刚创建的 ppt-rsd-vpc
5. 计算规格: 最小
6. 存储: 20GB
7. 设置 root 密码

记录:
- 数据库地址
- 端口: 3306
- 用户名: root
- 密码
```

### 步骤 3: 创建 Redis
```
控制台: https://buy.cloud.tencent.com/redis

1. 版本: Redis 5.0 标准版
2. 地域: 广州
3. 网络: 选择 ppt-rsd-vpc
4. 规格: 256MB
5. 计费: 包年包月
6. 设置密码

记录:
- 连接地址
- 端口: 6379
- 密码
```

### 步骤 4: 创建 TKE 集群
```
控制台: https://console.cloud.tencent.com/tke2

1. 创建标准集群
2. 地域: 广州
3. 集群名称: ppt-rsd-cluster
4. 网络: 选择 ppt-rsd-vpc
5. 节点配置:
   - 2核4GB * 2 个节点
   - 按量计费

记录:
- 集群 ID
- API Server 地址
```

### 步骤 5: 配置负载均衡
```
控制台: https://console.cloud.tencent.com/clb

1. 创建应用型 CLB
2. 地域: 广州
3. 网络: 选择 ppt-rsd-vpc
4. 监听端口: 80, 443
5. 绑定 TKE 集群

记录:
- CLB VIP
- 域名配置
```

## 五、GitHub Secrets 配置

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加:

```yaml
# 腾讯云密钥
TENCENT_SECRET_ID: "your-secret-id"
TENCENT_SECRET_KEY: "your-secret-key"

# TKE 集群
TKE_CLUSTER_ID: "cls-xxxxxx"
TKE_REGION: "ap-guangzhou"

# TDSQL-C MySQL
DATABASE_URL: "mysql+pymysql://root:password@host:3306/ppt_rsd"
DB_HOST: "xxx.sql.tencentcdb.com"
DB_PORT: "3306"
DB_NAME: "ppt_rsd"
DB_USER: "root"
DB_PASSWORD: "your-password"

# Redis
REDIS_URL: "redis://:password@host:6379/0"
REDIS_HOST: "xxx.redis.rds.tencentcloud.com"
REDIS_PORT: "6379"
REDIS_PASSWORD: "your-password"

# Elasticsearch
ES_HOST: "http://space-k4t5xi0i.ap-guangzhou.qcloudes.com"
ES_USERNAME: "elastic"
ES_PASSWORD: "caonidaye@123"
ES_INDEX_NAME: "ppt_slides"

# COS
COS_BUCKET: "ppt-rsd-files-1253851367"
COS_REGION: "ap-guangzhou"

# TCR 镜像仓库
TCR_REGISTRY: "ccr.ccs.tencentyun.com"
TCR_NAMESPACE: "codebuddy-ppt-creator"
TCR_USERNAME: "100000763815"
TCR_PASSWORD: "your-tcr-password"

# JWT
SECRET_KEY: "生成一个32位随机字符串"
```

## 六、数据库迁移
项目需要从 PostgreSQL/SQLite 切换到 MySQL:

### 6.1 连接字符串格式
```python
# 原 PostgreSQL 格式
DATABASE_URL=postgresql://user:password@host:5432/ppt_rsd

# 新 MySQL 格式
DATABASE_URL=mysql+pymysql://root:password@host:3306/ppt_rsd
```

### 6.2 无需代码修改
项目使用 SQLAlchemy ORM，无需修改代码，只需更新环境变量。

## 七、部署架构图
```
                    用户请求
                        │
                        ▼
                  ┌───────────┐
                  │ 负载均衡    │
                  │   (CLB)    │
                  └─────┬─────┘
                        │
                        ▼
                  ┌───────────┐
                  │  TKE 集群   │
                  │           │
                  │  ┌─────┐   │
                  │  │前端  │   │
                  │  └──┬──┘   │
                  │     │       │
                  │  ┌──┴──┐   │
                  │  │后端  │   │
                  │  └──┬──┘   │
                  └─────┼─────┘
                        │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  MySQL   │  │  Redis   │  │    ES    │
    │(TDSQL-C) │  │          │  │Serverless│
    └──────────┘  └──────────┘  └──────────┘
          │
          ▼
    ┌──────────┐
    │   COS    │
    │  存储    │
    └──────────┘
```

## 八、与 CloudBase 对比

| 项目 | CloudBase 方案 | 独立云资源方案 |
|-----|----------------|---------------|
| 月成本 | ~¥70-400 | ~¥436-716 |
| 可控性 | 有限 | 完全控制 |
| 扩展性 | 受限 | 灵活扩展 |
| 自定义配置 | 受限 | 完全自定义 |
| 监控告警 | 基础 | 完整监控 |
| 适合场景 | 初创验证 | 生产级应用 |
## 九、注意事项

1. **网络互通**: 确保所有资源在同一 VPC 内
2. **安全组**: 配置正确的入站/出站规则
3. **备份策略**: 启用 MySQL 自动备份
4. **监控告警**: 配置云监控告警策略
5. **成本控制**: 设置资源使用告警阈值

---

**文档版本**: v2.0
**最后更新**: 2026-03-14
**架构**: 独立云资源
