"""
文档和页面模型
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, SoftDeleteMixin


class DocumentStatus(str, enum.Enum):
    """文档处理状态"""
    UPLOADING = "uploading"      # 上传中
    PARSING = "parsing"          # 解析中
    VECTORIZING = "vectorizing"  # 向量化中
    READY = "ready"              # 就绪
    ERROR = "error"              # 错误


class Document(BaseModel, SoftDeleteMixin):
    """文档表"""
    __tablename__ = "documents"
    
    # 基本信息
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # 文档元数据
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    page_count = Column(Integer, default=0, nullable=False)
    
    # 处理状态
    status = Column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.UPLOADING,
        nullable=False
    )
    error_message = Column(Text, nullable=True)
    
    # 所属用户
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="documents")
    
    # 关联页面
    slides = relationship(
        "Slide",
        back_populates="document",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )


class Slide(BaseModel):
    """页面表"""
    __tablename__ = "slides"
    
    # 所属文档
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    document = relationship("Document", back_populates="slides")
    
    # 页面信息
    page_number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=True)
    content_text = Column(Text, nullable=True)  # 纯文本内容（用于搜索和向量化）
    
    # 布局和元素
    layout_type = Column(String(50), nullable=True)
    elements = Column(JSON, nullable=True)  # 元素详情
    
    # 缩略图
    thumbnail_path = Column(String(500), nullable=True)
    
    # 向量ID（存储在 ChromaDB 中）
    vector_id = Column(String(100), nullable=True, index=True)
    
    # 附加数据
    extra_data = Column(JSON, nullable=True)
