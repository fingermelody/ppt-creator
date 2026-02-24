# PPT-Creator 智能PPT生成系统 - 项目结构文档

## 1. 项目概述

本项目是一个基于Web的PPT页面拼凑组装系统，采用前后端分离架构，支持用户从本地PPT文档库中检索相关页面，以"页面复制"方式组装成新PPT。

**技术栈**：
- 前端：React 18 + TypeScript + TDesign + Zustand + React Query
- 后端：Python 3.9+ + FastAPI + SQLAlchemy + Celery
- 数据库：SQLite（开发）/ MySQL（生产）+ Redis + ChromaDB
- 部署：轻量服务器 + Docker Compose（推荐）/ 腾讯云TKE容器服务
- 流水线：GitHub Actions（免费）/ 腾讯云CODING DevOps
- LLM：可选，优先使用免费额度（混元-lite/文心-lite/通义-free）

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
│   │   ├── Generation/       # PPT智能生成页面
│   │   │   ├── index.tsx
│   │   │   ├── index.css
│   │   │   └── components/
│   │   │       ├── ProgressModal.tsx    # 生成进度弹窗
│   │   │       └── TemplateCard.tsx     # 模板卡片组件
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
│   │   ├── generationStore.ts # PPT智能生成状态
│   │   └── uiStore.ts
│   │
│   ├── types/                # TypeScript类型定义
│   │   ├── document.ts
│   │   ├── outline.ts        # 大纲相关类型
│   │   ├── assembly.ts
│   │   ├── refinement.ts
│   │   ├── generation.ts     # PPT智能生成类型
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
│   │   │   │   ├── generation.py   # PPT智能生成接口
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
│   │   ├── generation.py     # 智能生成任务模型
│   │   └── base.py           # 基础模型
│   │
│   ├── schemas/              # Pydantic数据模型
│   │   ├── __init__.py
│   │   ├── document.py
│   │   ├── slide.py
│   │   ├── outline.py        # 大纲请求/响应模型
│   │   ├── assembly.py
│   │   ├── refinement.py
│   │   ├── generation.py     # 智能生成请求/响应模型
│   │   └── common.py
│   │
│   ├── services/             # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   ├── slide_service.py
│   │   ├── outline_service.py    # 大纲生成服务
│   │   ├── assembly_service.py
│   │   ├── refinement_service.py
│   │   ├── generation_service.py # PPT智能生成服务
│   │   ├── web_search_service.py # 联网搜索服务
│   │   ├── template_service.py   # 模板管理服务
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
┌─────────────────────────────────────────────────────────────────────────────┐
│                             页面层 (Pages)                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  │ Library  │ │ Outline  │ │ Assembly │ │Refinement│ │Generation│ │ Drafts│ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬───┘ │
└───────┼────────────┼────────────┼────────────┼────────────┼───────────┼─────┘
        │            │            │            │            │           │
        └────────────┴─────┬──────┴────────────┴────────────┴───────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           业务组件层                                          │
│  ┌──────────┐ ┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│  │ Document │ │   Outline    │ │ Assembly │ │Refinement│ │   Generation   │ │
│  │Components│ │  Components  │ │Components│ │Components│ │   Components   │ │
│  └────┬─────┘ └──────┬───────┘ └────┬─────┘ └────┬─────┘ └───────┬────────┘ │
└───────┼──────────────┼──────────────┼────────────┼───────────────┼──────────┘
        │              │              │            │               │
        └──────────────┴──────┬───────┴────────────┴───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           基础层                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐                      │
│  │   API    │ │  Stores  │ │  Hooks   │ │ Components │                      │
│  │  Layer   │ │(Zustand) │ │          │ │  (Common)  │                      │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 后端模块依赖

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API 层 (Routers)                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐ │
│  │/documents│ │ /outline │ │/assembly │ │/refinement│ │    /generation     │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬──────┘ └─────────┬──────────┘ │
└───────┼────────────┼────────────┼────────────┼──────────────────┼────────────┘
        │            │            │            │                  │
        └────────────┴─────┬──────┴────────────┴──────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Service 层（业务逻辑）                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐ │
