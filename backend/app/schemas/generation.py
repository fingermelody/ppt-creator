"""
PPT 智能生成相关 Schema
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.generation import GenerationStatus, SearchDepth


class TemplateColorScheme(BaseModel):
    """配色方案"""
    primary: str
    secondary: str
    accent: str
    background: str
    text: str


class TemplateResponse(BaseModel):
    """模板响应 Schema"""
    id: str
    name: str
    description: Optional[str] = None
    category: str
    preview_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    color_scheme: Optional[TemplateColorScheme] = None
    font_family: Optional[str] = None
    is_premium: bool
    usage_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    templates: List[TemplateResponse]
    total: int
    categories: List[str]


class TemplateUploadResponse(BaseModel):
    """模板上传响应"""
    template_id: str
    preview_url: str
    name: str


class WebSourceResponse(BaseModel):
    """网络来源响应 Schema"""
    id: str
    title: str
    url: str
    snippet: Optional[str] = None
    relevance: float
    is_used: bool
    
    class Config:
        from_attributes = True


class PageContentResponse(BaseModel):
    """页面内容响应"""
    title: Optional[str] = None
    subtitle: Optional[str] = None
    bullet_points: Optional[List[str]] = None
    paragraphs: Optional[List[str]] = None
    images: Optional[List[dict]] = None
    charts: Optional[List[dict]] = None
    tables: Optional[List[dict]] = None


class GeneratedPageResponse(BaseModel):
    """生成的页面响应 Schema"""
    id: str
    page_index: int
    title: Optional[str] = None
    content: Optional[PageContentResponse] = None
    thumbnail_path: Optional[str] = None
    source_ids: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class GenerationTaskResponse(BaseModel):
    """生成任务响应 Schema"""
    id: str
    title: Optional[str] = None
    topic: str
    status: GenerationStatus
    progress: int
    current_step: Optional[str] = None
    message: Optional[str] = None
    total_pages: int
    sources_found: int
    template_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GenerationTaskDetailResponse(GenerationTaskResponse):
    """生成任务详情响应 Schema"""
    pages: List[GeneratedPageResponse] = []
    sources: List[WebSourceResponse] = []
    error_message: Optional[str] = None
    exported_file_path: Optional[str] = None


class TaskListResponse(BaseModel):
    """任务列表响应"""
    tasks: List[GenerationTaskResponse]
    total: int


class GenerationRequest(BaseModel):
    """生成请求 Schema"""
    topic: str = Field(..., min_length=10, max_length=2000, description="主题描述")
    title: Optional[str] = Field(None, max_length=255, description="PPT标题")
    page_count: int = Field(default=10, ge=5, le=30, description="期望页数")
    template_id: Optional[str] = None
    include_images: bool = True
    include_charts: bool = True
    language: str = Field(default="zh", pattern="^(zh|en)$")
    search_depth: SearchDepth = SearchDepth.NORMAL


class GenerationResponse(BaseModel):
    """生成响应 Schema"""
    task_id: str
    status: GenerationStatus
    message: str
    estimated_time: Optional[int] = None  # 预估时间（秒）


class GenerationProgressResponse(BaseModel):
    """生成进度响应 Schema"""
    task_id: str
    status: GenerationStatus
    progress: int
    current_step: str
    message: str
    sources_found: Optional[int] = None
    pages_generated: Optional[int] = None


class RegeneratePageRequest(BaseModel):
    """重新生成页面请求"""
    instructions: Optional[str] = None


class RegeneratePageResponse(BaseModel):
    """重新生成页面响应"""
    success: bool
    page: GeneratedPageResponse
    message: str


class PageSourcesResponse(BaseModel):
    """页面来源响应"""
    sources: List[WebSourceResponse]
    citations: List[dict]


class ExportRequest(BaseModel):
    """导出请求"""
    format: str = Field(default="pptx", pattern="^(pptx|pdf)$")


class ExportResponse(BaseModel):
    """导出响应"""
    download_url: str
    file_size: int
    file_name: str
    exported_at: datetime


class SearchMoreRequest(BaseModel):
    """搜索更多来源请求"""
    query: Optional[str] = None


class SearchMoreResponse(BaseModel):
    """搜索更多来源响应"""
    success: bool
    new_sources: List[WebSourceResponse]
    total_sources: int
