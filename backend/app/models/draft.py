"""
草稿模型
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, SoftDeleteMixin


class DraftStatus(str, enum.Enum):
    """草稿状态"""
    ASSEMBLING = "assembling"  # 组装中
    COMPLETED = "completed"    # 已完成
    EXPORTED = "exported"      # 已导出


class Draft(BaseModel, SoftDeleteMixin):
    """草稿表"""
    __tablename__ = "drafts"
    
    # 基本信息
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 关联大纲（可选）
    outline_id = Column(String(36), ForeignKey("outlines.id"), nullable=True, index=True)
    outline = relationship("Outline", back_populates="drafts")
    
    # 状态
    status = Column(
        SQLEnum(DraftStatus),
        default=DraftStatus.ASSEMBLING,
        nullable=False
    )
    
    # 页面数量
    page_count = Column(Integer, default=0, nullable=False)
    
    # 导出信息
    exported_file_path = Column(String(500), nullable=True)
    
    # 所属用户
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="drafts")
    
    # 关联页面
    pages = relationship(
        "DraftPage",
        back_populates="draft",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="DraftPage.order_index"
    )
    
    # 精修任务
    refinement_tasks = relationship("RefinementTask", back_populates="draft", lazy="dynamic")


class DraftPage(BaseModel):
    """草稿页面表"""
    __tablename__ = "draft_pages"
    
    # 所属草稿
    draft_id = Column(String(36), ForeignKey("drafts.id"), nullable=False, index=True)
    draft = relationship("Draft", back_populates="pages")
    
    # 来源页面（从文档库复制）
    source_slide_id = Column(String(36), ForeignKey("slides.id"), nullable=True, index=True)
    source_slide = relationship("Slide")
    
    # 关联章节
    section_id = Column(String(36), ForeignKey("outline_sections.id"), nullable=True, index=True)
    section = relationship("OutlineSection")
    
    # 页面信息
    title = Column(String(500), nullable=True)
    order_index = Column(Integer, default=0, nullable=False)
    
    # 页面内容（复制后可能被修改）
    content = Column(JSON, nullable=True)
    
    # 缩略图
    thumbnail_path = Column(String(500), nullable=True)
    
    # 是否已修改
    is_modified = Column(Integer, default=0, nullable=False)  # 0=未修改, 1=已修改
