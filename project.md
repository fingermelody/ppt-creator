# PPT-Creator 智能PPT生成系统 - 项目结构文档

## 1. 项目概述

本项目是一个基于Web的PPT页面拼凑组装系统，采用前后端分离架构，支持用户从本地PPT文档库中检索相关页面，以"页面复制"方式组装成新PPT。

**技术栈**：
- 前端：React 18 + TypeScript + TDesign + Zustand + React Query
- 后端：Python 3.9+ + FastAPI + SQLAlchemy + Celery
- 数据库：TDSQL-C MySQL + Redis + ChromaDB
- 部署：腾讯云TKE容器服务 / 轻量服务器 + Docker Compose
- 流水线：腾讯云CODING DevOps / GitHub Actions + TCR
- LLM：可选，支持混元/文心一言/通义千问/OpenAI/自定义模型

---

## 2. 整体目录结构

```
ppt-creator/
├── frontend/                 # 前端应用（React）
├── backend/                  # 后端应用（FastAPI）
├── workers/                  # 异步任务处理器（Celery）
├── deployment/               # 部署配置（腾讯云 + Docker）
├── docs/                     # 项目文档
└── README.md                 # 项目说明
```

---

## 3. 前端项目结构 (frontend/)

```
frontend/
├── public/                   # 静态资源
│   ├── index.html
│   ├── favicon.ico
│   └── assets/
│       └── images/
├── src/
│   ├── api/                  # API调用层
│   │   ├── client.ts         # Axios实例配置
│   │   ├── documents.ts      # 文档管理API
│   │   ├── outline.ts        # 大纲设计API
│   │   ├── assembly.ts       # PPT组装API
│   │   ├── refinement.ts     # PPT精修API
│   │   ├── export.ts         # 导出API
│   │   └── types.ts          # API响应类型定义
│   │
│   ├── components/           # 公共组件
│   │   ├── common/           # 通用组件
│   │   │   ├── Button/
│   │   │   ├── Card/
│   │   │   ├── Modal/
│   │   │   ├── Upload/
│   │   │   └── ...
│   │   ├── document/         # 文档相关组件
│   │   │   ├── DocumentCard/
│   │   │   ├── SlideGrid/
│   │   │   ├── SlidePreview/
│   │   │   └── ...
│   │   ├── assembly/         # 组装相关组件
│   │   │   ├── ChapterEditor/
│   │   │   ├── SlideSelector/
│   │   │   ├── AlternativePanel/
│   │   │   └── ...
│   │   └── refinement/       # 精修相关组件
│   │       ├── ChatPanel/
│   │       ├── ElementEditor/
│   │       └── ...
│   │
│   ├── pages/                # 页面组件
│   │   ├── Library/          # 文档库页面
│   │   │   ├── index.tsx
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   ├── Outline/          # 大纲设计页面
│   │   │   ├── index.tsx
│   │   │   ├── index.css
│   │   │   └── components/
│   │   │       ├── SmartGenerate.tsx    # 智能生成组件
│   │   │       ├── WizardGenerate.tsx   # 向导式生成组件
│   │   │       ├── OutlinePreview.tsx   # 大纲预览组件
│   │   │       └── TemplateSelector.tsx # 模板选择器
│   │   ├── Assembly/         # PPT组装页面
│   │   │   ├── index.tsx
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   ├── Refinement/       # PPT精修页面
│   │   │   ├── index.tsx
│   │   │   ├── components/
│   │   │   └── hooks/
│   │   └── Drafts/           # 草稿管理页面
│   │       ├── index.tsx
│   │       └── components/
│   │
│   ├── hooks/                # 自定义Hooks
│   │   ├── useDocuments.ts
│   │   ├── useAssembly.ts
│   │   ├── useUndoRedo.ts
│   │   └── ...
│   │
│   ├── stores/               # 状态管理（Zustand）
│   │   ├── documentStore.ts
│   │   ├── outlineStore.ts   # 大纲设计状态
│   │   ├── assemblyStore.ts
│   │   ├── refinementStore.ts
│   │   └── uiStore.ts
│   │
│   ├── types/                # TypeScript类型定义
│   │   ├── document.ts
│   │   ├── outline.ts        # 大纲相关类型
│   │   ├── assembly.ts
│   │   ├── refinement.ts
│   │   └── common.ts
│   │
│   ├── utils/                # 工具函数
│   │   ├── constants.ts
│   │   ├── helpers.ts
│   │   └── validators.ts
│   │
│   ├── styles/               # 样式文件
│   │   ├── global.css
│   │   ├── variables.css
│   │   └── components/
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── router.tsx
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── .env
```

