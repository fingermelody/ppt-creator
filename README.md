# CloudBase 项目

基于云开发 + CloudBase AI ToolKit 构建的项目

[![Powered by CloudBase](https://7463-tcb-advanced-a656fc-1257967285.tcb.qcloud.la/mcp/powered-by-cloudbase-badge.svg)](https://github.com/TencentCloudBase/CloudBase-AI-ToolKit)  

> 本项目基于 [**CloudBase AI ToolKit**](https://github.com/TencentCloudBase/CloudBase-AI-ToolKit) 开发，通过AI提示词和 MCP 协议+云开发，让开发更智能、更高效，支持AI生成全栈代码、一键部署至腾讯云开发（免服务器）、智能日志修复。

## 核心功能

### PPT 预览功能 ✨

本项目集成了**腾讯云数据万象文档预览服务**，提供高质量的 PPT 在线预览功能。

#### 功能特点

- **完整预览**：支持完整的 PPT 内容预览，包括动画、特效和高清渲染
- **多种模式**：支持 HTML 预览（交互性好）和图片预览（保真度高）
- **实时转换**：基于腾讯云数据万象服务，实时转换 PPT 格式
- **智能降级**：当 COS 服务未配置时，自动降级到本地文件预览
- **成本可控**：按量计费，免费额度充足（6000 页/2 个月）

#### 使用方式

1. 在 Assembly 页面点击"预览 PPT"按钮
2. 系统自动导出 PPT 并上传到 COS
3. 使用腾讯云数据万象服务进行实时预览
4. 支持全屏查看、刷新和下载

#### 配置要求

需要在 `.env` 文件中配置以下环境变量：

```bash
# 腾讯云 COS 配置
COS_SECRET_ID=your-secret-id
COS_SECRET_KEY=your-secret-key
COS_REGION=ap-guangzhou
COS_BUCKET=your-bucket-name
```

#### 成本估算

- **文档转 HTML**：0.01 元/次
- **文档转图片**：0.1 元/千页
- **免费额度**：6000 页/2 个月
- **预估成本**（1000 次预览/月）：约 10-20 元

## 技术栈

- **前端**：React 18 + TypeScript + Vite + TDesign UI
- **后端**：Python FastAPI + 腾讯云 COS SDK
- **云服务**：腾讯云数据万象（CI）文档预览
- **数据库**：TDSQL-C PostgreSQL
- **缓存**：腾讯云 Redis
- **存储**：腾讯云 COS

## 快速开始

### 1. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并填写必要的配置信息。

### 3. 启动服务

```bash
# 后端
cd backend
uvicorn app.main:app --reload

# 前端
cd frontend
npm run dev
```

### 4. 访问应用

打开浏览器访问 `http://localhost:5173`

## 项目结构

```
PPT-RSD/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── models/      # 数据模型
│   │   ├── schemas/     # 数据验证模式
│   │   ├── services/    # 业务逻辑
│   │   │   ├── ppt_export.py      # PPT 导出服务
│   │   │   └── cos_upload.py      # COS 上传服务
│   │   └── main.py      # 应用入口
│   └── requirements.txt
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── components/  # 公共组件
│   │   │   └── PPTViewer/         # PPT 预览组件
│   │   ├── pages/       # 页面组件
│   │   │   └── Assembly/          # PPT 组装页面
│   │   ├── api/         # API 调用
│   │   └── stores/      # 状态管理
│   └── package.json
└── README.md
```

## 开发指南

### PPT 预览功能开发

#### 前端组件

```tsx
import PPTViewer from '@/components/PPTViewer';

<PPTViewer
  visible={showPreview}
  fileUrl={previewUrl}
  fileName={fileName}
  onClose={() => setShowPreview(false)}
  onDownload={handleDownload}
/>
```

#### 后端 API

```python
# 预览端点
POST /api/drafts/{draft_id}/preview

# 返回格式
{
  "download_url": "https://cos-url?ci-process=doc-preview&dstType=html",
  "file_size": 1024000,
  "file_name": "演示文稿.pptx",
  "exported_at": "2025-03-06T10:00:00"
}
```

### 自定义预览参数

腾讯云数据万象支持多种预览参数：

```javascript
// HTML 预览（默认）
url?ci-process=doc-preview&dstType=html

// 图片预览
url?ci-process=doc-preview&dstType=jpg

// 指定页码
url?ci-process=doc-preview&dstType=html&page=1
```

更多参数请参考 [腾讯云数据万象文档](https://cloud.tencent.com/document/product/460/46499)。

## 许可证

MIT License