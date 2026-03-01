"""
文档管理 API
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db import get_db
from app.core import get_current_user_id
from app.models import Document, Slide, DocumentStatus
from app.schemas import (
    UploadInitRequest,
    UploadInitResponse,
    UploadChunkResponse,
    UploadCompleteRequest,
    UploadCompleteResponse,
    DocumentResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    SlideResponse,
    SlideDetailResponse,
)

router = APIRouter()


@router.post("/upload/init", response_model=UploadInitResponse, summary="初始化分片上传")
async def init_upload(
    request: UploadInitRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    初始化分片上传
    
    - **filename**: 文件名
    - **filesize**: 文件大小（字节）
    - **total_chunks**: 分片总数
    """
    # TODO: 实现分片上传初始化逻辑
    from app.core.config import settings
    import uuid
    
    upload_id = str(uuid.uuid4())
    
    return UploadInitResponse(
        upload_id=upload_id,
        chunk_size=settings.CHUNK_SIZE,
        total_chunks=request.total_chunks
    )


@router.post("/upload/chunk", response_model=UploadChunkResponse, summary="上传分片")
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    chunk: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    """上传文件分片"""
    # TODO: 实现分片上传逻辑
    return UploadChunkResponse(success=True, received_chunks=chunk_index + 1)


@router.post("/upload/complete", response_model=UploadCompleteResponse, summary="完成上传")
async def complete_upload(
    request: UploadCompleteRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    完成分片上传，合并文件并开始解析
    """
    # TODO: 实现文件合并和解析任务创建逻辑
    import uuid
    document_id = str(uuid.uuid4())
    
    return UploadCompleteResponse(
        document_id=document_id,
        status="parsing"
    )


@router.get("", response_model=DocumentListResponse, summary="获取文档列表")
async def get_documents(
    page: int = 1,
    limit: int = 20,
    status: Optional[DocumentStatus] = None,
    search: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    获取用户的文档列表
    
    - **page**: 页码
    - **limit**: 每页数量
    - **status**: 状态筛选
    - **search**: 搜索关键词
    """
    query = db.query(Document).filter(
        Document.owner_id == user_id,
        Document.is_deleted == False
    )
    
    if status:
        query = query.filter(Document.status == status)
    
    if search:
        query = query.filter(Document.original_filename.ilike(f"%{search}%"))
    
    total = query.count()
    documents = query.order_by(Document.created_at.desc()) \
        .offset((page - 1) * limit) \
        .limit(limit) \
        .all()
    
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        limit=limit
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse, summary="获取文档详情")
async def get_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取文档详情"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == user_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    slides = db.query(Slide).filter(Slide.document_id == document_id) \
        .order_by(Slide.page_number).all()
    
    response = DocumentDetailResponse.model_validate(document)
    response.slides = [SlideResponse.model_validate(s) for s in slides]
    
    return response


@router.get("/{document_id}/slides", summary="获取文档页面列表")
async def get_document_slides(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取文档的所有页面"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == user_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    slides = db.query(Slide).filter(Slide.document_id == document_id) \
        .order_by(Slide.page_number).all()
    
    return {"slides": [SlideResponse.model_validate(s) for s in slides]}


@router.delete("/{document_id}", summary="删除文档")
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """删除文档（软删除）"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.owner_id == user_id,
        Document.is_deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文档不存在"
        )
    
    from datetime import datetime
    document.is_deleted = True
    document.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}


@router.get("/search", response_model=DocumentListResponse, summary="搜索文档")
async def search_documents(
    query: str,
    page: int = 1,
    limit: int = 20,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """搜索文档"""
    db_query = db.query(Document).filter(
        Document.owner_id == user_id,
        Document.is_deleted == False,
        Document.original_filename.ilike(f"%{query}%")
    )
    
    total = db_query.count()
    documents = db_query.order_by(Document.created_at.desc()) \
        .offset((page - 1) * limit) \
        .limit(limit) \
        .all()
    
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        page=page,
        limit=limit
    )