---

## 4. 后端项目结构 (backend/)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI应用入口
│   │
│   ├── api/                  # API路由层
│   │   ├── __init__.py
│   │   ├── deps.py           # 依赖注入
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py     # v1路由聚合
│   │   │   ├── endpoints/
│   │   │   │   ├── documents.py    # 文档管理接口
│   │   │   │   ├── outline.py      # 大纲设计接口
│   │   │   │   ├── assembly.py     # PPT组装接口
│   │   │   │   ├── refinement.py   # PPT精修接口
│   │   │   │   ├── export.py       # 导出接口
│   │   │   │   └── health.py       # 健康检查
│   │   │   └── websockets/
│   │   │       └── progress.py     # 进度推送
│   │
│   ├── core/                 # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py         # 配置管理
│   │   ├── security.py       # 安全相关
│   │   ├── exceptions.py     # 自定义异常
│   │   └── logging.py        # 日志配置
│   │
│   ├── models/               # 数据模型（SQLAlchemy）
│   │   ├── __init__.py
│   │   ├── document.py       # 文档模型
│   │   ├── slide.py          # 页面模型
│   │   ├── outline.py        # 大纲模型
│   │   ├── assembly.py       # 组装草稿模型
│   │   ├── refinement.py     # 精修任务模型
│   │   └── base.py           # 基础模型
│   │
│   ├── schemas/              # Pydantic数据模型
│   │   ├── __init__.py
│   │   ├── document.py
│   │   ├── slide.py
│   │   ├── outline.py        # 大纲请求/响应模型
│   │   ├── assembly.py
│   │   ├── refinement.py
│   │   └── common.py
│   │
│   ├── services/             # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   ├── slide_service.py
│   │   ├── outline_service.py    # 大纲生成服务
│   │   ├── assembly_service.py
│   │   ├── refinement_service.py
│   │   ├── export_service.py
│   │   └── retrieval_service.py
│   │
│   ├── db/                   # 数据库相关
│   │   ├── __init__.py
│   │   ├── session.py        # 数据库会话
│   │   ├── base.py           # 基础类
│   │   └── migrations/       # Alembic迁移
│   │
│   ├── infrastructure/       # 基础设施层
│   │   ├── __init__.py
│   │   ├── storage/          # 文件存储
│   │   │   ├── __init__.py
│   │   │   ├── local.py
│   │   │   └── minio.py
│   │   ├── vector/           # 向量数据库
│   │   │   ├── __init__.py
│   │   │   └── chroma.py
│   │   ├── cache/            # 缓存
│   │   │   ├── __init__.py
│   │   │   └── redis.py
│   │   └── llm/              # LLM客户端（可选，支持多模型）
│   │       ├── __init__.py
│   │       ├── base.py       # LLM抽象基类
│   │       ├── factory.py    # 模型工厂（动态创建）
│   │       ├── config.py     # 模型配置管理
│   │       ├── providers/    # 内置模型提供商
│   │       │   ├── __init__.py
│   │       │   ├── hunyuan.py      # 腾讯混元
│   │       │   ├── wenxin.py       # 百度文心一言
│   │       │   ├── qwen.py         # 阿里通义千问
│   │       │   ├── openai.py       # OpenAI
│   │       │   ├── claude.py       # Anthropic Claude
│   │       │   └── custom.py       # 自定义模型基类
│   │       └── custom/       # 用户自定义模型
│   │           ├── __init__.py
│   │           └── README.md
│   │
│   └── utils/                # 工具函数
│       ├── __init__.py
│       ├── ppt_parser.py     # PPT解析
│       ├── thumbnail.py      # 缩略图生成
│       └── validators.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_services/
│   │   └── test_utils/
│   └── integration/
│       ├── test_api/
│       └── test_workflows/
│
├── alembic.ini
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── Dockerfile
```

---

## 5. 任务队列项目结构 (workers/)

```
workers/
├── app/
│   ├── __init__.py
│   ├── celery_app.py         # Celery应用配置
│   │
│   ├── tasks/                # 任务定义
│   │   ├── __init__.py
│   │   ├── document_tasks.py # 文档处理任务
│   │   ├── parse_tasks.py    # PPT解析任务
│   │   ├── embedding_tasks.py# 向量化任务
│   │   ├── thumbnail_tasks.py# 缩略图生成任务
│   │   └── export_tasks.py   # 导出任务
│   │
│   └── utils/                # 任务工具
│       ├── __init__.py
│       ├── progress.py       # 进度上报
│       └── retry.py          # 重试机制
│
├── tests/
│   └── test_tasks/
│
├── requirements.txt
└── Dockerfile
```

---

## 6. 部署配置结构 (deployment/)

```
deployment/
├── docker/                          # Docker配置
│   ├── docker-compose.yml           # 本地编排
│   ├── docker-compose.dev.yml
│   ├── Dockerfile.frontend          # 前端镜像
│   ├── Dockerfile.backend           # 后端镜像
│   ├── Dockerfile.worker            # 任务队列镜像
│   ├── nginx/
│   │   ├── nginx.conf
│   │   └── conf.d/
│   │       └── default.conf
│   └── scripts/
│       ├── init-db.sh
│       └── backup.sh
│
├── tke/                             # 腾讯云TKE容器服务
│   ├── namespaces/                  # 命名空间
│   │   ├── production.yaml
│   │   └── staging.yaml
│   ├── configmaps/                  # 配置
│   │   ├── app-config.yaml
│   │   └── nginx-config.yaml
│   ├── secrets/                     # 密钥模板
│   │   ├── db-secret.yaml.example
│   │   └── cos-secret.yaml.example
│   ├── deployments/                 # 工作负载
│   │   ├── frontend.yaml
│   │   ├── backend.yaml
│   │   └── worker.yaml
│   ├── services/                    # 服务暴露
│   │   ├── frontend-svc.yaml
│   │   ├── backend-svc.yaml
│   │   └── ingress.yaml
│   ├── hpa/                         # 自动扩缩容
│   │   ├── backend-hpa.yaml
│   │   └── worker-hpa.yaml
│   └── kustomization.yaml           # 环境配置
│
├── tencent-cloud/                   # 腾讯云资源配置
│   ├── lighthouse/                  # 轻量服务器配置
│   │   ├── setup.sh                 # 初始化脚本
│   │   └── firewall.sh              # 防火墙配置
│   ├── cvm/                         # CVM配置
│   │   └── docker-install.sh
│   ├── cos/                         # 对象存储配置
│   │   ├── create-bucket.sh
│   │   └── cors-config.json
│   ├── tcr/                         # 容器镜像服务
│   │   └── create-namespace.sh
│   └── ssl/                         # SSL证书
│       └── apply-ssl.sh
│
└── cicd/                            # 持续集成/部署
    ├── coding/                      # 腾讯云CODING
    │   ├── coding-ci.yaml           # 构建流水线
    │   └── coding-cd.yaml           # 部署流水线
    ├── github-actions/              # GitHub Actions
    │   ├── build.yml
    │   └── deploy-tke.yml
    └── scripts/
        ├── build-images.sh
        └── deploy-tke.sh
