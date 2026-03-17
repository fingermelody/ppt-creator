# PPT-creator项目

基于工蜂+腾讯云 构建的项目

## 核心功能

### PPT 预览功能 ✨

本项目集成了**腾讯云数据万象文档预览服务**，提供高质量的 PPT 在线预览功能。

#### 功能特点

- **完整预览**：支持完整的 PPT 内容预览，包括动画、特效和高清渲染
- **多种模式**：支持 HTML 预览（交互性好）和图片预览（保真度高）

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

## 许可证

MIT License