│  │ Document │ │ Outline  │ │ Assembly │ │Refinement│ │     Generation     │ │
│  │ Service  │ │ Service  │ │ Service  │ │ Service  │ │      Service       │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────────────────┘ │
│                                                      ┌────────────────────┐ │
│                                                      │  WebSearch/Template│ │
│                                                      │      Services      │ │
│                                                      └────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
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

### 8.4 PPT智能生成流程

```
Frontend                    Backend                     WebSearch/LLM
   │                          │                           │
   │  1. 提交生成请求          │                           │
   │     (主题/页数/模板)      │                           │
   │ ───────────────────────> │                           │
   │                          │  2. 创建生成任务           │
   │                          │  3. 联网搜索               │
   │                          │ ────────────────────────> │
   │  4. WebSocket进度推送     │ <──────────────────────── │
   │ <─────────────────────── │  (搜索中: 10%)             │
   │                          │                           │
   │                          │  5. 内容分析               │
   │                          │ ────────────────────────> │
   │  6. WebSocket进度推送     │ <──────────────────────── │
   │ <─────────────────────── │  (分析中: 30%)             │
   │                          │                           │
   │                          │  7. 逐页生成PPT内容        │
   │                          │ ────────────────────────> │
   │  8. WebSocket进度推送     │ <──────────────────────── │
   │ <─────────────────────── │  (生成中: 40-80%)          │
   │                          │                           │
   │                          │  9. 应用风格模板           │
   │  10. WebSocket进度推送    │  (应用风格: 85%)           │
   │ <─────────────────────── │                           │
   │                          │                           │
   │  11. 生成完成             │  12. 保存生成结果          │
   │ <─────────────────────── │  (完成: 100%)              │
   │                          │                           │
   │  13. 预览/进入精修        │                           │
   │ ───────────────────────> │                           │
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

### 9.3 PPT智能生成模块示例

以PPT智能生成模块为例，展示包含联网搜索等复杂功能的模块结构：

```
前端新增文件：
├── src/
│   ├── api/
│   │   └── generation.ts           # 生成API接口
│   ├── pages/
│   │   └── Generation/
│   │       ├── index.tsx           # 生成页面主入口
│   │       ├── index.css           # 生成页面样式
│   │       └── components/
│   │           ├── ProgressModal.tsx    # 生成进度弹窗
│   │           └── TemplateCard.tsx     # 模板卡片组件
│   ├── stores/
│   │   └── generationStore.ts      # 生成状态管理
│   └── types/
│       └── generation.ts           # 生成类型定义