```

---

## 7. 模块依赖关系

### 7.1 前端模块依赖

```
┌───────────────────────────────────────────────────────────────────┐
│                        页面层 (Pages)                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │ Library  │ │ Outline  │ │ Assembly │ │Refinement│ │ Drafts  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬────┘ │
└───────┼────────────┼────────────┼────────────┼────────────┼──────┘
        │            │            │            │            │
        └────────────┴─────┬──────┴────────────┴────────────┘
                           ▼
┌───────────────────────────────────────────────────────────────────┐
│                      业务组件层                                    │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────────────┐ │
│  │ Document │ │   Outline    │ │ Assembly │ │   Refinement     │ │
│  │Components│ │  Components  │ │Components│ │   Components     │ │
│  └────┬─────┘ └──────┬───────┘ └────┬─────┘ └────────┬─────────┘ │
└───────┼──────────────┼──────────────┼────────────────┼───────────┘
        │              │              │                │
        └──────────────┴──────┬───────┴────────────────┘
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│                      基础层                                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐           │
│  │   API    │ │  Stores  │ │  Hooks   │ │ Components │           │
│  │  Layer   │ │(Zustand) │ │          │ │  (Common)  │           │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘           │
└───────────────────────────────────────────────────────────────────┘
```

### 7.2 后端模块依赖

```
┌───────────────────────────────────────────────────────────────────┐
│                      API 层 (Routers)                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │/documents│ │ /outline │ │/assembly │ │    /refinement       │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────────┬───────────┘ │
└───────┼────────────┼────────────┼──────────────────┼─────────────┘
        │            │            │                  │
        └────────────┴─────┬──────┴──────────────────┘
                           ▼
