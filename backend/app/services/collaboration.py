"""
协作编辑服务
"""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.collaboration import (
    CollaborationSession, Collaborator, CollaborationActivity,
    Comment, CursorPosition, EditLock,
    CollaboratorRole, InviteStatus
)
from app.models import RefinementTask


class CollaborationService:
    """协作编辑服务"""
    
    # 用户颜色列表
    USER_COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
        "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
        "#BB8FCE", "#85C1E9", "#F8B500", "#00CED1",
    ]
    
    def __init__(self, db: Session):
        self.db = db
    
    def enable_collaboration(
        self,
        task_id: str,
        user_id: str,
        allow_anonymous_view: bool = False,
        allow_comments: bool = True,
    ) -> CollaborationSession:
        """
        启用协作功能
        
        Args:
            task_id: 任务ID
            user_id: 用户ID（必须是任务所有者）
            allow_anonymous_view: 允许匿名查看
            allow_comments: 允许评论
        
        Returns:
            协作会话
        """
        # 验证任务归属
        task = self.db.query(RefinementTask).filter(
            RefinementTask.id == task_id,
            RefinementTask.owner_id == user_id
        ).first()
        
        if not task:
            raise ValueError("任务不存在或无权操作")
        
        # 检查是否已存在协作会话
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.task_id == task_id
        ).first()
        
        if session:
            # 更新设置
            session.is_enabled = True
            session.allow_anonymous_view = allow_anonymous_view
            session.allow_comments = allow_comments
        else:
            # 创建新会话
            session = CollaborationSession(
                task_id=task_id,
                is_enabled=True,
                allow_anonymous_view=allow_anonymous_view,
                allow_comments=allow_comments,
            )
            self.db.add(session)
            self.db.flush()
            
            # 添加所有者作为协作者
            owner_collaborator = Collaborator(
                session_id=session.id,
                user_id=user_id,
                role=CollaboratorRole.OWNER,
                invite_status=InviteStatus.ACCEPTED,
                accepted_at=datetime.utcnow(),
            )
            self.db.add(owner_collaborator)
        
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def disable_collaboration(self, task_id: str, user_id: str) -> bool:
        """禁用协作功能"""
        session = self.db.query(CollaborationSession).join(
            RefinementTask
        ).filter(
            CollaborationSession.task_id == task_id,
            RefinementTask.owner_id == user_id
        ).first()
        
        if not session:
            return False
        
        session.is_enabled = False
        self.db.commit()
        return True
    
    def generate_share_link(
        self,
        task_id: str,
        user_id: str,
        expires_in_hours: int = 24 * 7,  # 默认7天
    ) -> str:
        """生成分享链接"""
        session = self._get_session_for_owner(task_id, user_id)
        if not session:
            raise ValueError("协作会话不存在")
        
        # 生成唯一链接
        share_code = secrets.token_urlsafe(16)
        session.share_link = share_code
        session.share_link_expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
        
        self.db.commit()
        
        return share_code
    
    def invite_collaborator(
        self,
        task_id: str,
        inviter_id: str,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        role: str = "viewer",
    ) -> Collaborator:
        """
        邀请协作者
        
        Args:
            task_id: 任务ID
            inviter_id: 邀请者ID
            user_id: 被邀请者用户ID（如果已注册）
            email: 被邀请者邮箱（如果未注册）
            role: 角色
        
        Returns:
            协作者记录
        """
        session = self._get_session_for_editor(task_id, inviter_id)
        if not session:
            raise ValueError("无权邀请协作者")
        
        # 解析角色
        try:
            role_enum = CollaboratorRole(role)
        except ValueError:
            role_enum = CollaboratorRole.VIEWER
        
        # 检查是否已邀请
        existing = None
        if user_id:
            existing = self.db.query(Collaborator).filter(
                Collaborator.session_id == session.id,
                Collaborator.user_id == user_id
            ).first()
        elif email:
            existing = self.db.query(Collaborator).filter(
                Collaborator.session_id == session.id,
                Collaborator.invite_email == email
            ).first()
        
        if existing:
            # 更新角色
            existing.role = role_enum
            self.db.commit()
            return existing
        
        # 分配颜色
        used_colors = self.db.query(CursorPosition.user_color).join(
            Collaborator
        ).filter(
            Collaborator.session_id == session.id
        ).all()
        used_colors = {c[0] for c in used_colors if c[0]}
        
        available_colors = [c for c in self.USER_COLORS if c not in used_colors]
        user_color = available_colors[0] if available_colors else self.USER_COLORS[0]
        
        # 创建协作者
        collaborator = Collaborator(
            session_id=session.id,
            user_id=user_id or str(uuid.uuid4()),  # 临时ID
            role=role_enum,
            invite_status=InviteStatus.PENDING,
            invited_by=inviter_id,
            invite_email=email,
        )
        self.db.add(collaborator)
        
        # 创建光标位置记录
        cursor = CursorPosition(
            collaborator_id=collaborator.id,
            user_color=user_color,
        )
        self.db.add(cursor)
        
        # 记录活动
        self._record_activity(
            session.id, inviter_id, "invite",
            {"invited_user": user_id or email, "role": role}
        )
        
        self.db.commit()
        self.db.refresh(collaborator)
        
        return collaborator
    
    def accept_invite(self, collaborator_id: str, user_id: str) -> bool:
        """接受邀请"""
        collaborator = self.db.query(Collaborator).filter(
            Collaborator.id == collaborator_id,
            Collaborator.user_id == user_id,
            Collaborator.invite_status == InviteStatus.PENDING
        ).first()
        
        if not collaborator:
            return False
        
        collaborator.invite_status = InviteStatus.ACCEPTED
        collaborator.accepted_at = datetime.utcnow()
        
        self._record_activity(
            collaborator.session_id, user_id, "join", {}
        )
        
        self.db.commit()
        return True
    
    def remove_collaborator(
        self,
        task_id: str,
        remover_id: str,
        collaborator_id: str,
    ) -> bool:
        """移除协作者"""
        session = self._get_session_for_owner(task_id, remover_id)
        if not session:
            raise ValueError("无权移除协作者")
        
        collaborator = self.db.query(Collaborator).filter(
            Collaborator.id == collaborator_id,
            Collaborator.session_id == session.id,
            Collaborator.role != CollaboratorRole.OWNER  # 不能移除所有者
        ).first()
        
        if not collaborator:
            return False
        
        self.db.delete(collaborator)
        self.db.commit()
        return True
    
    def update_collaborator_role(
        self,
        task_id: str,
        updater_id: str,
        collaborator_id: str,
        new_role: str,
    ) -> Optional[Collaborator]:
        """更新协作者角色"""
        session = self._get_session_for_owner(task_id, updater_id)
        if not session:
            raise ValueError("无权修改角色")
        
        try:
            role_enum = CollaboratorRole(new_role)
        except ValueError:
            raise ValueError("无效的角色")
        
        collaborator = self.db.query(Collaborator).filter(
            Collaborator.id == collaborator_id,
            Collaborator.session_id == session.id,
            Collaborator.role != CollaboratorRole.OWNER  # 不能修改所有者角色
        ).first()
        
        if not collaborator:
            return None
        
        collaborator.role = role_enum
        self.db.commit()
        self.db.refresh(collaborator)
        
        return collaborator
    
    def get_collaborators(
        self,
        task_id: str,
        user_id: str,
    ) -> List[Collaborator]:
        """获取协作者列表"""
        session = self._get_session_for_viewer(task_id, user_id)
        if not session:
            return []
        
        return self.db.query(Collaborator).filter(
            Collaborator.session_id == session.id,
            Collaborator.invite_status == InviteStatus.ACCEPTED
        ).all()
    
    def create_comment(
        self,
        task_id: str,
        user_id: str,
        content: str,
        page_index: Optional[int] = None,
        element_id: Optional[str] = None,
        position: Optional[Dict[str, float]] = None,
        parent_id: Optional[str] = None,
    ) -> Comment:
        """创建评论"""
        session = self._get_session_for_commenter(task_id, user_id)
        if not session:
            raise ValueError("无权评论")
        
        comment = Comment(
            session_id=session.id,
            user_id=user_id,
            content=content,
            page_index=page_index,
            element_id=element_id,
            position=position,
            parent_id=parent_id,
        )
        
        self.db.add(comment)
        
        self._record_activity(
            session.id, user_id, "comment",
            {"page_index": page_index, "element_id": element_id}
        )
        
        self.db.commit()
        self.db.refresh(comment)
        
        return comment
    
    def get_comments(
        self,
        task_id: str,
        user_id: str,
        page_index: Optional[int] = None,
        include_resolved: bool = False,
    ) -> List[Comment]:
        """获取评论列表"""
        session = self._get_session_for_viewer(task_id, user_id)
        if not session:
            return []
        
        query = self.db.query(Comment).filter(
            Comment.session_id == session.id,
            Comment.parent_id == None  # 只获取顶级评论
        )
        
        if page_index is not None:
            query = query.filter(Comment.page_index == page_index)
        
        if not include_resolved:
            query = query.filter(Comment.is_resolved == False)
        
        return query.order_by(Comment.created_at.desc()).all()
    
    def resolve_comment(
        self,
        comment_id: str,
        user_id: str,
        is_resolved: bool = True,
    ) -> Optional[Comment]:
        """解决/重开评论"""
        comment = self.db.query(Comment).filter(
            Comment.id == comment_id
        ).first()
        
        if not comment:
            return None
        
        # 验证权限
        session = self._get_session_for_editor(comment.session.task_id, user_id)
        if not session:
            raise ValueError("无权操作")
        
        comment.is_resolved = is_resolved
        if is_resolved:
            comment.resolved_by = user_id
            comment.resolved_at = datetime.utcnow()
        else:
            comment.resolved_by = None
            comment.resolved_at = None
        
        self.db.commit()
        self.db.refresh(comment)
        
        return comment
    
    def acquire_lock(
        self,
        task_id: str,
        user_id: str,
        page_index: int,
        element_id: str,
        duration_seconds: int = 60,
    ) -> Optional[EditLock]:
        """获取编辑锁"""
        session = self._get_session_for_editor(task_id, user_id)
        if not session:
            raise ValueError("无权编辑")
        
        # 检查是否已被锁定
        existing_lock = self.db.query(EditLock).filter(
            EditLock.session_id == session.id,
            EditLock.page_index == page_index,
            EditLock.element_id == element_id,
            EditLock.expires_at > datetime.utcnow()
        ).first()
        
        if existing_lock:
            if existing_lock.locked_by == user_id:
                # 续期
                existing_lock.expires_at = datetime.utcnow() + timedelta(seconds=duration_seconds)
                self.db.commit()
                return existing_lock
            else:
                # 被他人锁定
                return None
        
        # 创建新锁
        lock = EditLock(
            session_id=session.id,
            page_index=page_index,
            element_id=element_id,
            locked_by=user_id,
            expires_at=datetime.utcnow() + timedelta(seconds=duration_seconds),
        )
        
        self.db.add(lock)
        self.db.commit()
        self.db.refresh(lock)
        
        return lock
    
    def release_lock(
        self,
        task_id: str,
        user_id: str,
        page_index: int,
        element_id: str,
    ) -> bool:
        """释放编辑锁"""
        session = self._get_session_for_editor(task_id, user_id)
        if not session:
            return False
        
        lock = self.db.query(EditLock).filter(
            EditLock.session_id == session.id,
            EditLock.page_index == page_index,
            EditLock.element_id == element_id,
            EditLock.locked_by == user_id
        ).first()
        
        if not lock:
            return False
        
        self.db.delete(lock)
        self.db.commit()
        return True
    
    def update_cursor_position(
        self,
        task_id: str,
        user_id: str,
        page_index: Optional[int] = None,
        cursor_x: Optional[int] = None,
        cursor_y: Optional[int] = None,
        selected_element_id: Optional[str] = None,
    ) -> Optional[CursorPosition]:
        """更新光标位置"""
        session = self._get_session_for_viewer(task_id, user_id)
        if not session:
            return None
        
        collaborator = self.db.query(Collaborator).filter(
            Collaborator.session_id == session.id,
            Collaborator.user_id == user_id
        ).first()
        
        if not collaborator:
            return None
        
        cursor = self.db.query(CursorPosition).filter(
            CursorPosition.collaborator_id == collaborator.id
        ).first()
        
        if not cursor:
            cursor = CursorPosition(
                collaborator_id=collaborator.id,
                user_color=self.USER_COLORS[0],
            )
            self.db.add(cursor)
        
        if page_index is not None:
            cursor.page_index = page_index
        if cursor_x is not None:
            cursor.cursor_x = cursor_x
        if cursor_y is not None:
            cursor.cursor_y = cursor_y
        if selected_element_id is not None:
            cursor.selected_element_id = selected_element_id
        
        # 更新活跃时间
        collaborator.last_active_at = datetime.utcnow()
        collaborator.is_online = True
        
        self.db.commit()
        self.db.refresh(cursor)
        
        return cursor
    
    def get_online_cursors(
        self,
        task_id: str,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """获取所有在线用户的光标位置"""
        session = self._get_session_for_viewer(task_id, user_id)
        if not session:
            return []
        
        # 获取最近5分钟活跃的用户
        active_threshold = datetime.utcnow() - timedelta(minutes=5)
        
        cursors = self.db.query(CursorPosition).join(
            Collaborator
        ).filter(
            Collaborator.session_id == session.id,
            Collaborator.last_active_at > active_threshold,
            Collaborator.user_id != user_id  # 排除自己
        ).all()
        
        return [
            {
                "user_id": c.collaborator.user_id,
                "user_color": c.user_color,
                "page_index": c.page_index,
                "cursor_x": c.cursor_x,
                "cursor_y": c.cursor_y,
                "selected_element_id": c.selected_element_id,
            }
            for c in cursors
        ]
    
    def _get_session_for_owner(
        self,
        task_id: str,
        user_id: str,
    ) -> Optional[CollaborationSession]:
        """获取会话（需要所有者权限）"""
        return self.db.query(CollaborationSession).join(
            RefinementTask
        ).filter(
            CollaborationSession.task_id == task_id,
            RefinementTask.owner_id == user_id
        ).first()
    
    def _get_session_for_editor(
        self,
        task_id: str,
        user_id: str,
    ) -> Optional[CollaborationSession]:
        """获取会话（需要编辑权限）"""
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.task_id == task_id,
            CollaborationSession.is_enabled == True
        ).first()
        
        if not session:
            return None
        
        collaborator = self.db.query(Collaborator).filter(
            Collaborator.session_id == session.id,
            Collaborator.user_id == user_id,
            Collaborator.invite_status == InviteStatus.ACCEPTED,
            Collaborator.role.in_([CollaboratorRole.OWNER, CollaboratorRole.EDITOR])
        ).first()
        
        return session if collaborator else None
    
    def _get_session_for_commenter(
        self,
        task_id: str,
        user_id: str,
    ) -> Optional[CollaborationSession]:
        """获取会话（需要评论权限）"""
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.task_id == task_id,
            CollaborationSession.is_enabled == True,
            CollaborationSession.allow_comments == True
        ).first()
        
        if not session:
            return None
        
        collaborator = self.db.query(Collaborator).filter(
            Collaborator.session_id == session.id,
            Collaborator.user_id == user_id,
            Collaborator.invite_status == InviteStatus.ACCEPTED
        ).first()
        
        return session if collaborator else None
    
    def _get_session_for_viewer(
        self,
        task_id: str,
        user_id: str,
    ) -> Optional[CollaborationSession]:
        """获取会话（需要查看权限）"""
        session = self.db.query(CollaborationSession).filter(
            CollaborationSession.task_id == task_id,
            CollaborationSession.is_enabled == True
        ).first()
        
        if not session:
            return None
        
        # 检查是否是协作者
        collaborator = self.db.query(Collaborator).filter(
            Collaborator.session_id == session.id,
            Collaborator.user_id == user_id,
            Collaborator.invite_status == InviteStatus.ACCEPTED
        ).first()
        
        # 或者允许匿名查看
        if collaborator or session.allow_anonymous_view:
            return session
        
        return None
    
    def _record_activity(
        self,
        session_id: str,
        user_id: str,
        activity_type: str,
        details: Dict[str, Any],
        page_index: Optional[int] = None,
        element_id: Optional[str] = None,
    ):
        """记录活动"""
        activity = CollaborationActivity(
            session_id=session_id,
            user_id=user_id,
            activity_type=activity_type,
            details=details,
            page_index=page_index,
            element_id=element_id,
        )
        self.db.add(activity)
