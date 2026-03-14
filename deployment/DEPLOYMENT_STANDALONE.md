# PPT-RSD 生产级部署方案（独立云资源版）

> 放弃 CloudBase，使用独立的腾讯云资源构建生产级架构

## 一、架构概览

| Component | Status | Details |
|-----------|--------|---------|
| **EKS Serverless** | ✅ 已有 | `cls-1lvwzqie` (stable-diffusion-webui) |
| **TDSQL-C MySQL** | ✅ 已创建 | `cynosdbmysql-1iqzmqr3` (ppt-rsd-mysql) |
| **Redis** | ✅ 已创建 | `crs-bn7gmtnk` (ppt-creator-redis-256M) |
| **COS** | ✅ 已有 | `ppt-creator-store-1253851367` |
| **ES Serverless** | ✅ 已有 | `space-k4t5xi0i` |
| **TCR** | ✅ 已有 | `codebuddy-ppt-creator` |
| **VPC** | ✅ 已有 | `vpc-gjkbluhz` (guang7-tke) |

## 二、已创建资源详情

### 2.1 EKS Serverless 集群（容器平台）

| 项目 | 值 |
|-----|-----|
| **集群 ID** | `cls-1lvwzqie` |
| **集群名称** | `stable-diffusion-webui` |
| **状态** | Running ✅ |
| **K8s 版本** | 1.24.4 |
| **VPC** | `vpc-gjkbluhz` |
| **子网** | `subnet-fw1l5vte` (广州七区) |
| **成本** | 按量计费 |

**控制台**: https://console.cloud.tencent.com/tke2/cluster/cls-1lvwzqie

### 2.2 TDSQL-C MySQL Serverless（数据库）

| 项目 | 值 |
|-----|-----|
| **集群 ID** | `cynosdbmysql-1iqzmqr3` |
| **集群名称** | `ppt-rsd-mysql` |
| **状态** | Running ✅ |
| **版本** | MySQL 8.0 |
| **模式** | SERVERLESS |
| **内网地址** | `10.6.1.13` |
| **端口** | `3306` |
| **用户名** | `root` |
| **密码** | `PPT@RSD2024!mysql` |
| **VPC** | `vpc-gjkbluhz` |
| **子网** | `subnet-fw1l5vte` |
| **成本** | ¥30-80/月 |

**连接字符串**:
```
mysql+pymysql://root:PPT@RSD2024!mysql@10.6.1.13:3306/ppt_rsd
```

**控制台**: https://console.cloud.tencent.com/cynosdb/db/detail/cynosdbmysql-1iqzmqr3

### 2.3 云数据库 Redis（缓存）

| 项目 | 值 |
|-----|-----|
| **实例 ID** | `crs-bn7gmtnk` |
| **实例名称** | `ppt-creator-redis-256M` |
| **状态** | Running ✅ |
| **版本** | Redis 7.1.3 |
| **内存** | 256MB |
| **内网地址** | `10.6.1.42` |
| **端口** | `6379` |
| **密码** | `caonidaye@123` |
| **VPC** | `vpc-gjkbluhz` |
| **子网** | `subnet-fw1l5vte` |
| **成本** | ~¥56/月 |

**连接字符串**:
```
redis://:caonidaye@123@10.6.1.42:6379/0
```

**控制台**: https://console.cloud.tencent.com/redis/instance/crs-bn7gmtnk

### 2.4 Elasticsearch Serverless（向量检索）

| 项目 | 值 |
|-----|-----|
| **应用 ID** | `space-k4t5xi0i` |
| **访问地址** | `http://space-k4t5xi0i.ap-guangzhou.qcloudes.com` |
| **用户名** | `elastic` |
| **密码** | `caonidaye@123` |
| **索引名** | `ppt_slides` |

**控制台**: https://console.cloud.tencent.com/es

### 2.5 VPC 网络

| 项目 | 值 |
|-----|-----|
| **VPC ID** | `vpc-gjkbluhz` |
| **VPC 名称** | `guang7-tke` |
| **CIDR** | `10.6.0.0/16` |
| **子网 ID** | `subnet-fw1l5vte` |
| **子网 CIDR** | `10.6.1.0/24` |
| **可用 IP** | 250 个 |
| **地域** | 广州七区 |

## 三、成本汇总

所有资源已创建完成，无需额外创建资源。

| 资源 | 配置 | 月成本 |
|-----|------|--------|
| EKS Serverless | 已有 | 按量计费 |
| MySQL Serverless | 0.5-2核，20GB | ¥30-80 |
| ES Serverless | 已有 | 按量计费 |
| COS | 已有 | ~¥10 |
| Redis | 256MB | ~¥56 |
| **总计** | - | **¥96-146/月** |

## 五、连接信息汇总

### 环境变量配置

```bash
# 腾讯云密钥
TENCENT_SECRET_ID=AKID_REDACTED_SECRET_ID
TENCENT_SECRET_KEY=HWlrlX9fyIQj3Pj0GJ9l9IEwQgimmdP8
TENCENT_REGION=ap-guangzhou

# EKS 集群
TKE_CLUSTER_ID=cls-1lvwzqie
TKE_REGION=ap-guangzhou

# TDSQL-C MySQL
DATABASE_URL=mysql+pymysql://root:PPT@RSD2024!mysql@10.6.1.13:3306/ppt_rsd
DB_HOST=10.6.1.13
DB_PORT=3306
DB_NAME=ppt_rsd
DB_USER=root
DB_PASSWORD=PPT@RSD2024!mysql

# Elasticsearch
ES_HOST=http://space-k4t5xi0i.ap-guangzhou.qcloudes.com
ES_USERNAME=elastic
ES_PASSWORD=caonidaye@123
ES_INDEX_NAME=ppt_slides

# COS
COS_BUCKET=ppt-creator-store-1253851367
COS_REGION=ap-guangzhou

# TCR
TCR_REGISTRY=ccr.ccs.tencentyun.com
TCR_NAMESPACE=codebuddy-ppt-creator
TCR_USERNAME=100000763815
```

### GitHub Secrets 配置

在 GitHub 仓库 Settings → Secrets → Actions 中添加:

```yaml
# 必需
TENCENT_SECRET_ID: "AKID_REDACTED_SECRET_ID"
TENCENT_SECRET_KEY: "HWlrlX9fyIQj3Pj0GJ9l9IEwQgimmdP8"
TKE_CLUSTER_ID: "cls-1lvwzqie"

# 数据库
DATABASE_URL: "mysql+pymysql://root:PPT@RSD2024!mysql@10.6.1.13:3306/ppt_rsd"

# Elasticsearch
ES_HOST: "http://space-k4t5xi0i.ap-guangzhou.qcloudes.com"
ES_USERNAME: "elastic"
ES_PASSWORD: "caonidaye@123"
```

## 六、部署命令

```bash
# 本地部署
export TENCENT_SECRET_ID="AKID_REDACTED_SECRET_ID"
export TENCENT_SECRET_KEY="HWlrlX9fyIQj3Pj0GJ9l9IEwQgimmdP8"
export TKE_CLUSTER_ID="cls-1lvwzqie"
./deployment/deploy.sh prod
```

---

**文档版本**: v2.1
**最后更新**: 2026-03-14
**架构**: 独立云资源（使用现有 EKS）
