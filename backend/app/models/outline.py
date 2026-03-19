"""
大纲模型
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, SoftDeleteMixin


class OutlineStatus(str, enum.Enum):
    """大纲状态"""
    DRAFT = "draft"          # 草稿
    COMPLETED = "completed"  # 已完成


class OutlineGenerationMode(str, enum.Enum):
    """大纲生成方式"""
    INTELLIGENT = "intelligent"  # 智能生成
    WIZARD = "wizard"            # 向导式生成
    MANUAL = "manual"            # 手动创建


class Outline(BaseModel, SoftDeleteMixin):
    """大纲表"""
    __tablename__ = "outlines"
    
    # 基本信息
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 生成方式
    generation_mode = Column(
        SQLEnum(OutlineGenerationMode),
        default=OutlineGenerationMode.MANUAL,
        nullable=False
    )
    
    # 生成配置（智能生成时的参数）
    generation_config = Column(JSON, nullable=True)
    
    # 状态
    status = Column(
        SQLEnum(OutlineStatus),
        default=OutlineStatus.DRAFT,
        nullable=False
    )
    
    # 章节数量统计
    section_count = Column(Integer, default=0, nullable=False)
    
    # 所属用户
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="outlines")
    
    # 关联章节
    sections = relationship(
        "OutlineSection",
        back_populates="outline",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="OutlineSection.order_index"
    )
    
    # 关联草稿
    drafts = relationship("Draft", back_populates="outline", lazy="dynamic")


class OutlineSection(BaseModel):
    """大纲章节表"""
    __tablename__ = "outline_sections"
    
    # 所属大纲
    outline_id = Column(String(36), ForeignKey("outlines.id"), nullable=False, index=True)
    outline = relationship("Outline", back_populates="sections")
    
    # 父章节（支持多级结构）
    parent_id = Column(String(36), ForeignKey("outline_sections.id"), nullable=True, index=True)
    parent = relationship("OutlineSection", remote_side="OutlineSection.id", backref="children")
    
    # 章节信息
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content_hint = Column(Text, nullable=True)  # 内容提示/关键点
    
    # 排序
    order_index = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)  # 层级深度
    
    # 期望页数
    expected_pages = Column(Integer, default=1, nullable=False)
    
    # 是否已完成页面选择
    is_page_selected = Column(Boolean, default=False, nullable=False)
