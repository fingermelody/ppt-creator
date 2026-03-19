"""
协作编辑 API
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.core import get_current_user_id
from app.services.collaboration import CollaborationService
from app.schemas.collaboration import (
    EnableCollaborationRequest, EnableCollaborationResponse,
    InviteCollaboratorRequest, InviteCollaboratorResponse,
    UpdateCollaboratorRoleRequest,
    CreateCommentRequest, CreateCommentResponse, ResolveCommentRequest,
    UpdateCursorRequest, AcquireLockRequest, AcquireLockResponse,
    CollaborationSessionResponse, CollaboratorListResponse, CollaboratorInfo,
    CommentListResponse, CommentInfo, CursorListResponse, CursorInfo,
    ActivityListResponse, ActivityInfo,
)

router = APIRouter()


@router.post("/tasks/{task_id}/collaboration/enable", 
             response_model=EnableCollaborationResponse, 
             summary="启用协作")
async def enable_collaboration(
    task_id: str,
    request: EnableCollaborationRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """启用任务的协作功能"""
    service = CollaborationService(db)
    
    try:
        session = service.enable_collaboration(
            task_id=task_id,
            user_id=user_id,
            allow_anonymous_view=request.allow_anonymous_view,
            allow_comments=request.allow_comments,
        )
        
        return EnableCollaborationResponse(
            success=True,
            session_id=session.id,
            share_link=session.share_link,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/collaboration/disable", summary="禁用协作")
async def disable_collaboration(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """禁用任务的协作功能"""
    service = CollaborationService(db)
    success = service.disable_collaboration(task_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="协作会话不存在")
    
    return {"success": True}


@router.get("/tasks/{task_id}/collaboration", 
            response_model=CollaborationSessionResponse, 
            summary="获取协作状态")
async def get_collaboration_status(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取协作会话状态"""
    from app.models.collaboration import CollaborationSession, InviteStatus
    
    session = db.query(CollaborationSession).filter(
        CollaborationSession.task_id == task_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="协作会话不存在")
    
    service = CollaborationService(db)
    collaborators = service.get_collaborators(task_id, user_id)
    
    return CollaborationSessionResponse(
        id=session.id,
        task_id=session.task_id,
        is_enabled=session.is_enabled,
        share_link=session.share_link,
        share_link_expires_at=session.share_link_expires_at,
        allow_anonymous_view=session.allow_anonymous_view,
        allow_comments=session.allow_comments,
        online_count=session.online_count,
        collaborators=[
            CollaboratorInfo(
                id=c.id,
                user_id=c.user_id,
                role=c.role.value,
                invite_status=c.invite_status.value,
                is_online=c.is_online,
                last_active_at=c.last_active_at,
            )
            for c in collaborators
        ],
    )


