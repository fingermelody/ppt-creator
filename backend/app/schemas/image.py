"""
智能图片推荐 Schema
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ 图片信息 ============

class ImageInfo(BaseModel):
    """图片信息"""
    id: str
    url: str
    thumbnail_url: Optional[str] = None
    source: str
    title: Optional[str] = None
    description: Optional[str] = None
    alt_text: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    tags: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class RecommendedImage(BaseModel):
    """推荐的图片"""
    url: str
    thumbnail_url: str
    source: str
    source_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    alt_text: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    relevance_score: float = Field(..., description="相关性评分 0-1")
    keywords_matched: Optional[List[str]] = None


# ============ 请求模型 ============

class GetRecommendationsRequest(BaseModel):
    """获取图片推荐请求"""
    content: Optional[str] = Field(None, description="页面内容")
    title: Optional[str] = Field(None, description="页面标题")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")
    style: Optional[str] = Field(None, description="图片风格偏好")
    count: int = Field(10, ge=1, le=50, description="推荐数量")


class SearchImagesRequest(BaseModel):
    """搜索图片请求"""
    query: str = Field(..., min_length=1, max_length=200, description="搜索关键词")
    source: Optional[str] = Field(None, description="图片来源筛选")
    category: Optional[str] = Field(None, description="分类筛选")
    orientation: Optional[str] = Field(None, description="方向: landscape, portrait, square")
    color: Optional[str] = Field(None, description="颜色筛选")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=50)


class UploadImageRequest(BaseModel):
    """上传图片元数据"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[List[str]] = None
    category: str = Field("other", description="图片分类")


class InsertImageRequest(BaseModel):
    """插入图片请求"""
    image_url: str = Field(..., description="图片URL")
    image_id: Optional[str] = Field(None, description="图片库中的图片ID")
    position: Optional[Dict[str, float]] = Field(None, description="位置 {x, y}")
    size: Optional[Dict[str, float]] = Field(None, description="尺寸 {width, height}")


class AnalyzeImageRequest(BaseModel):
    """分析图片请求"""
    image_url: str = Field(..., description="图片URL")


# ============ 响应模型 ============

class RecommendationsResponse(BaseModel):
    """图片推荐响应"""
    images: List[RecommendedImage]
    keywords_used: List[str]
    total: int


class SearchImagesResponse(BaseModel):
    """搜索图片响应"""
    images: List[RecommendedImage]
    total: int
    page: int
    page_size: int
    query: str


class ImageLibraryResponse(BaseModel):
    """图片库列表响应"""
    images: List[ImageInfo]
    total: int
    page: int
    page_size: int


class UploadImageResponse(BaseModel):
    """上传图片响应"""
    success: bool
    image_id: str
    url: str
    thumbnail_url: Optional[str] = None


class InsertImageResponse(BaseModel):
    """插入图片响应"""
    success: bool
    element_id: str
    modification_id: str


class ImageAnalysisResponse(BaseModel):
    """图片分析响应"""
    tags: List[str]
    description: str
    colors: List[Dict[str, Any]]
    category: str
    objects: Optional[List[str]] = None


class ImageDetailResponse(ImageInfo):
    """图片详情响应"""
    ai_tags: Optional[List[str]] = None
    ai_description: Optional[str] = None
    color_palette: Optional[List[str]] = None
    use_count: int = 0
    created_at: datetime