┌───────────────────────────────────────────────────────────────────┐
│                    Service 层（业务逻辑）                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │ Document │ │ Outline  │ │ Assembly │ │     Refinement       │ │
│  │ Service  │ │ Service  │ │ Service  │ │      Service         │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│  Model 层    │  │ Infrastructure│  │     Workers      │
│  (SQLAlchemy)│  │    Layer      │  │    (Celery)      │
└──────────────┘  └──────────────┘  └──────────────────┘
```

---

## 8. 核心数据流

### 8.1 文档上传与解析流程

```
Frontend                    Backend                     Workers
   │                          │                           │
   │  1. 分片上传              │                           │
   │ ───────────────────────> │                           │
   │                          │  2. 合并文件               │
   │                          │  3. 创建文档记录            │
   │                          │  4. 发送解析任务            │
   │                          │ ────────────────────────> │
   │                          │                           │ 5. PPT解析
   │                          │                           │ 6. 向量化
   │                          │                           │ 7. 缩略图生成
   │  8. WebSocket进度推送     │ <──────────────────────── │
   │ <─────────────────────── │                           │
```

### 8.2 大纲设计流程

```
Frontend                    Backend                     LLM (可选)
   │                          │                           │
   │  【智能生成模式】          │                           │
   │  1. 提交描述文本          │                           │
   │ ───────────────────────> │                           │
   │                          │  2. 调用LLM分析             │
   │                          │ ────────────────────────> │
   │                          │ <──────────────────────── │
   │  3. 返回生成的大纲        │                           │
   │ <─────────────────────── │                           │
   │                          │                           │
   │  【向导式生成模式】        │                           │
   │  4. 创建向导会话          │                           │
   │ ───────────────────────> │  5. 保存会话               │
   │                          │                           │
   │  6. 步骤1：主题设定       │                           │
   │ ───────────────────────> │  7. 保存步骤数据           │
   │                          │                           │
   │  8. 步骤2：章节规划       │                           │
   │ ───────────────────────> │  9. 保存章节               │
   │                          │                           │
   │  10. 步骤3：内容摘要      │                           │
   │ ───────────────────────> │  11. AI建议（可选）        │
   │                          │ ────────────────────────> │
   │                          │ <──────────────────────── │
   │                          │                           │
   │  12. 步骤4：完成生成      │                           │
   │ ───────────────────────> │  13. 生成大纲结构          │
   │                          │                           │
   │  14. 返回完整大纲         │                           │
   │ <─────────────────────── │                           │
   │                          │                           │
   │  【确认大纲】             │                           │
   │  15. 确认大纲开始组装     │                           │
   │ ───────────────────────> │  16. 创建组装草稿          │
   │                          │  17. 关联大纲章节          │
   │  18. 跳转到组装页面       │                           │
   │ <─────────────────────── │                           │
