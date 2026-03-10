"""
大文件处理 API 端点
支持分片上传、断点续传、进度跟踪
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.large_file import LargeFileService, UploadStatus
from app.schemas.large_file import (
    InitUploadRequest,
    InitUploadResponse,
    UploadChunkResponse,
    UploadStatusResponse,
    ResumeUploadResponse,
    UploadCompleteResponse,
    CleanupExpiredResponse,
    UploadListResponse,
    UploadListItem,
    ChunkInfoResponse,
)

router = APIRouter()


def get_current_user_id() -> str:
    """临时获取用户ID（实际应从认证中间件获取）"""
    # TODO: 从认证中间件获取真实用户ID
    return "test-user-001"


@router.post("/init", response_model=InitUploadResponse, summary="初始化分片上传")
async def init_upload(
    request: InitUploadRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    初始化分片上传任务
    
    - **file_name**: 文件名
    - **file_size**: 文件大小（字节）
    - **file_type**: 文件MIME类型（可选）
    - **file_hash**: 文件SHA-256哈希，用于秒传检测（可选）
    - **chunk_size**: 自定义分片大小（可选，默认根据文件大小自动计算）
    
    返回上传任务ID和分片信息，客户端据此进行分片上传。
    如果提供file_hash且服务器已存在相同文件，则返回秒传成功。
    """
    service = LargeFileService(db)
    
    upload = service.init_upload(
        user_id=user_id,
        file_name=request.file_name,
        file_size=request.file_size,
        file_type=request.file_type,
        file_hash=request.file_hash,
        chunk_size=request.chunk_size,
    )
    
    # 检查是否秒传成功
    instant_upload = upload.status == UploadStatus.COMPLETED
    
    return InitUploadResponse(
        upload_id=upload.id,
        file_name=upload.file_name,
        file_size=upload.file_size,
        chunk_size=upload.chunk_size,
        total_chunks=upload.total_chunks,
        expires_at=upload.expires_at,
        instant_upload=instant_upload,
        final_path=upload.final_path if instant_upload else None,
    )


@router.post("/{upload_id}/chunk", response_model=UploadChunkResponse, summary="上传分片")
async def upload_chunk(
    upload_id: str,
    chunk_index: int = Form(..., ge=0, description="分片索引"),
    chunk_hash: Optional[str] = Form(None, description="分片SHA-256哈希"),
    chunk: UploadFile = File(..., description="分片文件数据"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    上传单个分片
    
    - **upload_id**: 上传任务ID（从init接口获取）
    - **chunk_index**: 分片索引（从0开始）
    - **chunk_hash**: 分片SHA-256哈希（可选，用于校验）
    - **chunk**: 分片二进制数据
    
    分片上传完成后自动检测是否所有分片已上传，如是则自动触发合并。
    """
    service = LargeFileService(db)
    
    # 读取分片数据
    chunk_data = await chunk.read()
    
    result = service.upload_chunk(
        upload_id=upload_id,
        chunk_index=chunk_index,
        chunk_data=chunk_data,
        chunk_hash=chunk_hash,
    )
    
    if not result.get("success", False):
        raise HTTPException(status_code=400, detail=result.get("error", "上传失败"))
    
    return UploadChunkResponse(
        success=True,
        chunk_index=result.get("chunk_index", chunk_index),
        uploaded_chunks=result.get("uploaded_chunks", 0),
        total_chunks=result.get("total_chunks", 0),
        progress=result.get("progress", 0),
        error=None,
    )


@router.get("/{upload_id}/status", response_model=UploadStatusResponse, summary="获取上传状态")
async def get_upload_status(
    upload_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    获取上传任务的当前状态
    
    返回已上传分片数、缺失分片列表、整体进度等信息。
    """
    service = LargeFileService(db)
    
    status = service.get_upload_status(upload_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    
    return UploadStatusResponse(**status)


@router.get("/{upload_id}/resume", response_model=ResumeUploadResponse, summary="获取断点续传信息")
async def resume_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    获取断点续传信息
    
    返回需要继续上传的分片列表及其详细信息（起始位置、结束位置、大小）。
    客户端可据此实现断点续传功能。
    """
    service = LargeFileService(db)
    
    result = service.resume_upload(upload_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="上传任务不存在")
    
    # 转换 missing_chunks_info 格式
    missing_chunks_info = [
        ChunkInfoResponse(**info) 
        for info in result.get("missing_chunks_info", [])
    ]
    
    return ResumeUploadResponse(
        id=result["id"],
        file_name=result["file_name"],
        file_size=result["file_size"],
        status=result["status"],
        chunk_size=result.get("chunk_size", 0),
        total_chunks=result["total_chunks"],
        uploaded_chunks=result["uploaded_chunks"],
        progress=result["progress"],
        missing_chunks=result.get("missing_chunks", []),
        missing_chunks_info=missing_chunks_info,
        final_path=result.get("final_path"),
        expires_at=result.get("expires_at"),
    )


@router.delete("/{upload_id}", summary="取消上传")
async def cancel_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    取消上传任务
    
    取消后会清理已上传的临时分片文件。
    """
    service = LargeFileService(db)
    
    success = service.cancel_upload(upload_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="上传任务不存在或无权操作")
    
    return {"success": True, "message": "上传已取消"}


@router.get("/", response_model=UploadListResponse, summary="获取上传列表")
async def list_uploads(
    status: Optional[str] = Query(None, description="筛选状态"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    获取用户的上传任务列表
    
    支持按状态筛选和分页。
    """
    from app.services.large_file import ChunkedUpload
    
    query = db.query(ChunkedUpload).filter(ChunkedUpload.user_id == user_id)
    
    if status:
        try:
            status_enum = UploadStatus(status)
            query = query.filter(ChunkedUpload.status == status_enum)
        except ValueError:
            pass
    
    total = query.count()
    
    uploads = query.order_by(ChunkedUpload.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()
    
    items = [
        UploadListItem(
            id=u.id,
            file_name=u.file_name,
            file_size=u.file_size,
            file_type=u.file_type,
            status=u.status.value,
            progress=u.uploaded_chunks / u.total_chunks * 100 if u.total_chunks > 0 else 0,
            created_at=u.created_at,
            expires_at=u.expires_at,
        )
        for u in uploads
    ]
    
    return UploadListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/cleanup", response_model=CleanupExpiredResponse, summary="清理过期上传")
async def cleanup_expired(
    db: Session = Depends(get_db),
):
    """
    清理过期的上传任务
    
    此接口通常由定时任务调用，清理超过24小时未完成的上传任务。
    """
    service = LargeFileService(db)
    
    count = service.cleanup_expired_uploads()
    
    return CleanupExpiredResponse(
        success=True,
        cleaned_count=count,
        message=f"已清理 {count} 个过期上传任务",
    )