后端新增文件：
├── app/
│   ├── api/v1/endpoints/
│   │   └── generation.py           # 生成路由
│   ├── services/
│   │   ├── generation_service.py   # 生成服务
│   │   ├── web_search_service.py   # 联网搜索服务
│   │   └── template_service.py     # 模板管理服务
│   ├── models/
│   │   └── generation.py           # 生成任务模型
│   └── schemas/
│       └── generation.py           # 生成Pydantic模型
```

### 9.4 可替换组件

| 组件 | 推荐实现（高性价比） | 备选方案（付费） |
|------|---------------------|-----------------|
| 向量数据库 | ChromaDB（本地免费） | 腾讯云向量数据库 |
| 文件存储 | 本地文件系统 / MinIO | 腾讯云COS |
| LLM服务 | 混元-lite免费额度 | 付费模型 |
| 缓存 | 本地Redis容器 | 腾讯云Redis |
| 数据库 | SQLite/本地MySQL | 腾讯云TDSQL-C |
| 服务器 | 轻量服务器（促销价） | 腾讯云TKE/CVM |
| 镜像仓库 | Docker Hub免费 | 腾讯云TCR |

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

## 11. 部署方案（高性价比优先）

### 11.1 部署架构选型

| 场景 | 推荐方案 | 月成本预估 | 适用说明 |
|------|---------|-----------|---------|
| **开发测试（推荐）** | 本地 Docker Compose | ￥0 | 本机开发调试 |
| **个人项目（⭐首选）** | 轻量服务器 + 全本地服务 | ￥35-50 | 新用户促销价，极致性价比 |
| **小团队** | 轻量服务器 + 云数据库 | ￥60-100 | 数据更安全 |
| **中大规模** | TKE Serverless | ￥200-500 | 按需计费，弹性扩缩 |

### 11.2 推荐资源配置

#### 方案A：极简部署（⭐⭐⭐ 最高性价比，首选推荐）

> 💰 **月成本：￥35-50**  
> 💡 **核心原则**：能本地就本地，能免费就免费，所有服务一台机器搞定

| 组件 | 推荐配置 | 月成本 | 说明 |
|------|---------|--------|------|
| **服务器** | 腾讯云轻量 2核2G 50G SSD 4M | ￥35-45 | 新用户首年特惠 |
| **数据库** | SQLite（开发）/ MySQL Docker | ￥0 | 本地容器部署 |
| **缓存** | Redis Docker 容器 | ￥0 | 本地容器部署 |
| **向量库** | ChromaDB Docker 容器 | ￥0 | 本地容器部署 |
| **文件存储** | 服务器本地磁盘 | ￥0 | 自带50G存储 |
| **镜像仓库** | 阿里云ACR个人版 | ￥0 | 永久免费 |
| **CI/CD** | GitHub Actions | ￥0 | 公开仓库无限制 |
| **LLM服务** | 通义千问-turbo免费版 | ￥0 | 100万tokens/月 |
| **CDN加速** | Cloudflare | ￥0 | 免费无限流量 |
| **SSL证书** | Let's Encrypt | ￥0 | 免费自动续期 |
| **合计** | - | **￥35-50/月** | - |

**适用场景**：个人项目、小型团队（<10人）、日活<1000

#### 方案B：进阶部署（数据安全优先）

> 💰 **月成本：￥60-100**  
> 💡 **适用场景**：对数据安全有要求，需要数据备份

| 组件 | 推荐配置 | 月成本 | 说明 |
|------|---------|--------|------|
| **服务器** | 腾讯云轻量 2核4G 60G SSD 6M | ￥50-70 | 新用户首年特惠 |
| **数据库** | TDSQL-C Serverless | ￥5-30 | 按量计费，空闲几乎免费 |
| **缓存** | Redis Docker 容器 | ￥0 | 本地部署即可 |
| **向量库** | ChromaDB Docker 容器 | ￥0 | 本地部署 |
| **文件存储** | 腾讯云COS | ￥0-5 | 50G免费额度 |
| **LLM服务** | 混元-lite 免费额度 | ￥0 | 50万tokens/月 |
| **合计** | - | **￥60-100/月** | - |

#### 方案C：弹性部署（中大规模）

> 💰 **月成本：￥200-500**  
> 💡 **适用场景**：用户量波动大，需要弹性扩缩

| 组件 | 推荐配置 | 月成本 | 说明 |
|------|---------|--------|------|
| **计算** | TKE Serverless | ￥100-300 | 按实际使用计费 |
| **数据库** | TDSQL-C Serverless | ￥30-100 | 自动扩缩 |
| **缓存** | 腾讯云Redis 256MB | ￥30-50 | 最小规格 |
| **文件存储** | 腾讯云COS | ￥10-30 | 按量计费 |
| **合计** | - | **￥200-500/月** | - |

### 11.3 免费资源一览表

| 服务类型 | 服务商 | 免费额度 | 有效期 | 推荐指数 |
|---------|-------|---------|--------|---------|
| **LLM服务** | | | | |
| 通义千问 qwen-turbo | 阿里云 | 100万tokens/月 | 永久 | ⭐⭐⭐⭐⭐ |
| 混元-lite | 腾讯云 | 50万tokens/月 | 需申请 | ⭐⭐⭐⭐ |
| 文心 ERNIE-Lite-8K | 百度 | 免费调用 | 永久 | ⭐⭐⭐⭐ |
| GLM-4-Flash | 智谱AI | 免费调用 | 永久 | ⭐⭐⭐⭐ |
| **对象存储** | | | | |
| 腾讯云COS | 腾讯云 | 50GB + 10GB流量/月 | 6个月 | ⭐⭐⭐⭐ |
| 阿里云OSS | 阿里云 | 5GB存储 | 永久 | ⭐⭐⭐ |
| **容器镜像** | | | | |
| 腾讯云个人版CCR | 腾讯云 | 无限镜像 | 永久 | ⭐⭐⭐⭐⭐ |
| Docker Hub | Docker | 1私有+无限公开仓库 | 永久 | ⭐⭐⭐⭐ |
| **CI/CD** | | | | |
| GitHub Actions | GitHub | 2000分钟/月 | 永久 | ⭐⭐⭐⭐⭐ |
| Gitee Go | Gitee | 200分钟/月 | 永久 | ⭐⭐⭐ |
| **CDN/网络** | | | | |
| Cloudflare CDN | Cloudflare | 无限流量 | 永久 | ⭐⭐⭐⭐⭐ |
| **SSL证书** | | | | |
| Let's Encrypt | ISRG | 免费证书 | 永久 | ⭐⭐⭐⭐⭐ |
| 腾讯云免费证书 | 腾讯云 | 1年DV证书 | 可续期 | ⭐⭐⭐⭐ |
| **数据库** | | | | |
| TDSQL-C Serverless | 腾讯云 | 按量计费（空闲￥0） | 永久 | ⭐⭐⭐⭐ |
| PlanetScale | PlanetScale | 5GB存储 | 永久 | ⭐⭐⭐ |

### 11.4 服务器选购指南

#### 腾讯云轻量服务器活动价参考

| 配置 | 原价 | 新用户首年 | 续费价 | 推荐场景 |
|------|-----|-----------|-------|---------|
| 2核2G 50G 4M | ￥100+/月 | ￥35-45/月 | ￥60-80/月 | 个人项目 |
| 2核4G 60G 6M | ￥150+/月 | ￥50-70/月 | ￥100-120/月 | 小团队 |
| 4核8G 80G 10M | ￥300+/月 | ￥100-150/月 | ￥200+/月 | 中型项目 |

> 💡 **省钱技巧**：
> 1. 关注腾讯云/阿里云大促活动（618、双11、年终）
> 2. 新用户首单优惠力度最大，建议一次买3年
> 3. 轻量服务器性价比 > CVM
> 4. 竞价实例适合可中断的任务（便宜50-80%）

### 11.5 开发环境

```bash
# 本地开发（零成本）
# 前端
cd frontend && npm run dev

