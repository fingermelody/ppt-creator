"""
FastAPI 主应用入口 - SCF 精简版
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# 创建应用
app = FastAPI(
    title="PPT-RSD",
    version="1.0.0",
    description="PPT 智能生成与文档库管理系统 API",
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0", "service": "ppt-rsd-backend"}

@app.get("/")
async def root():
    return {"message": "Welcome to PPT-RSD API", "docs": "/docs"}

@app.get("/api/v1/test")
async def api_test():
    return {"message": "API v1 is working"}

# SCF 事件函数入口
handler = Mangum(app, lifespan="off")
