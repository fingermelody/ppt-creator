"""
文档相关 Schema
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.document import DocumentStatus


class UploadInitRequest(BaseModel):
    """上传初始化请求"""
    filename: str
    filesize: int = Field(..., gt=0)
    total_chunks: int = Field(..., ge=1)


class UploadInitResponse(BaseModel):
    """上传初始化响应"""
    upload_id: str
    chunk_size: int
    total_chunks: int


class UploadChunkResponse(BaseModel):
    """分片上传响应"""
    success: bool
    received_chunks: int


class UploadCompleteRequest(BaseModel):
    """上传完成请求"""
    upload_id: str
    title: str  # 文档标题（通常从文件名提取，去除扩展名）
    category: Optional[str] = None  # 可选分类


class UploadCompleteResponse(BaseModel):
    """上传完成响应"""
    document_id: str
    status: str


class SlideResponse(BaseModel):
    """页面响应 Schema"""
    id: str
    document_id: str
    page_number: int
    title: Optional[str] = None
    content_text: Optional[str] = None
    layout_type: Optional[str] = None
    thumbnail_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    vector_id: Optional[str] = None
    is_vectorized: int = 0
    
    class Config:
        from_attributes = True


class SlideDetailResponse(SlideResponse):
    """页面详情响应 Schema（包含源 PPT 信息，用于 PPT 组装）"""
    elements: Optional[List[Any]] = None
    metadata: Optional[dict] = None
    # 源 PPT 信息（用于检索和组装）
    source_url: Optional[str] = None  # 源 PPT 的 COS URL
    source_filename: Optional[str] = None  # 源 PPT 的原始文件名
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SlideSearchResult(BaseModel):
    """页面搜索结果 Schema"""
    slide_id: str
    document_id: str
    page_number: int
    title: Optional[str] = None
    content: str
    source_url: Optional[str] = None  # 源 PPT 的 COS URL
    source_filename: Optional[str] = None  # 源 PPT 的文件名
    similarity: float  # 相似度分数 (0-1)
    distance: float  # 向量距离


class SlideSearchResponse(BaseModel):
    """页面搜索响应 Schema"""
    query: str
    total: int
    results: List[SlideSearchResult]


class DocumentResponse(BaseModel):
    """文档响应 Schema"""
    id: str
    filename: str
    original_filename: str
    file_size: int
    title: Optional[str] = None
    description: Optional[str] = None
    page_count: int
    status: DocumentStatus
    cos_url: Optional[str] = None  # COS 访问 URL
    vectorized_pages: int = 0  # 已向量化的页数
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    """文档详情响应 Schema"""
    slides: List[SlideResponse] = []
    cos_object_key: Optional[str] = None  # COS 对象键


class DocumentListParams(BaseModel):
    """文档列表参数"""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    status: Optional[DocumentStatus] = None
    search: Optional[str] = None
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc")


class DocumentListResponse(BaseModel):
    """文档列表响应"""
    documents: List[DocumentResponse]
    total: int
    page: int
    limit: int