# 后端（使用SQLite作为开发数据库）
cd backend && uvicorn app.main:app --reload

# 任务队列（可选，开发时可跳过）
cd workers && celery -A app.celery_app worker --loglevel=info
```

### 11.6 一键部署（轻量服务器）

```bash
# 1. 购买轻量服务器后SSH登录
ssh root@<lighthouse-ip>

# 2. 安装 Docker（一键脚本）
curl -fsSL https://get.docker.com | bash
systemctl enable docker && systemctl start docker

# 3. 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 4. 克隆代码并部署
git clone <repo-url> /opt/ppt-rsd
cd /opt/ppt-rsd/deployment/docker
cp .env.example .env

# 5. 配置免费 LLM API（选一个）
# 通义千问免费版（推荐）：https://dashscope.console.aliyun.com/
# 混元免费版：https://cloud.tencent.com/product/hunyuan

# 6. 启动所有服务
docker-compose up -d

# 7. 配置免费SSL（使用 certbot）
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

### 11.7 环境变量配置（高性价比版）

```bash
# .env.production（优先使用免费服务）

# ============================================
# 数据库配置（本地Docker容器，￥0）
# ============================================
DATABASE_URL=mysql+pymysql://root:password@mysql:3306/ppt_rsd

# ============================================
# Redis配置（本地Docker容器，￥0）
# ============================================
REDIS_URL=redis://redis:6379/0

# ============================================
# 文件存储（本地磁盘，￥0）
# ============================================
STORAGE_TYPE=local
STORAGE_PATH=/app/data

# 如需使用云存储（有50G免费额度）
# STORAGE_TYPE=cos
# COS_SECRET_ID=your-secret-id
# COS_SECRET_KEY=your-secret-key
# COS_REGION=ap-guangzhou
# COS_BUCKET=ppt-rsd-files

# ============================================
# LLM 配置（优先使用免费额度）
# ============================================
LLM_ENABLED=true

# 推荐方案1：通义千问免费版（100万tokens/月）⭐推荐
LLM_DEFAULT_PROVIDER=qwen
QWEN_API_KEY=your-dashscope-api-key
QWEN_MODEL=qwen-turbo  # 免费版

# 推荐方案2：混元-lite（50万tokens/月）
# LLM_DEFAULT_PROVIDER=hunyuan
# HUNYUAN_SECRET_ID=your-secret-id
# HUNYUAN_SECRET_KEY=your-secret-key
# HUNYUAN_MODEL=hunyuan-lite

# 推荐方案3：文心免费版
# LLM_DEFAULT_PROVIDER=wenxin
# WENXIN_API_KEY=your-api-key
# WENXIN_SECRET_KEY=your-secret-key
# WENXIN_MODEL=ernie-lite-8k  # 免费

# 推荐方案4：智谱GLM免费版
# LLM_DEFAULT_PROVIDER=zhipu
# ZHIPU_API_KEY=your-api-key
# ZHIPU_MODEL=glm-4-flash  # 免费

# ============================================
# 镜像仓库（使用腾讯云个人版镜像仓库，免费）
# ============================================
REGISTRY=ccr.ccs.tencentyun.com
REGISTRY_NAMESPACE=codebuddy-ppt-creator
```