```

### 8.3 PPT组装流程

```
Frontend                    Backend                     VectorDB
   │                          │                           │
   │  1. 创建组装任务          │                           │
   │ ───────────────────────> │                           │
   │                          │  2. 保存章节结构           │
   │                          │  3. 语义检索               │
   │                          │ ────────────────────────> │
   │                          │ <──────────────────────── │
   │  4. 返回初稿页面          │  5. 生成初稿               │
   │ <─────────────────────── │                           │
   │                          │                           │
   │  6. 查看备选/替换页面     │  7. 相似度检索             │
   │ ───────────────────────> │ ────────────────────────> │
   │ <─────────────────────── │                           │
```

---

## 9. 扩展性设计

### 9.1 新增功能模块步骤

1. **前端**：
   - 在 `src/pages/` 新增页面目录
   - 在 `src/components/` 新增业务组件
   - 在 `src/api/` 新增API接口
   - 在 `src/stores/` 新增状态管理
   - 在 `src/types/` 新增类型定义

2. **后端**：
   - 在 `app/api/v1/endpoints/` 新增路由
   - 在 `app/services/` 新增服务类
   - 在 `app/models/` 新增数据模型（如需）
   - 在 `app/schemas/` 新增Pydantic模型

3. **任务队列**（如需异步处理）：
   - 在 `workers/tasks/` 新增任务

### 9.2 大纲模块示例

以大纲设计模块为例，展示模块新增流程：

```
前端新增文件：
├── src/
│   ├── api/
│   │   └── outline.ts              # 大纲API接口
│   ├── pages/
│   │   └── Outline/
│   │       ├── index.tsx           # 大纲页面主入口
│   │       ├── index.css           # 大纲页面样式
│   │       └── components/
│   │           ├── SmartGenerate.tsx    # 智能生成
│   │           ├── WizardGenerate.tsx   # 向导式生成
│   │           ├── OutlinePreview.tsx   # 大纲预览
│   │           └── TemplateSelector.tsx # 模板选择
│   ├── stores/
│   │   └── outlineStore.ts         # 大纲状态管理
│   └── types/
│       └── outline.ts              # 大纲类型定义

后端新增文件：
├── app/
│   ├── api/v1/endpoints/
│   │   └── outline.py              # 大纲路由
│   ├── services/
│   │   └── outline_service.py      # 大纲服务
│   ├── models/
│   │   └── outline.py              # 大纲数据模型
│   └── schemas/
│       └── outline.py              # 大纲Pydantic模型
```

### 9.3 可替换组件

| 组件 | 当前实现 | 可替换方案 |
|------|---------|-----------|
| 向量数据库 | ChromaDB | 腾讯云向量数据库 |
| 文件存储 | 本地文件系统 | 腾讯云COS |
| LLM服务 | 可选/多模型支持 | 混元/文心/通义/OpenAI/自定义 |
| 缓存 | Redis | 腾讯云Redis |
| 数据库 | TDSQL-C MySQL | 腾讯云TDSQL |
| 服务器 | 腾讯云TKE / 轻量服务器 | 腾讯云CVM |

---

## 10. 开发规范

### 10.1 命名规范

- **前端**：
  - 组件：PascalCase（如 `SlidePreview.tsx`）
  - Hooks：camelCase，前缀 `use`（如 `useDocuments.ts`）
  - 常量：UPPER_SNAKE_CASE
  - 类型：PascalCase，后缀 `Type` 或 `Interface`

- **后端**：
  - 模块/包：snake_case
  - 类：PascalCase
  - 函数/变量：snake_case
  - 常量：UPPER_SNAKE_CASE

### 10.2 代码组织原则

1. **单一职责**：每个模块/函数只负责一个功能
2. **依赖注入**：使用FastAPI的依赖注入系统
3. **接口隔离**：API层只依赖Service层接口
4. **分层清晰**：禁止跨层调用（如API直接调用Model）

---

## 11. 腾讯云部署方案

### 11.1 部署架构选型

| 场景 | 推荐方案 | 适用说明 |
|------|---------|---------|
| **生产环境（推荐）** | TKE容器服务 + TDSQL-C | 高可用、自动扩缩容 |
| **中小规模** | 轻量服务器 + Docker Compose | 简单、低成本 |
| **开发测试** | TKE Serverless | 按需付费、免运维 |

### 11.2 推荐资源配置

#### 方案A：TKE容器服务（生产推荐）

| 组件 | 推荐配置 | 说明 |
|------|---------|------|
| TKE集群 | 标准集群 2-4节点 | 托管Master |
| 工作节点 | 4核8G × 2 | 运行应用容器 |
| TDSQL-C MySQL | 2核4G 100G存储 | 关系数据库 |
| 腾讯云Redis | 1G内存 | 缓存/任务队列 |
| 腾讯云COS | 标准存储 | 文件/缩略图存储 |
| 腾讯云TCR | 标准版 | 容器镜像仓库 |
| LLM API | 按量付费 | AI精修功能（可选） |

#### 方案B：轻量服务器（中小规模）

| 组件 | 推荐配置 | 说明 |
|------|---------|------|
| 轻量服务器 | 4核8G 12M带宽 | 应用主服务器 |
| TDSQL-C MySQL | 2核4G 100G存储 | 关系数据库 |
| 腾讯云Redis | 1G内存 | 缓存/任务队列 |
| 腾讯云COS | 标准存储 | 文件/缩略图存储 |

### 11.3 开发环境

```bash
# 本地开发
# 前端
cd frontend && npm run dev

