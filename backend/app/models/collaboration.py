"""
协作编辑模型
支持多人实时协作编辑同一份 PPT
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum as SQLEnum, Boolean, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.models.base import BaseModel


class CollaboratorRole(str, enum.Enum):
    """协作者角色"""
    OWNER = "owner"         # 所有者
    EDITOR = "editor"       # 编辑者
    VIEWER = "viewer"       # 查看者
    COMMENTER = "commenter" # 评论者


class InviteStatus(str, enum.Enum):
    """邀请状态"""
    PENDING = "pending"     # 待接受
    ACCEPTED = "accepted"   # 已接受
    REJECTED = "rejected"   # 已拒绝
    EXPIRED = "expired"     # 已过期


class CollaborationSession(BaseModel):
    """协作会话表 - 记录协作任务的元信息"""
    __tablename__ = "collaboration_sessions"
    
    # 关联的精修任务
    task_id = Column(String(36), ForeignKey("refinement_tasks.id"), nullable=False, index=True, unique=True)
    task = relationship("RefinementTask", backref="collaboration_session")
    
    # 是否启用协作
    is_enabled = Column(Boolean, default=False, nullable=False)
    
    # 分享链接（可选）
    share_link = Column(String(100), nullable=True, unique=True)
    share_link_expires_at = Column(DateTime, nullable=True)
    
    # 协作设置
    allow_anonymous_view = Column(Boolean, default=False, nullable=False)
    allow_comments = Column(Boolean, default=True, nullable=False)
    
    # 在线人数
    online_count = Column(Integer, default=0, nullable=False)


class Collaborator(BaseModel):
    """协作者表"""
    __tablename__ = "collaborators"
    
    # 关联的协作会话
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    session = relationship("CollaborationSession", backref="collaborators")
    
    # 用户
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", foreign_keys=[user_id], backref="collaborations")
    
    # 角色
    role = Column(
        SQLEnum(CollaboratorRole),
        default=CollaboratorRole.VIEWER,
        nullable=False
    )
    
    # 状态
    invite_status = Column(
        SQLEnum(InviteStatus),
        default=InviteStatus.PENDING,
        nullable=False
    )
    
    # 邀请信息
    invited_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    invited_by_user = relationship("User", foreign_keys=[invited_by])
    invited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    
    # 邀请邮箱（如果用户未注册）
    invite_email = Column(String(255), nullable=True)
    
    # 最后活跃时间
    last_active_at = Column(DateTime, nullable=True)
    
    # 当前是否在线
    is_online = Column(Boolean, default=False, nullable=False)


class CollaborationActivity(BaseModel):
    """协作活动记录表 - 记录协作中的操作"""
    __tablename__ = "collaboration_activities"
    
    # 关联的协作会话
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    session = relationship("CollaborationSession", backref="activities")
    
    # 操作者
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User")
    
    # 操作类型
    activity_type = Column(String(50), nullable=False)  # edit, comment, view, join, leave
    
    # 操作详情
    details = Column(JSON, nullable=True)
    
    # 影响的页面
    page_index = Column(Integer, nullable=True)
    
    # 影响的元素
    element_id = Column(String(100), nullable=True)


class Comment(BaseModel):
    """评论表"""
    __tablename__ = "collaboration_comments"
    
    # 关联的协作会话
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    session = relationship("CollaborationSession", backref="comments")
    
    # 评论者
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", foreign_keys=[user_id])
    
    # 评论位置
    page_index = Column(Integer, nullable=True)
    element_id = Column(String(100), nullable=True)
    position = Column(JSON, nullable=True)  # {x, y} 评论锚点位置
    
    # 评论内容
    content = Column(Text, nullable=False)
    
    # 回复的评论（如果是回复）
    parent_id = Column(String(36), ForeignKey("collaboration_comments.id"), nullable=True)
    replies = relationship("Comment", backref="parent", remote_side="[Comment.id]")
    
    # 是否已解决
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_by_user = relationship("User", foreign_keys=[resolved_by])
    resolved_at = Column(DateTime, nullable=True)


class CursorPosition(BaseModel):
    """光标位置表 - 记录协作者的实时光标位置"""
    __tablename__ = "cursor_positions"
    
    # 协作者
    collaborator_id = Column(String(36), ForeignKey("collaborators.id"), nullable=False, index=True)
    collaborator = relationship("Collaborator", backref="cursor_position")
    
    # 当前页面
    page_index = Column(Integer, nullable=True)
    
    # 选中的元素
    selected_element_id = Column(String(100), nullable=True)
    
    # 光标位置
    cursor_x = Column(Integer, nullable=True)
    cursor_y = Column(Integer, nullable=True)
    
    # 用户颜色（用于显示不同协作者）
    user_color = Column(String(20), nullable=True)


class EditLock(BaseModel):
    """编辑锁表 - 防止同时编辑同一元素"""
    __tablename__ = "edit_locks"
    
    # 关联的协作会话
    session_id = Column(String(36), ForeignKey("collaboration_sessions.id"), nullable=False, index=True)
    session = relationship("CollaborationSession", backref="edit_locks")
    
    # 锁定的元素
    page_index = Column(Integer, nullable=False)
    element_id = Column(String(100), nullable=False)
    
    # 锁定者
    locked_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    locker = relationship("User", foreign_keys=[locked_by])
    
    # 锁定时间
    locked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)  # 锁自动过期时间
