"""
版本历史管理 API
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.core import get_current_user_id
from app.models import RefinementTask
from app.models.version import VersionType
from app.services.version import VersionService
from app.schemas.version import (
    CreateVersionRequest, CreateVersionResponse,
    RollbackVersionRequest, RollbackResponse,
    CompareVersionsRequest, VersionComparisonResponse,
    VersionListResponse, VersionInfo, VersionDetailResponse,
    VersionSnapshotResponse, PageDiff,
)

router = APIRouter()


@router.get("/tasks/{task_id}/versions", response_model=VersionListResponse, summary="获取版本列表")
async def get_versions(
    task_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取精修任务的所有版本历史"""
    # 验证任务归属
    task = db.query(RefinementTask).filter(
        RefinementTask.id == task_id,
        RefinementTask.owner_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    service = VersionService(db)
    versions, total = service.get_versions(task_id, page, page_size)
    
    return VersionListResponse(
        versions=[
            VersionInfo(
                id=v.id,
                version_number=v.version_number,
                version_label=v.version_label,
                version_type=v.version_type.value,
                description=v.description,
                page_count=v.page_count,
                total_elements=v.total_elements,
                snapshot_size=v.snapshot_size,
                created_at=v.created_at,
                created_by=v.created_by,
            )
            for v in versions
        ],
        total=total,
        current_version=task.version,
    )


@router.post("/tasks/{task_id}/versions", response_model=CreateVersionResponse, summary="创建新版本")
async def create_version(
    task_id: str,
    request: CreateVersionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """手动创建一个新版本快照"""
    # 验证任务归属
    task = db.query(RefinementTask).filter(
        RefinementTask.id == task_id,
        RefinementTask.owner_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    service = VersionService(db)
    
    # 解析版本类型
    version_type_map = {
        "auto": VersionType.AUTO,
        "manual": VersionType.MANUAL,
        "export": VersionType.EXPORT,
    }
    version_type = version_type_map.get(request.version_type, VersionType.MANUAL)
    
    version = service.create_version(
        task_id=task_id,
        user_id=user_id,
        description=request.description,
        version_type=version_type
    )
    
    return CreateVersionResponse(
        success=True,
        version_id=version.id,
        version_label=version.version_label,
        created_at=version.created_at,
    )


@router.get("/tasks/{task_id}/versions/{version_id}", response_model=VersionDetailResponse, summary="获取版本详情")
async def get_version_detail(
    task_id: str,
    version_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取指定版本的详细信息"""
    # 验证任务归属
    task = db.query(RefinementTask).filter(
        RefinementTask.id == task_id,
        RefinementTask.owner_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    service = VersionService(db)
    version = service.get_version_detail(version_id)
    
    if not version or version.task_id != task_id:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    # 生成页面预览
    snapshot_preview = []
    pages = version.snapshot_data.get("pages", [])
    for page in pages[:10]:  # 最多返回前10页预览
        snapshot_preview.append({
            "page_index": page.get("page_index"),
            "title": page.get("title"),
            "element_count": len(page.get("elements", [])),
        })
    
    return VersionDetailResponse(
        id=version.id,
        version_number=version.version_number,
        version_label=version.version_label,
        version_type=version.version_type.value,
        description=version.description,
        page_count=version.page_count,
        total_elements=version.total_elements,
        snapshot_size=version.snapshot_size,
        created_at=version.created_at,
        created_by=version.created_by,
        snapshot_preview=snapshot_preview,
    )


@router.get("/tasks/{task_id}/versions/{version_id}/snapshot", response_model=VersionSnapshotResponse, summary="获取版本快照")
async def get_version_snapshot(
    task_id: str,
    version_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取版本的完整快照数据"""
    # 验证任务归属
    task = db.query(RefinementTask).filter(
        RefinementTask.id == task_id,
        RefinementTask.owner_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    service = VersionService(db)
    version = service.get_version_detail(version_id)
    
    if not version or version.task_id != task_id:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return VersionSnapshotResponse(
        version_id=version.id,
        version_label=version.version_label,
        pages=version.snapshot_data.get("pages", []),
        metadata=version.snapshot_data.get("task_info", {}),
    )


@router.post("/tasks/{task_id}/versions/{version_id}/rollback", response_model=RollbackResponse, summary="回滚到指定版本")
async def rollback_to_version(
    task_id: str,
    version_id: str,
    request: RollbackVersionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """回滚精修任务到指定版本"""
    # 验证任务归属
    task = db.query(RefinementTask).filter(
        RefinementTask.id == task_id,
        RefinementTask.owner_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    service = VersionService(db)
    
    try:
        result = service.rollback_to_version(
            task_id=task_id,
            version_id=version_id,
            user_id=user_id,
            create_backup=request.create_backup
        )
        
        return RollbackResponse(
            success=result["success"],
            backup_version_id=result.get("backup_version_id"),
            restored_version_id=result["restored_version_id"],
            restored_at=result["restored_at"],
            pages_restored=result["pages_restored"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/versions/compare", response_model=VersionComparisonResponse, summary="比较两个版本")
async def compare_versions(
    task_id: str,
    request: CompareVersionsRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """比较两个版本之间的差异"""
    # 验证任务归属
    task = db.query(RefinementTask).filter(
        RefinementTask.id == task_id,
        RefinementTask.owner_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    service = VersionService(db)
    
    try:
        result = service.compare_versions(
            version_from_id=request.version_from_id,
            version_to_id=request.version_to_id
        )
        
        return VersionComparisonResponse(
            version_from=VersionInfo(
                id=result["version_from"].id,
                version_number=result["version_from"].version_number,
                version_label=result["version_from"].version_label,
                version_type=result["version_from"].version_type.value,
                description=result["version_from"].description,
                page_count=result["version_from"].page_count,
                total_elements=result["version_from"].total_elements,
                snapshot_size=result["version_from"].snapshot_size,
                created_at=result["version_from"].created_at,
                created_by=result["version_from"].created_by,
            ),
            version_to=VersionInfo(
                id=result["version_to"].id,
                version_number=result["version_to"].version_number,
                version_label=result["version_to"].version_label,
                version_type=result["version_to"].version_type.value,
                description=result["version_to"].description,
                page_count=result["version_to"].page_count,
                total_elements=result["version_to"].total_elements,
                snapshot_size=result["version_to"].snapshot_size,
                created_at=result["version_to"].created_at,
                created_by=result["version_to"].created_by,
            ),
            summary=result["summary"],
            page_diffs=[
                PageDiff(
                    page_index=diff["page_index"],
                    status=diff["status"],
                    changes=diff.get("changes")
                )
                for diff in result["page_diffs"]
            ],
            element_changes=result["element_changes"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/tasks/{task_id}/versions/{version_id}", summary="删除版本")
async def delete_version(
    task_id: str,
    version_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """删除指定版本"""
    # 验证任务归属
    task = db.query(RefinementTask).filter(
        RefinementTask.id == task_id,
        RefinementTask.owner_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    service = VersionService(db)
    success = service.delete_version(version_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="版本不存在")
    
    return {"success": True, "message": "版本已删除"}


@router.post("/tasks/{task_id}/versions/auto-save", summary="自动保存版本")
async def auto_save_version(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """自动保存当前状态为新版本"""
    # 验证任务归属
    task = db.query(RefinementTask).filter(
        RefinementTask.id == task_id,
        RefinementTask.owner_id == user_id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    service = VersionService(db)
    version = service.auto_save_version(task_id, user_id)
    
    return {
        "success": True,
        "version_id": version.id,
        "version_label": version.version_label,
    }