# 后端
cd backend && uvicorn app.main:app --reload

# 任务队列
cd workers && celery -A app.celery_app worker --loglevel=info
```

### 11.4 TKE容器服务部署

```bash
# 1. 配置kubectl连接TKE集群
# 在腾讯云控制台获取kubeconfig并配置

# 2. 创建命名空间和配置
kubectl apply -k deployment/tke/overlays/production

# 3. 部署应用
kubectl apply -f deployment/tke/deployments/
kubectl apply -f deployment/tke/services/

# 4. 查看部署状态
kubectl get pods -n ppt-rsd-prod
kubectl get svc -n ppt-rsd-prod
```

### 11.5 轻量服务器部署

```bash
# 1. 初始化轻量服务器
ssh root@<lighthouse-ip>
curl -fsSL https://get.docker.com | bash

# 2. 克隆代码并部署
git clone <repo-url> /opt/ppt-rsd
cd /opt/ppt-rsd/deployment/docker
docker-compose -f docker-compose.prod.yml up -d
```

### 11.6 腾讯云环境变量配置

```bash
# .env.production
# 数据库 - TDSQL-C MySQL
DATABASE_URL=mysql+pymysql://user:pass@<tdsql-endpoint>:3306/ppt_rsd

# Redis - 腾讯云Redis
REDIS_URL=redis://:<password>@<redis-endpoint>:6379/0

# COS - 腾讯云对象存储
COS_SECRET_ID=your-secret-id
COS_SECRET_KEY=your-secret-key
COS_REGION=ap-guangzhou
COS_BUCKET=ppt-rsd-files

# TCR - 容器镜像仓库
TCR_REGISTRY=ccr.ccs.tencentyun.com
TCR_NAMESPACE=ppt-rsd

# ================================
# LLM 模型配置（可选，至少配置一个）
# ================================

# 是否启用LLM功能
LLM_ENABLED=true

# 默认模型提供商
LLM_DEFAULT_PROVIDER=hunyuan

# 腾讯混元大模型
HUNYUAN_SECRET_ID=your-secret-id
HUNYUAN_SECRET_KEY=your-secret-key
HUNYUAN_MODEL=hunyuan-lite

# 百度文心一言
WENXIN_API_KEY=your-api-key
WENXIN_SECRET_KEY=your-secret-key
WENXIN_MODEL=ernie-lite-8k

# 阿里通义千问
QWEN_API_KEY=your-api-key
QWEN_MODEL=qwen-turbo

# OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# Claude
CLAUDE_API_KEY=your-api-key
CLAUDE_MODEL=claude-3-haiku-20240307