---

## 12. CI/CD 流水线配置（免费方案）

### 12.1 方案选型

| 方案 | 成本 | 适用场景 | 推荐指数 |
|------|-----|---------|---------|
| **GitHub Actions** | ￥0 | 公开仓库 | ⭐⭐⭐⭐⭐ |
| **Gitee Go** | ￥0 | 私有仓库（200分钟/月） | ⭐⭐⭐ |
| **腾讯云CODING** | 按量计费 | 企业私有部署 | ⭐⭐⭐ |

### 12.2 GitHub Actions + 腾讯云CCR（完全免费）

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]

env:
  REGISTRY: registry.cn-hangzhou.aliyuncs.com
  NAMESPACE: your-namespace

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # 登录腾讯云个人版镜像仓库（免费）
      - name: Login to Tencent CCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.TCR_USERNAME }}
          password: ${{ secrets.TCR_PASSWORD }}
      
      # 构建并推送镜像
      - name: Build and Push Images
        run: |
          # 前端
          docker build -t $REGISTRY/$NAMESPACE/frontend:${{ github.sha }} -f deployment/docker/Dockerfile.frontend .
          docker push $REGISTRY/$NAMESPACE/frontend:${{ github.sha }}
          
          # 后端
          docker build -t $REGISTRY/$NAMESPACE/backend:${{ github.sha }} -f deployment/docker/Dockerfile.backend .
          docker push $REGISTRY/$NAMESPACE/backend:${{ github.sha }}
      
      # SSH部署到轻量服务器
      - name: Deploy to Server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: root
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/ppt-rsd
            docker-compose pull
            docker-compose up -d
            docker image prune -f
```

### 12.3 简化部署流程图

```
代码推送 (git push)
    │
    ▼
