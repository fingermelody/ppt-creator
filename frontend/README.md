# PPT-RSD Frontend

基于 React 18 + TypeScript + TDesign 的前端应用。

## 技术栈

- **框架**: React 18
- **语言**: TypeScript 5.x
- **UI组件库**: TDesign React
- **路由**: React Router v6
- **状态管理**: Zustand
- **数据获取**: React Query (@tanstack/react-query)
- **HTTP客户端**: Axios
- **构建工具**: Vite
- **CSS**: 原生CSS + CSS Modules

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API调用层
│   │   ├── client.ts    # Axios实例配置
│   │   ├── documents.ts # 文档管理API
│   │   ├── assembly.ts  # PPT组装API
│   │   ├── refinement.ts# PPT精修API
│   │   └── export.ts    # 导出API
│   ├── components/       # 公共组件
│   │   └── Layout.tsx   # 主布局
│   ├── pages/           # 页面组件
│   │   ├── Library/     # 文档库页面
│   │   ├── Assembly/    # PPT组装页面
│   │   ├── Drafts/      # 草稿管理页面
│   │   └── Refinement/  # PPT精修页面
│   ├── stores/          # 状态管理（Zustand）
│   │   ├── documentStore.ts
│   │   ├── assemblyStore.ts
│   │   └── refinementStore.ts
│   ├── types/           # TypeScript类型定义
│   │   ├── common.ts
│   │   ├── document.ts
│   │   ├── assembly.ts
│   │   └── refinement.ts
│   ├── utils/           # 工具函数
│   │   ├── constants.ts
│   │   ├── helpers.ts
│   │   └── validators.ts
│   ├── styles/          # 全局样式
│   │   └── global.css
│   ├── App.tsx          # 主应用组件
│   ├── main.tsx         # 入口文件
│   └── router.tsx       # 路由配置
├── public/              # 静态资源
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 功能模块

### 1. 文档库 (Library)
- PPT文件上传（支持分片上传）
- 文档列表展示
- 文档页面浏览
- 文档删除

### 2. PPT组装 (Assembly)
- 创建新的PPT草稿
- 添加章节并生成初稿
- 查看章节和页面详情
- 查看备选页面
- 替换页面
- 删除页面
- 调整页面顺序
- 撤销/重做操作
- 导出PPT

### 3. 草稿管理 (Drafts)
- 草稿列表展示
- 搜索草稿
- 编辑草稿
- 删除草稿
- 导出PPT
- 进入精修模式

### 4. PPT精修 (Refinement)
- 页面列表导航
- AI对话编辑
- 实时预览修改
- 对话历史记录
- 导出精修版本

## 开发指南

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

开发服务器将在 `http://localhost:3000` 启动。

### 构建生产版本

```bash
npm run build
```

构建产物将生成在 `dist/` 目录。

### 预览生产版本

```bash
npm run preview
```

### 代码检查

```bash
npm run lint
```

## 环境变量

开发环境 (`.env`):
```
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

生产环境 (`.env.production`):
```
VITE_API_BASE_URL=https://api.ppt-rsd.example.com
VITE_WS_BASE_URL=wss://api.ppt-rsd.example.com
```

## API 代理配置

Vite 已配置代理，开发时所有 `/api` 请求将转发到 `http://localhost:8000`，WebSocket 请求转发到 `ws://localhost:8000`。

## 类型定义

所有类型定义在 `src/types/` 目录下：

- `common.ts` - 通用类型
- `document.ts` - 文档相关类型
- `assembly.ts` - 组装相关类型
- `refinement.ts` - 精修相关类型

## 状态管理

使用 Zustand 进行状态管理：

- `documentStore` - 文档状态
- `assemblyStore` - 组装状态
- `refinementStore` - 精修状态

## 工具函数

常用工具函数在 `src/utils/` 目录：

- `constants.ts` - 常量定义
- `helpers.ts` - 辅助函数
- `validators.ts` - 验证函数

## 浏览器支持

- Chrome (最新版)
- Firefox (最新版)
- Safari (最新版)
- Edge (最新版)

## 注意事项

1. 所有 API 调用都使用 Axios 实例，已在 `api/client.ts` 中配置拦截器
2. 使用 TDesign React 组件库，保持UI一致性
3. 所有组件使用 TypeScript 编写，确保类型安全
4. 使用 React Router 进行页面路由
5. 使用 Zustand 进行全局状态管理

## 开发规范

### 命名规范

- 组件：PascalCase（如 `DocumentCard.tsx`）
- Hooks：camelCase，前缀 `use`（如 `useDocuments.ts`）
- 常量：UPPER_SNAKE_CASE
- 类型：PascalCase

### 代码风格

- 使用 ESLint 进行代码检查
- 遵循 React Hooks 规则
- 组件拆分，单一职责
- 使用 TypeScript 类型注解

## 待实现功能

- [ ] 单元测试
- [ ] E2E测试
- [ ] 性能优化
- [ ] 错误边界
- [ ] 加载状态优化
- [ ] 离线支持
- [ ] 国际化

## 许可证

Copyright © 2026 PPT-RSD Project