# 自定义模型（OpenAI兼容格式）
CUSTOM_MODEL_NAME=my-custom-model
CUSTOM_API_URL=https://your-custom-api.com/v1
CUSTOM_API_KEY=your-api-key
CUSTOM_MODEL_IDENTIFIER=gpt-4
```

---

## 12. CI/CD 流水线配置

### 12.1 方案选型

| 方案 | 适用场景 | 特点 |
|------|---------|------|
| **腾讯云CODING** | 代码在CODING | 与腾讯云深度集成 |
| **GitHub Actions + TCR** | 代码在GitHub | 国际化、生态丰富 |

### 12.2 CODING 流水线配置

```yaml
# deployment/cicd/coding/coding-ci.yaml
# 构建流水线：代码提交 → 构建镜像 → 推送到TCR

stages:
  - checkout
  - build
  - push
  - deploy

# 构建前端镜像
build-frontend:
  stage: build
  script:
    - docker build -t $TCR_REGISTRY/$TCR_NAMESPACE/frontend:$CI_COMMIT_SHA -f deployment/docker/Dockerfile.frontend .
    - docker push $TCR_REGISTRY/$TCR_NAMESPACE/frontend:$CI_COMMIT_SHA

# 构建后端镜像
build-backend:
  stage: build
  script:
    - docker build -t $TCR_REGISTRY/$TCR_NAMESPACE/backend:$CI_COMMIT_SHA -f deployment/docker/Dockerfile.backend .
    - docker push $TCR_REGISTRY/$TCR_NAMESPACE/backend:$CI_COMMIT_SHA

# 构建Worker镜像
build-worker:
  stage: build
  script:
    - docker build -t $TCR_REGISTRY/$TCR_NAMESPACE/worker:$CI_COMMIT_SHA -f deployment/docker/Dockerfile.worker .
    - docker push $TCR_REGISTRY/$TCR_NAMESPACE/worker:$CI_COMMIT_SHA

# 部署到TKE
deploy-tke:
  stage: deploy
  script:
    - kubectl set image deployment/frontend frontend=$TCR_REGISTRY/$TCR_NAMESPACE/frontend:$CI_COMMIT_SHA -n ppt-rsd-prod
    - kubectl set image deployment/backend backend=$TCR_REGISTRY/$TCR_NAMESPACE/backend:$CI_COMMIT_SHA -n ppt-rsd-prod
    - kubectl set image deployment/worker worker=$TCR_REGISTRY/$TCR_NAMESPACE/worker:$CI_COMMIT_SHA -n ppt-rsd-prod
```

### 12.3 GitHub Actions 配置

```yaml
# .github/workflows/deploy-tke.yml
name: Build and Deploy to TKE

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # 登录腾讯云TCR
      - name: Login to TCR
        uses: docker/login-action@v2
        with:
          registry: ccr.ccs.tencentyun.com
          username: ${{ secrets.TCR_USERNAME }}
          password: ${{ secrets.TCR_PASSWORD }}
      
      # 构建并推送镜像
      - name: Build and Push
        run: |
          docker build -t ccr.ccs.tencentyun.com/ppt-rsd/frontend:${{ github.sha }} -f deployment/docker/Dockerfile.frontend .
          docker build -t ccr.ccs.tencentyun.com/ppt-rsd/backend:${{ github.sha }} -f deployment/docker/Dockerfile.backend .
          docker build -t ccr.ccs.tencentyun.com/ppt-rsd/worker:${{ github.sha }} -f deployment/docker/Dockerfile.worker .
          docker push ccr.ccs.tencentyun.com/ppt-rsd/frontend:${{ github.sha }}
          docker push ccr.ccs.tencentyun.com/ppt-rsd/backend:${{ github.sha }}
          docker push ccr.ccs.tencentyun.com/ppt-rsd/worker:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      # 配置TKE访问凭证
      - name: Configure TKE Credentials
        uses: tencentcloud/tke-cluster-credential-action@v1
        with:
          secret_id: ${{ secrets.TENCENT_CLOUD_SECRET_ID }}
          secret_key: ${{ secrets.TENCENT_CLOUD_SECRET_KEY }}
          tke_region: ap-guangzhou
          cluster_id: ${{ secrets.TKE_CLUSTER_ID }}
      
      # 部署到TKE
      - name: Deploy to TKE
        run: |
          kubectl set image deployment/frontend frontend=ccr.ccs.tencentyun.com/ppt-rsd/frontend:${{ github.sha }} -n ppt-rsd-prod
          kubectl set image deployment/backend backend=ccr.ccs.tencentyun.com/ppt-rsd/backend:${{ github.sha }} -n ppt-rsd-prod
          kubectl set image deployment/worker worker=ccr.ccs.tencentyun.com/ppt-rsd/worker:${{ github.sha }} -n ppt-rsd-prod
          kubectl rollout status deployment/frontend -n ppt-rsd-prod
          kubectl rollout status deployment/backend -n ppt-rsd-prod
