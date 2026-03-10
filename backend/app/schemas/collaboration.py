"""
协作编辑 Schema
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ 基础模型 ============

class CollaboratorInfo(BaseModel):
    """协作者信息"""
    id: str
    user_id: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    invite_status: str
    is_online: bool = False
    last_active_at: Optional[datetime] = None
    user_color: Optional[str] = None
    
    class Config:
        from_attributes = True


class CursorInfo(BaseModel):
    """光标信息"""
    user_id: str
    username: str
    user_color: str
    page_index: Optional[int] = None
    cursor_x: Optional[int] = None
    cursor_y: Optional[int] = None
    selected_element_id: Optional[str] = None


class CommentInfo(BaseModel):
    """评论信息"""
    id: str
    user_id: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    content: str
    page_index: Optional[int] = None
    element_id: Optional[str] = None
    position: Optional[Dict[str, float]] = None
    is_resolved: bool = False
    created_at: datetime
    replies: Optional[List["CommentInfo"]] = None
    
    class Config:
        from_attributes = True


# ============ 请求模型 ============

class EnableCollaborationRequest(BaseModel):
    """启用协作请求"""
    allow_anonymous_view: bool = Field(False, description="允许匿名查看")
    allow_comments: bool = Field(True, description="允许评论")


class InviteCollaboratorRequest(BaseModel):
    """邀请协作者请求"""
    user_id: Optional[str] = Field(None, description="用户ID（如果已注册）")
    email: Optional[str] = Field(None, description="邮箱（如果未注册）")
    role: str = Field("viewer", description="角色: owner, editor, viewer, commenter")


class UpdateCollaboratorRoleRequest(BaseModel):
    """更新协作者角色请求"""
    role: str = Field(..., description="新角色")


class CreateCommentRequest(BaseModel):
    """创建评论请求"""
    content: str = Field(..., min_length=1, max_length=2000, description="评论内容")
    page_index: Optional[int] = Field(None, description="页面索引")
    element_id: Optional[str] = Field(None, description="元素ID")
    position: Optional[Dict[str, float]] = Field(None, description="评论位置")
    parent_id: Optional[str] = Field(None, description="回复的评论ID")


class ResolveCommentRequest(BaseModel):
    """解决评论请求"""
    is_resolved: bool = Field(True, description="是否已解决")


class UpdateCursorRequest(BaseModel):
    """更新光标位置请求"""
    page_index: Optional[int] = None
    cursor_x: Optional[int] = None
    cursor_y: Optional[int] = None
    selected_element_id: Optional[str] = None


class AcquireLockRequest(BaseModel):
    """获取编辑锁请求"""
    page_index: int = Field(..., description="页面索引")
    element_id: str = Field(..., description="元素ID")
    duration: int = Field(60, description="锁定时长（秒）")


# ============ 响应模型 ============

class CollaborationSessionResponse(BaseModel):
    """协作会话响应"""
    id: str
    task_id: str
    is_enabled: bool
    share_link: Optional[str] = None
    share_link_expires_at: Optional[datetime] = None
    allow_anonymous_view: bool
    allow_comments: bool
    online_count: int
    collaborators: List[CollaboratorInfo] = []


class EnableCollaborationResponse(BaseModel):
    """启用协作响应"""
    success: bool
    session_id: str
    share_link: Optional[str] = None


class InviteCollaboratorResponse(BaseModel):
    """邀请协作者响应"""
    success: bool
    collaborator_id: str
    invite_status: str
    invite_link: Optional[str] = None


class CollaboratorListResponse(BaseModel):
    """协作者列表响应"""
    collaborators: List[CollaboratorInfo]
    total: int
    online_count: int


class CommentListResponse(BaseModel):
    """评论列表响应"""
    comments: List[CommentInfo]
    total: int
    unresolved_count: int


class CreateCommentResponse(BaseModel):
    """创建评论响应"""
    success: bool
    comment_id: str
    created_at: datetime


class CursorListResponse(BaseModel):
    """光标列表响应"""
    cursors: List[CursorInfo]


class AcquireLockResponse(BaseModel):
    """获取编辑锁响应"""
    success: bool
    lock_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    locked_by: Optional[str] = None  # 如果获取失败，返回当前锁定者


class ActivityInfo(BaseModel):
    """活动信息"""
    id: str
    user_id: str
    username: Optional[str] = None
    activity_type: str
    details: Optional[Dict[str, Any]] = None
    page_index: Optional[int] = None
    created_at: datetime


class ActivityListResponse(BaseModel):
    """活动列表响应"""
    activities: List[ActivityInfo]
    total: int


# ============ WebSocket 消息模型 ============

class WSMessage(BaseModel):
    """WebSocket 消息基类"""
    type: str
    payload: Dict[str, Any]


class WSJoinMessage(BaseModel):
    """加入协作消息"""
    type: str = "join"
    session_id: str
    user_id: str
    username: str
    user_color: str


class WSLeaveMessage(BaseModel):
    """离开协作消息"""
    type: str = "leave"
    user_id: str


class WSCursorUpdateMessage(BaseModel):
    """光标更新消息"""
    type: str = "cursor_update"
    user_id: str
    cursor: CursorInfo


class WSEditMessage(BaseModel):
    """编辑操作消息"""
    type: str = "edit"
    user_id: str
    page_index: int
    element_id: str
    operation: str
    data: Dict[str, Any]


class WSLockMessage(BaseModel):
    """锁定消息"""
    type: str = "lock"
    user_id: str
    page_index: int
    element_id: str
    action: str  # acquire, release


class WSCommentMessage(BaseModel):
    """评论消息"""
    type: str = "comment"
    action: str  # add, resolve, delete
    comment: CommentInfo
