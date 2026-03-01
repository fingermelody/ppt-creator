"""
草稿相关 Schema
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.draft import DraftStatus


class DraftPageBase(BaseModel):
    """草稿页面基础 Schema"""
    title: Optional[str] = None
    order_index: int = 0


class DraftPageCreate(DraftPageBase):
    """草稿页面创建 Schema"""
    source_slide_id: Optional[str] = None
    section_id: Optional[str] = None


class DraftPageUpdate(BaseModel):
    """草稿页面更新 Schema"""
    title: Optional[str] = None
    order_index: Optional[int] = None
    content: Optional[Any] = None


class DraftPageResponse(DraftPageBase):
    """草稿页面响应 Schema"""
    id: str
    draft_id: str
    source_slide_id: Optional[str] = None
    section_id: Optional[str] = None
    thumbnail_path: Optional[str] = None
    is_modified: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DraftPageDetailResponse(DraftPageResponse):
    """草稿页面详情响应 Schema"""
    content: Optional[Any] = None


class DraftBase(BaseModel):
    """草稿基础 Schema"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None


class DraftCreate(DraftBase):
    """草稿创建 Schema"""
    outline_id: Optional[str] = None


class DraftUpdate(BaseModel):
    """草稿更新 Schema"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[DraftStatus] = None


class DraftResponse(DraftBase):
    """草稿响应 Schema"""
    id: str
    outline_id: Optional[str] = None
    status: DraftStatus
    page_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DraftDetailResponse(DraftResponse):
    """草稿详情响应 Schema"""
    pages: List[DraftPageResponse] = []
    exported_file_path: Optional[str] = None


class DraftListResponse(BaseModel):
    """草稿列表响应"""
    drafts: List[DraftResponse]
    total: int


# 页面操作相关
class AddPageRequest(BaseModel):
    """添加页面请求"""
    slide_id: str
    section_id: Optional[str] = None
    position: Optional[int] = None  # 插入位置，不指定则追加到末尾


class AddPagesRequest(BaseModel):
    """批量添加页面请求"""
    slide_ids: List[str]
    section_id: Optional[str] = None


class RemovePageRequest(BaseModel):
    """移除页面请求"""
    page_id: str


class ReorderPagesRequest(BaseModel):
    """重排页面请求"""
    page_orders: List[dict]  # [{"page_id": "xxx", "order_index": 0}, ...]


class DraftExportRequest(BaseModel):
    """草稿导出请求"""
    format: str = Field(default="pptx", pattern="^(pptx|pdf)$")


class DraftExportResponse(BaseModel):
    """草稿导出响应"""
    download_url: str
    file_size: int
    file_name: str
    exported_at: datetime