```

### 12.4 流水线流程图

```
代码提交 (Git Push)
    │
    ▼
┌─────────────────┐
│   CODING /      │
│ GitHub Actions  │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│ 构建前端 │ │ 构建后端 │ │ 构建Worker│
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    └──────────┼──────────┘
               ▼
    ┌──────────────────────┐
    │  推送镜像到TCR        │
    │  (腾讯云容器镜像服务)  │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │   部署到TKE集群       │
    │  (腾讯云容器服务)     │
    └──────────────────────┘
```

### 12.5 环境管理

| 环境 | 部署方式 | 触发条件 |
|------|---------|---------|
| 开发环境 | TKE Serverless / 本地 | 功能分支推送 |
| 测试环境 | TKE标准集群 | develop分支合并 |
| 生产环境 | TKE标准集群 | main分支合并 + 手动确认 |

---

## 13. LLM 模型配置指南

### 13.1 支持的模型提供商

| 提供商 | 配置项 | 说明 |
|--------|--------|------|
| **腾讯混元** | `hunyuan` | 国内首选，中文优化 |
| **百度文心** | `wenxin` | 百度生态 |
| **阿里通义** | `qwen` | 阿里生态 |
| **OpenAI** | `openai` | 国际通用 |
| **Claude** | `claude` | Anthropic |
| **自定义** | `custom` | OpenAI兼容格式 |

### 13.2 模型选择建议

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 国内部署 | 腾讯混元/文心/通义 | 国内访问快、合规 |
| 国际部署 | OpenAI/Claude | 性能稳定 |
| 私有化 | 自定义模型 | 数据安全 |
| 成本敏感 | 混元-lite/文心-lite | 免费/低价档位 |

### 13.3 自定义模型接入

```python
# backend/app/infrastructure/llm/custom/my_model.py
from app.infrastructure.llm.providers.custom import CustomLLMProvider

class MyCustomModel(CustomLLMProvider):
    """自定义模型示例"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.api_url = config.get('api_url')
        self.model_name = config.get('model_name')
    
    async def chat(self, messages: list, **kwargs) -> str:
        # 实现自定义调用逻辑
        response = await self._call_api(messages)
        return response

# 在配置中注册
# .env
CUSTOM_MODEL_NAME=my-custom-model
CUSTOM_API_URL=https://your-api.com/v1/chat
CUSTOM_API_KEY=your-key
```

### 13.4 功能降级策略

当LLM服务不可用时，系统支持功能降级：
- **精修功能禁用**：保留基础组装功能
- **本地规则替代**：简单文本替换使用本地规则
- **缓存结果复用**：使用历史相似修改建议

---

## 14. 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 需求文档 | `/docs/requirements.md` | 功能需求说明 |
| 详细设计 | `/docs/design.md` | 系统详细设计 |
| API文档 | `/docs/api.md` | 接口文档 |
| 部署指南 | `/docs/deployment.md` | TKE/轻量服务器部署说明 |
| CI/CD配置 | `/docs/cicd.md` | 流水线配置指南 |
| 开发规范 | `/docs/development.md` | 开发规范 |
| 腾讯云配置 | `/docs/tencent-cloud.md` | 腾讯云产品配置指南 |
| LLM配置 | `/docs/llm-configuration.md` | 多模型配置指南 |

---

*文档版本：v1.1*  
*最后更新：2026-02-09*