@router.post("/tasks/{task_id}/collaboration/share-link", summary="生成分享链接")
async def generate_share_link(
    task_id: str,
    expires_in_hours: int = Query(168, ge=1, le=720, description="过期时间（小时）"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """生成协作分享链接"""
    service = CollaborationService(db)
    
    try:
        share_code = service.generate_share_link(task_id, user_id, expires_in_hours)
        return {
            "success": True,
            "share_link": f"/collaborate/{share_code}",
            "share_code": share_code,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/collaboration/invite", 
             response_model=InviteCollaboratorResponse, 
             summary="邀请协作者")
async def invite_collaborator(
    task_id: str,
    request: InviteCollaboratorRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """邀请协作者"""
    if not request.user_id and not request.email:
        raise HTTPException(status_code=400, detail="必须提供用户ID或邮箱")
    
    service = CollaborationService(db)
    
    try:
        collaborator = service.invite_collaborator(
            task_id=task_id,
            inviter_id=user_id,
            user_id=request.user_id,
            email=request.email,
            role=request.role,
        )
        
        return InviteCollaboratorResponse(
            success=True,
            collaborator_id=collaborator.id,
            invite_status=collaborator.invite_status.value,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}/collaboration/collaborators", 
            response_model=CollaboratorListResponse, 
            summary="获取协作者列表")
async def get_collaborators(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取协作者列表"""
    service = CollaborationService(db)
    collaborators = service.get_collaborators(task_id, user_id)
    
    online_count = sum(1 for c in collaborators if c.is_online)
    
    return CollaboratorListResponse(
        collaborators=[
            CollaboratorInfo(
                id=c.id,
                user_id=c.user_id,
                role=c.role.value,
                invite_status=c.invite_status.value,
                is_online=c.is_online,
                last_active_at=c.last_active_at,
            )
            for c in collaborators
        ],
        total=len(collaborators),
        online_count=online_count,
    )


@router.delete("/tasks/{task_id}/collaboration/collaborators/{collaborator_id}", 
               summary="移除协作者")
async def remove_collaborator(
    task_id: str,
    collaborator_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """移除协作者"""
    service = CollaborationService(db)
    
    try:
        success = service.remove_collaborator(task_id, user_id, collaborator_id)
        if not success:
            raise HTTPException(status_code=404, detail="协作者不存在")
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/tasks/{task_id}/collaboration/collaborators/{collaborator_id}/role", 
            summary="更新协作者角色")
async def update_collaborator_role(
    task_id: str,
    collaborator_id: str,
    request: UpdateCollaboratorRoleRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新协作者角色"""
    service = CollaborationService(db)
    
    try:
        collaborator = service.update_collaborator_role(
            task_id, user_id, collaborator_id, request.role
        )
        if not collaborator:
            raise HTTPException(status_code=404, detail="协作者不存在")
        
        return {
            "success": True,
            "collaborator_id": collaborator.id,
            "new_role": collaborator.role.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ 评论相关 ============

@router.get("/tasks/{task_id}/collaboration/comments", 
            response_model=CommentListResponse, 
            summary="获取评论列表")
async def get_comments(
    task_id: str,
    page_index: Optional[int] = Query(None, description="页面索引筛选"),
    include_resolved: bool = Query(False, description="是否包含已解决的评论"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取评论列表"""
    service = CollaborationService(db)
    comments = service.get_comments(
        task_id, user_id, page_index, include_resolved
    )
    
    unresolved_count = sum(1 for c in comments if not c.is_resolved)
    
    return CommentListResponse(
        comments=[
            CommentInfo(
                id=c.id,
                user_id=c.user_id,
                content=c.content,
                page_index=c.page_index,
                element_id=c.element_id,
                position=c.position,
                is_resolved=c.is_resolved,
                created_at=c.created_at,
            )
            for c in comments
        ],
        total=len(comments),
        unresolved_count=unresolved_count,
    )


@router.post("/tasks/{task_id}/collaboration/comments", 
             response_model=CreateCommentResponse, 
             summary="创建评论")
async def create_comment(
    task_id: str,
    request: CreateCommentRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """创建评论"""
    service = CollaborationService(db)
    
    try:
        comment = service.create_comment(
            task_id=task_id,
            user_id=user_id,
            content=request.content,
            page_index=request.page_index,
            element_id=request.element_id,
            position=request.position,
            parent_id=request.parent_id,
        )
        
        return CreateCommentResponse(
            success=True,
            comment_id=comment.id,
            created_at=comment.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/tasks/{task_id}/collaboration/comments/{comment_id}/resolve", 
            summary="解决评论")
async def resolve_comment(
    task_id: str,
    comment_id: str,
    request: ResolveCommentRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """解决或重开评论"""
    service = CollaborationService(db)
    
    try:
        comment = service.resolve_comment(comment_id, user_id, request.is_resolved)
        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")
        
        return {
            "success": True,
            "is_resolved": comment.is_resolved,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ 光标和锁 ============

@router.get("/tasks/{task_id}/collaboration/cursors", 
            response_model=CursorListResponse, 
            summary="获取在线用户光标")
async def get_cursors(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取所有在线用户的光标位置"""
    service = CollaborationService(db)
    cursors = service.get_online_cursors(task_id, user_id)
    
    return CursorListResponse(
        cursors=[
            CursorInfo(
                user_id=c["user_id"],
                username="",  # TODO: 从用户表获取
                user_color=c["user_color"],
                page_index=c["page_index"],
                cursor_x=c["cursor_x"],
                cursor_y=c["cursor_y"],
                selected_element_id=c["selected_element_id"],
            )
            for c in cursors
        ]
    )


@router.put("/tasks/{task_id}/collaboration/cursor", summary="更新光标位置")
async def update_cursor(
    task_id: str,
    request: UpdateCursorRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新当前用户的光标位置"""
    service = CollaborationService(db)
    cursor = service.update_cursor_position(
        task_id=task_id,
        user_id=user_id,
        page_index=request.page_index,
        cursor_x=request.cursor_x,
        cursor_y=request.cursor_y,
        selected_element_id=request.selected_element_id,
    )
    
    if not cursor:
        raise HTTPException(status_code=400, detail="无法更新光标位置")
    
    return {"success": True}


@router.post("/tasks/{task_id}/collaboration/lock", 
             response_model=AcquireLockResponse, 
             summary="获取编辑锁")
async def acquire_lock(
    task_id: str,
    request: AcquireLockRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取元素的编辑锁"""
    service = CollaborationService(db)
    
    try:
        lock = service.acquire_lock(
            task_id=task_id,
            user_id=user_id,
            page_index=request.page_index,
            element_id=request.element_id,
            duration_seconds=request.duration,
        )
        
        if lock:
            return AcquireLockResponse(
                success=True,
                lock_id=lock.id,
                expires_at=lock.expires_at,
            )
        else:
            # 获取当前锁定者
            from app.models.collaboration import EditLock, CollaborationSession
            from datetime import datetime
            
            session = db.query(CollaborationSession).filter(
                CollaborationSession.task_id == task_id
            ).first()
            
            if session:
                existing = db.query(EditLock).filter(
                    EditLock.session_id == session.id,
                    EditLock.page_index == request.page_index,
                    EditLock.element_id == request.element_id,
                    EditLock.expires_at > datetime.utcnow()
                ).first()
                
                return AcquireLockResponse(
                    success=False,
                    locked_by=existing.locked_by if existing else None,
                )
            
            return AcquireLockResponse(success=False)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/tasks/{task_id}/collaboration/lock", summary="释放编辑锁")
async def release_lock(
    task_id: str,
    page_index: int,
    element_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """释放元素的编辑锁"""
    service = CollaborationService(db)
    success = service.release_lock(task_id, user_id, page_index, element_id)
    
    return {"success": success}
