"""
模板系统 Schema
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ 请求模型 ============

class CreateTemplateRequest(BaseModel):
    """创建模板请求"""
    name: str = Field(..., max_length=255, description="模板名称")
    description: Optional[str] = Field(None, max_length=2000, description="模板描述")
    category: str = Field("business", description="模板分类")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    is_public: bool = Field(True, description="是否公开")
    config: Optional[Dict[str, Any]] = Field(None, description="模板配置")


class UpdateTemplateRequest(BaseModel):
    """更新模板请求"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class ApplyTemplateRequest(BaseModel):
    """应用模板请求"""
    template_id: str = Field(..., description="模板ID")
    target_type: str = Field(..., description="目标类型: draft, outline")
    target_id: str = Field(..., description="目标ID")


# ============ 响应模型 ============

class TemplatePageInfo(BaseModel):
    """模板页面信息"""
    id: str
    order_index: int
    name: Optional[str] = None
    layout_type: Optional[str] = None
    thumbnail_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class TemplateInfo(BaseModel):
    """模板信息"""
    id: str
    name: str
    description: Optional[str] = None
    category: str
    status: str
    is_system: bool
    is_public: bool
    thumbnail_url: Optional[str] = None
    preview_images: Optional[List[str]] = None
    file_size: int
    use_count: int
    like_count: int
    tags: Optional[List[str]] = None
    creator_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TemplateDetailResponse(TemplateInfo):
    """模板详情响应"""
    pages: List[TemplatePageInfo] = []
    config: Optional[Dict[str, Any]] = None
    layouts: Optional[List[Dict[str, Any]]] = None


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    templates: List[TemplateInfo]
    total: int
    page: int
    page_size: int


class CreateTemplateResponse(BaseModel):
    """创建模板响应"""
    success: bool
    template_id: str
    created_at: datetime


class ApplyTemplateResponse(BaseModel):
    """应用模板响应"""
    success: bool
    applied_at: datetime
    pages_created: int


class UploadTemplateResponse(BaseModel):
    """上传模板响应"""
    success: bool
    template_id: str
    file_path: str
    file_size: int
    pages_count: int
    thumbnail_url: Optional[str] = None


class TemplateCategoryInfo(BaseModel):
    """模板分类信息"""
    category: str
    name: str
    count: int
    icon: Optional[str] = None


class TemplateCategoriesResponse(BaseModel):
    """模板分类列表响应"""
    categories: List[TemplateCategoryInfo]


class FavoriteResponse(BaseModel):
    """收藏操作响应"""
    success: bool
    is_favorited: bool
    total_favorites: int