┌─────────────────────┐
│   GitHub Actions    │  ← 免费 2000分钟/月
│   (自动触发)         │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────┐   ┌────────┐
│构建前端 │   │构建后端 │  ← 并行构建
└───┬────┘   └───┬────┘
    │            │
    └──────┬─────┘
           ▼
┌─────────────────────┐
│  推送到腾讯云CCR     │  ← 免费镜像仓库
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SSH部署到服务器     │  ← docker-compose up -d
└─────────────────────┘
```

---

## 13. LLM 模型配置指南（免费优先）

### 13.1 免费LLM服务推荐

| 提供商 | 免费模型 | 免费额度 | 申请链接 | 推荐指数 |
|--------|---------|---------|---------|---------|
| **阿里通义** | qwen-turbo | 100万tokens/月 | [控制台](https://dashscope.console.aliyun.com/) | ⭐⭐⭐⭐⭐ |
| **智谱AI** | glm-4-flash | 无限制 | [开放平台](https://open.bigmodel.cn/) | ⭐⭐⭐⭐⭐ |
| **百度文心** | ernie-lite-8k | 免费调用 | [千帆平台](https://qianfan.cloud.baidu.com/) | ⭐⭐⭐⭐ |
| **腾讯混元** | hunyuan-lite | 50万tokens/月 | [控制台](https://cloud.tencent.com/product/hunyuan) | ⭐⭐⭐⭐ |
| **讯飞星火** | spark-lite | 200万tokens | [开放平台](https://xinghuo.xfyun.cn/) | ⭐⭐⭐ |

### 13.2 配置优先级建议

```bash
# 推荐配置顺序（按性价比排序）

# 1️⃣ 首选：通义千问免费版（100万tokens/月，效果好）
LLM_DEFAULT_PROVIDER=qwen
QWEN_API_KEY=sk-xxx
QWEN_MODEL=qwen-turbo

# 2️⃣ 备选：智谱GLM免费版（无限制，响应快）
# LLM_DEFAULT_PROVIDER=zhipu
# ZHIPU_API_KEY=xxx
# ZHIPU_MODEL=glm-4-flash

# 3️⃣ 备选：文心免费版（稳定可靠）
# LLM_DEFAULT_PROVIDER=wenxin
# WENXIN_API_KEY=xxx
# WENXIN_SECRET_KEY=xxx
# WENXIN_MODEL=ernie-lite-8k
```

### 13.3 模型能力对比

| 模型 | 中文理解 | 响应速度 | 上下文长度 | 适用场景 |
|------|---------|---------|-----------|---------|
| qwen-turbo | ⭐⭐⭐⭐⭐ | 快 | 8K | 通用对话、内容生成 |
| glm-4-flash | ⭐⭐⭐⭐ | 极快 | 128K | 长文本处理 |
| ernie-lite-8k | ⭐⭐⭐⭐ | 快 | 8K | 中文理解 |
| hunyuan-lite | ⭐⭐⭐⭐ | 中等 | 8K | 腾讯生态集成 |

### 13.4 功能降级策略

当LLM服务不可用或额度用尽时，系统支持功能降级：

| 功能 | 有LLM | 无LLM（降级） |
|------|-------|--------------|
| 智能大纲生成 | ✅ AI生成 | ⚠️ 使用预设模板 |
| AI精修建议 | ✅ 智能建议 | ⚠️ 基于规则的建议 |
| 内容优化 | ✅ AI优化 | ❌ 功能禁用 |
| 基础组装 | ✅ 正常 | ✅ 正常（不受影响）|

### 13.5 成本控制建议

```python
# 后端配置：限制每日调用量
LLM_DAILY_LIMIT=10000  # 每日最大调用tokens
LLM_CACHE_ENABLED=true  # 启用响应缓存
LLM_CACHE_TTL=3600      # 缓存1小时

# 前端配置：防抖避免重复调用
DEBOUNCE_DELAY=500      # 500ms防抖
```

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

*文档版本：v1.2*  
*最后更新：2026-02-24*
