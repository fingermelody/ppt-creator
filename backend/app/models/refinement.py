"""
PPT 精修模型
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, SoftDeleteMixin


class RefinementStatus(str, enum.Enum):
    """精修任务状态"""
    ACTIVE = "active"        # 进行中
    SAVED = "saved"          # 已保存
    EXPORTED = "exported"    # 已导出


class ModificationAction(str, enum.Enum):
    """修改操作类型"""
    EDIT_TEXT = "edit_text"
    EDIT_STYLE = "edit_style"
    EDIT_TABLE = "edit_table"
    REPLACE_IMAGE = "replace_image"
    MOVE = "move"
    RESIZE = "resize"
    DELETE = "delete"
    ADD = "add"
    DUPLICATE = "duplicate"
    CHANGE_ORDER = "change_order"


class RefinementTask(BaseModel, SoftDeleteMixin):
    """精修任务表"""
    __tablename__ = "refinement_tasks"
    
    # 基本信息
    title = Column(String(255), nullable=True)
    
    # 来源草稿
    draft_id = Column(String(36), ForeignKey("drafts.id"), nullable=False, index=True)
    draft = relationship("Draft", back_populates="refinement_tasks")
    
    # 状态
    status = Column(
        SQLEnum(RefinementStatus),
        default=RefinementStatus.ACTIVE,
        nullable=False
    )
    
    # 页面数量
    total_pages = Column(Integer, default=0, nullable=False)
    
    # 当前版本
    version = Column(String(50), default="v1", nullable=False)
    
    # 导出信息
    exported_file_path = Column(String(500), nullable=True)
    
    # 所属用户
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="refinement_tasks")
    
    # 关联页面
    pages = relationship(
        "RefinedPage",
        back_populates="task",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="RefinedPage.page_index"
    )


class RefinedPage(BaseModel):
    """精修页面表"""
    __tablename__ = "refined_pages"
    
    # 所属任务
    task_id = Column(String(36), ForeignKey("refinement_tasks.id"), nullable=False, index=True)
    task = relationship("RefinementTask", back_populates="pages")
    
    # 页面信息
    page_index = Column(Integer, nullable=False)
    title = Column(String(500), nullable=True)
    
    # 关联章节（从草稿页面继承）
    section_id = Column(String(36), ForeignKey("outline_sections.id"), nullable=True, index=True)
    section = relationship("OutlineSection")
    
    # 页面内容（当前状态）
    content = Column(JSON, nullable=True)
    elements = Column(JSON, nullable=True)
    
    # 缩略图
    thumbnail_path = Column(String(500), nullable=True)
    
    # 修改历史
    modifications = relationship(
        "PageModification",
        back_populates="page",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="PageModification.created_at"
    )
    
    # 对话历史
    conversations = relationship(
        "RefinementConversation",
        back_populates="page",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    
    # 撤销/重做状态
    history_step = Column(Integer, default=0, nullable=False)  # 当前历史步骤
    total_history_steps = Column(Integer, default=0, nullable=False)  # 总历史步骤数


class PageModification(BaseModel):
    """页面修改记录表"""
    __tablename__ = "page_modifications"
    
    # 所属页面
    page_id = Column(String(36), ForeignKey("refined_pages.id"), nullable=False, index=True)
    page = relationship("RefinedPage", back_populates="modifications")
    
    # 修改信息
    action = Column(
        SQLEnum(ModificationAction),
        nullable=False
    )
    element_id = Column(String(100), nullable=True)
    
    # 修改前后状态（用于撤销/重做）
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    
    # 历史步骤索引
    step_index = Column(Integer, nullable=False)
    
    # 描述
    description = Column(Text, nullable=True)


class RefinementConversation(BaseModel):
    """精修对话表"""
    __tablename__ = "refinement_conversations"
    
    # 所属页面
    page_id = Column(String(36), ForeignKey("refined_pages.id"), nullable=False, index=True)
    page = relationship("RefinedPage", back_populates="conversations")
    
    # 对话信息
    conversation_id = Column(String(100), nullable=False, index=True)
    
    # 关联消息
    messages = relationship(
        "RefinementMessage",
        back_populates="conversation",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="RefinementMessage.created_at"
    )


class RefinementMessage(BaseModel):
    """精修对话消息表"""
    __tablename__ = "refinement_messages"
    
    # 所属对话
    conversation_id = Column(String(36), ForeignKey("refinement_conversations.id"), nullable=False, index=True)
    conversation = relationship("RefinementConversation", back_populates="messages")
    
    # 消息信息
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    
    # 上下文信息
    selected_element = Column(String(100), nullable=True)
    
    # 关联的修改
    modification_id = Column(String(36), ForeignKey("page_modifications.id"), nullable=True)
    modification = relationship("PageModification")
