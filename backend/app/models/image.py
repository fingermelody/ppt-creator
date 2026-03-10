"""
智能图片推荐模型
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class ImageSource(str, enum.Enum):
    """图片来源"""
    UNSPLASH = "unsplash"
    PEXELS = "pexels"
    PIXABAY = "pixabay"
    UPLOAD = "upload"
    AI_GENERATED = "ai_generated"


class ImageCategory(str, enum.Enum):
    """图片分类"""
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    NATURE = "nature"
    PEOPLE = "people"
    ABSTRACT = "abstract"
    FOOD = "food"
    TRAVEL = "travel"
    EDUCATION = "education"
    OTHER = "other"


class ImageRecommendation(BaseModel):
    """图片推荐记录表"""
    __tablename__ = "image_recommendations"
    
    # 关联的页面
    page_id = Column(String(36), ForeignKey("refined_pages.id"), nullable=False, index=True)
    
    # 用户
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # 推荐的图片列表
    images = Column(JSON, nullable=True)  # 包含图片URL、描述、关键词等
    
    # 搜索关键词
    search_keywords = Column(JSON, nullable=True)
    
    # 内容上下文
    content_context = Column(Text, nullable=True)


class ImageLibrary(BaseModel):
    """图片库表 - 用户上传或收藏的图片"""
    __tablename__ = "image_library"
    
    # 用户
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", backref="images")
    
    # 图片信息
    url = Column(String(1000), nullable=False)
    thumbnail_url = Column(String(1000), nullable=True)
    
    # 来源
    source = Column(
        SQLEnum(ImageSource),
        default=ImageSource.UPLOAD,
        nullable=False
    )
    source_id = Column(String(100), nullable=True)  # 原图片ID（如果是外部来源）
    
    # 分类
    category = Column(
        SQLEnum(ImageCategory),
        default=ImageCategory.OTHER,
        nullable=False
    )
    
    # 描述信息
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    alt_text = Column(String(500), nullable=True)
    
    # 标签
    tags = Column(JSON, nullable=True)
    
    # 尺寸
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # AI 分析结果
    ai_tags = Column(JSON, nullable=True)  # AI 生成的标签
    ai_description = Column(Text, nullable=True)  # AI 生成的描述
    color_palette = Column(JSON, nullable=True)  # 主色调
    
    # 使用统计
    use_count = Column(Integer, default=0, nullable=False)


class ImageUsage(BaseModel):
    """图片使用记录表"""
    __tablename__ = "image_usages"
    
    # 图片
    image_id = Column(String(36), ForeignKey("image_library.id"), nullable=True)
    image_url = Column(String(1000), nullable=True)  # 外部图片直接存URL
    
    # 使用位置
    page_id = Column(String(36), ForeignKey("refined_pages.id"), nullable=False, index=True)
    element_id = Column(String(100), nullable=True)
    
    # 用户
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
