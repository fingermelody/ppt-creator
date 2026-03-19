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
    version,
    template,
    image,
    collaboration,
    large_file,
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
api_router.include_router(generation.router, prefix="/generation", tags=["智能生成"])

# 精修路由
api_router.include_router(refinement.router, prefix="/refinement", tags=["PPT精修"])

# 版本历史路由
api_router.include_router(version.router, prefix="/refinement", tags=["版本历史"])

# 模板系统路由
api_router.include_router(template.router, prefix="/templates", tags=["模板系统"])

# 图片推荐路由
api_router.include_router(image.router, prefix="/refinement", tags=["智能图片"])

# 协作编辑路由
api_router.include_router(collaboration.router, prefix="/refinement", tags=["协作编辑"])

# 大文件处理路由
api_router.include_router(large_file.router, prefix="/upload", tags=["大文件处理"])
