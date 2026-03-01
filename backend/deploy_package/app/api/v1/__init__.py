"""
API v1 模块
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    documents,
    outline,
    assembly,
    drafts,
    generation,
    refinement,
)

api_router = APIRouter()

# 认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 文档管理路由
api_router.include_router(documents.router, prefix="/documents", tags=["文档管理"])

# 大纲设计路由
api_router.include_router(outline.router, prefix="/outlines", tags=["大纲设计"])

# PPT 组装路由
api_router.include_router(assembly.router, prefix="/assembly", tags=["PPT组装"])

# 草稿管理路由
api_router.include_router(drafts.router, prefix="/drafts", tags=["草稿管理"])

# 智能生成路由
api_router.include_router(generation.router, prefix="/v1/generation", tags=["智能生成"])

# 精修路由
api_router.include_router(refinement.router, prefix="/refinement", tags=["PPT精修"])
