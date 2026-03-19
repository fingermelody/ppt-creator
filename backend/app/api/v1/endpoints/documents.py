"""
文档管理 API

上传流程：
1. 分片上传到本地临时目录
2. 合并分片
3. 上传 PPT 到 COS 存储桶（永久存储）
4. 解析 PPT 每一页内容
5. 创建 Slide 记录并向量化
6. 更新文档状态为就绪
"""

from typing import Optional
import os
import uuid
import shutil
from pathlib import Path
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db import get_db, SessionLocal
from app.core import get_current_user_id
from app.core.config import settings
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

logger = logging.getLogger(__name__)

router = APIRouter()

# 内存中存储上传会话信息（生产环境应使用 Redis）
upload_sessions = {}

# 线程池执行器（用于后台处理）
executor = ThreadPoolExecutor(max_workers=4)


def get_upload_dir() -> Path:
    """获取上传目录，优先使用相对于项目的目录"""
    # 使用项目目录下的 uploads 文件夹
    project_dir = Path(__file__).parent.parent.parent.parent.parent
    upload_dir = project_dir / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def get_chunk_dir(upload_id: str) -> Path:
    """获取分片临时存储目录"""
    chunk_dir = get_upload_dir() / "chunks" / upload_id
    chunk_dir.mkdir(parents=True, exist_ok=True)
    return chunk_dir


def get_file_dir() -> Path:
    """获取最终文件存储目录"""
    file_dir = get_upload_dir() / "files"
    file_dir.mkdir(parents=True, exist_ok=True)
    return file_dir


def process_document_background(document_id: str, file_path: str, original_filename: str):
    """
    后台处理文档：上传到 COS、ADP 解析内容、生成缩略图、向量化
    
    Args:
        document_id: 文档 ID
        file_path: 本地文件路径
        original_filename: 原始文件名
    """
    from app.services.cos_upload import cos_upload_service
    from app.services.ppt_parser import parse_ppt_file
    from app.services.vectorization import get_vectorization_service
    
    db = SessionLocal()
    
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found: {document_id}")
            return
        
        # 1. Upload to COS
        logger.info(f"Uploading document to COS: {document_id}")
        document.status = DocumentStatus.PROCESSING
        db.commit()
        
        cos_key, cos_url = cos_upload_service.upload_ppt(
            file_path=file_path,
            document_id=document_id,
            original_filename=original_filename
        )
        
        if not cos_key or not cos_url:
            raise Exception("Failed to upload to COS")
        
        document.cos_object_key = cos_key
        document.cos_url = cos_url
        db.commit()
        logger.info(f"COS upload success: {cos_url}")
        
        # 2. Parse PPT (ADP first, fallback to python-pptx)
        logger.info(f"Parsing PPT: {document_id}")
        document.status = DocumentStatus.PARSING
        db.commit()
        
        slides_content = parse_ppt_file(file_path, cos_url=cos_url)
        document.page_count = len(slides_content)
        db.commit()
        logger.info(f"PPT parsed: {len(slides_content)} pages")
        
        # 3. Generate thumbnail URLs via COS CI doc-preview
        logger.info(f"Generating thumbnail URLs: {document_id}")
        thumbnail_urls = []
        if cos_key and cos_upload_service.enabled:
            thumbnail_urls = cos_upload_service.generate_all_thumbnail_urls(
                object_key=cos_key,
                page_count=len(slides_content),
                scale=50,
                dst_type="png",
            )
        
        # 4. Create Slide records and vectorize
        logger.info(f"Creating Slide records and vectorizing: {document_id}")
        document.status = DocumentStatus.VECTORIZING
        db.commit()
        
        vectorization_service = get_vectorization_service()
        vectorized_count = 0
        
        source_url = document.cos_url
        source_filename = document.original_filename
        
        for idx, slide_content in enumerate(slides_content):
            slide_id = str(uuid.uuid4())
            
            # Get thumbnail URL for this page
            thumb_url = None
            if idx < len(thumbnail_urls):
                thumb_url = thumbnail_urls[idx]
            
            slide = Slide(
                id=slide_id,
                document_id=document_id,
                page_number=slide_content.page_number,
                title=slide_content.title,
                content_text=slide_content.content_text,
                layout_type=slide_content.layout_type,
                elements=slide_content.elements,
                thumbnail_url=thumb_url,
                thumbnail_cos_key=cos_key if thumb_url else None,
            )
            db.add(slide)
            db.flush()
            
            # Vectorize
            if slide_content.content_text:
                vector_id = vectorization_service.vectorize_slide(
                    slide_id=slide_id,
                    document_id=document_id,
                    page_number=slide_content.page_number,
                    content_text=slide_content.content_text,
                    title=slide_content.title,
                    source_url=source_url,
                    source_filename=source_filename
                )
                
                if vector_id:
                    slide.vector_id = vector_id
                    slide.is_vectorized = 1
                    vectorized_count += 1
            
            db.commit()
            logger.debug(f"Processed page {slide_content.page_number}")
        
        # 5. Update document status
        document.vectorized_pages = vectorized_count
        document.status = DocumentStatus.READY
        db.commit()
        
        logger.info(
            f"Document processing complete: {document_id}, "
            f"{len(slides_content)} pages, {vectorized_count} vectorized"
        )
        
    except Exception as e:
        logger.error(f"Document processing failed: {document_id}, error: {e}")
        try:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = DocumentStatus.ERROR
                document.error_message = str(e)
                db.commit()
        except:
            pass
    finally:
        db.close()


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
    upload_id = str(uuid.uuid4())
    
    # 保存上传会话信息
    upload_sessions[upload_id] = {
        "filename": request.filename,
        "filesize": request.filesize,
        "total_chunks": request.total_chunks,
        "received_chunks": set(),
        "user_id": user_id
    }
    
    # 创建分片目录
    get_chunk_dir(upload_id)
    
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
    # 检查上传会话
    if upload_id not in upload_sessions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的上传会话"
        )
    
    session = upload_sessions[upload_id]
    
    # 验证用户
    if session["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此上传会话"
        )
    
    # 保存分片
    chunk_dir = get_chunk_dir(upload_id)
    chunk_path = chunk_dir / f"chunk_{chunk_index}"
    
    content = await chunk.read()
    with open(chunk_path, "wb") as f:
        f.write(content)
    
    # 记录已接收的分片
    session["received_chunks"].add(chunk_index)
    
    return UploadChunkResponse(
        success=True, 
        received_chunks=len(session["received_chunks"])
    )


@router.post("/upload/complete", response_model=UploadCompleteResponse, summary="完成上传")
async def complete_upload(
    request: UploadCompleteRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    完成分片上传，合并文件并开始后台处理
    
    后台处理流程：
    1. 上传 PPT 到 COS 存储桶
    2. 解析 PPT 每一页内容
    3. 创建 Slide 记录
    4. 向量化每一页内容
    """
    upload_id = request.upload_id
    
    # 检查上传会话
    if upload_id not in upload_sessions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的上传会话"
        )
    
    session = upload_sessions[upload_id]
    
    # 验证用户
    if session["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此上传会话"
        )
    
    # 检查所有分片是否已上传
    expected_chunks = set(range(session["total_chunks"]))
    if session["received_chunks"] != expected_chunks:
        missing = expected_chunks - session["received_chunks"]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"缺少分片: {missing}"
        )
    
    # 合并分片
    chunk_dir = get_chunk_dir(upload_id)
    original_filename = session["filename"]
    file_ext = Path(original_filename).suffix
    new_filename = f"{uuid.uuid4()}{file_ext}"
    final_path = get_file_dir() / new_filename
    
    try:
        with open(final_path, "wb") as outfile:
            for i in range(session["total_chunks"]):
                chunk_path = chunk_dir / f"chunk_{i}"
                with open(chunk_path, "rb") as infile:
                    outfile.write(infile.read())
        
        # 清理分片目录
        shutil.rmtree(chunk_dir)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件合并失败: {str(e)}"
        )
    
    # 创建文档记录（初始状态为处理中）
    document_id = str(uuid.uuid4())
    
    document = Document(
        id=document_id,
        filename=new_filename,
        original_filename=original_filename,
        title=request.title or Path(original_filename).stem,
        file_size=session["filesize"],
        file_path=str(final_path),
        page_count=0,  # 稍后由后台任务更新
        status=DocumentStatus.UPLOADING,  # 初始状态
        owner_id=user_id
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # 清理上传会话
    del upload_sessions[upload_id]
    
    # 启动后台处理任务
    background_tasks.add_task(
        process_document_background,
        document_id=document_id,
        file_path=str(final_path),
        original_filename=original_filename
    )
    
    logger.info(f"文档上传完成，启动后台处理: {document_id}")
    
    return UploadCompleteResponse(
        document_id=document_id,
        status="processing"  # 返回处理中状态
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


@router.post("/slides/search", summary="语义搜索相似页面")
async def search_similar_slides(
    query: str,
    n_results: int = 10,
    document_id: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    语义搜索相似 PPT 页面
    
    根据查询文本，使用向量相似度搜索匹配的 PPT 页面。
    返回结果包含源 PPT 地址和页码，可用于 PPT 组装。
    
    - **query**: 搜索文本（如章节标题或内容描述）
    - **n_results**: 返回结果数量（默认10条）
    - **document_id**: 可选，限制在特定文档内搜索
    
    返回结果包含：
    - slide_id: 页面 ID
    - document_id: 文档 ID
    - page_number: 页码
    - title: 页面标题
    - content: 页面内容
    - source_url: 源 PPT 的 COS URL（可直接下载）
    - source_filename: 源 PPT 的文件名
    - similarity: 相似度分数（0-1，越高越相似）
    """
    from app.services.vectorization import get_vectorization_service
    
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="搜索文本不能为空"
        )
    
    # 如果指定了文档 ID，验证用户权限
    if document_id:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.owner_id == user_id,
            Document.is_deleted == False
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在或无权访问"
            )
    
    vectorization_service = get_vectorization_service()
    
    if not vectorization_service.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="向量化服务未启用"
        )
    
    # 执行语义搜索
    results = vectorization_service.search_similar_slides(
        query=query.strip(),
        n_results=n_results,
        document_id=document_id
    )
    
    # 过滤用户有权访问的结果（如果没有指定文档 ID）
    if not document_id:
        # 获取用户的文档 ID 列表
        user_doc_ids = set(
            doc.id for doc in db.query(Document.id).filter(
                Document.owner_id == user_id,
                Document.is_deleted == False
            ).all()
        )
        
        # 过滤结果
        results = [r for r in results if r.get("document_id") in user_doc_ids]
    
    return {
        "query": query,
        "total": len(results),
        "results": results
    }


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


@router.get("/{document_id}/file", summary="下载文档文件")
async def download_document_file(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """下载文档原始文件"""
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
    
    file_path = Path(document.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    # 返回文件，支持在线预览
    return FileResponse(
        path=str(file_path),
        filename=document.original_filename,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )


@router.post("/{document_id}/preview", summary="获取文档预览链接")
async def preview_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    获取文档预览链接
    
    使用 COS 存储的文件生成腾讯云数据万象预览 URL
    """
    from app.services.cos_upload import cos_upload_service
    
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
    
    # 检查文档状态
    if document.status == DocumentStatus.ERROR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文档处理失败: {document.error_message or '未知错误'}"
        )
    
    if document.status in [DocumentStatus.UPLOADING, DocumentStatus.PROCESSING]:
        return {
            "success": False,
            "message": "文档正在处理中，请稍后再试",
            "status": document.status.value
        }
    
    # 优先使用 COS 存储的文件
    if document.cos_object_key:
        preview_url = cos_upload_service.get_preview_url(document.cos_object_key)
        
        if preview_url:
            logger.info(f"文档 {document_id} 预览链接生成成功（COS）")
            return {
                "success": True,
                "preview_url": preview_url,
                "filename": document.original_filename,
                "preview_type": "cos",
                "cos_url": document.cos_url
            }
    
    # 降级方案：使用本地文件
    if document.file_path:
        file_path = Path(document.file_path)
        if file_path.exists():
            # 尝试上传本地文件到 COS 并生成预览
            cos_key, cos_url = cos_upload_service.upload_ppt(
                file_path=str(file_path),
                document_id=document_id,
                original_filename=document.original_filename
            )
            
            if cos_key and cos_url:
                # 更新文档的 COS 信息
                document.cos_object_key = cos_key
                document.cos_url = cos_url
                db.commit()
                
                preview_url = cos_upload_service.get_preview_url(cos_key)
                if preview_url:
                    return {
                        "success": True,
                        "preview_url": preview_url,
                        "filename": document.original_filename,
                        "preview_type": "cos",
                        "cos_url": cos_url
                    }
            
            # 最后降级：返回本地文件下载链接
            logger.warning(f"COS 预览不可用，降级使用本地文件: {document_id}")
            return {
                "success": True,
                "preview_url": f"/api/documents/{document_id}/file",
                "filename": document.original_filename,
                "preview_type": "local"
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="文档文件不存在"
    )


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
    
    return {
        "document_id": document_id,
        "slides": [
            {
                "id": slide.id,
                "page_number": slide.page_number,
                "title": slide.title,
                "content": slide.content_text,
                "thumbnail_url": slide.thumbnail_url,
            }
            for slide in slides
        ],
        "total": len(slides)
    }


@router.get("/{document_id}/slides/preview", summary="获取文档页面预览数据")
async def get_document_slides_preview(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    获取文档所有页面的预览数据（缩略图 + 内容概要）
    
    返回每页的缩略图 URL（COS CI doc-preview）和内容摘要，
    用于文档详情页的页面总览展示。
    
    如果缩略图 URL 已过期，会实时重新生成。
    """
    from app.services.cos_upload import cos_upload_service
    
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
    
    if document.status != DocumentStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文档尚未就绪，当前状态: {document.status.value}"
        )
    
    slides = db.query(Slide).filter(Slide.document_id == document_id) \
        .order_by(Slide.page_number).all()
    
    # Regenerate thumbnail URLs if COS key is available
    fresh_thumbnails = {}
    if document.cos_object_key and cos_upload_service.enabled:
        urls = cos_upload_service.generate_all_thumbnail_urls(
            object_key=document.cos_object_key,
            page_count=len(slides),
            scale=50,
            dst_type="png",
        )
        for i, url in enumerate(urls):
            fresh_thumbnails[i + 1] = url
    
    slides_preview = []
    for slide in slides:
        # Use fresh URL if available, otherwise use stored URL
        thumb_url = fresh_thumbnails.get(slide.page_number) or slide.thumbnail_url
        
        # Generate content summary (first 150 chars)
        summary = ""
        if slide.content_text:
            summary = slide.content_text[:150]
            if len(slide.content_text) > 150:
                summary += "..."
        
        slides_preview.append({
            "id": slide.id,
            "page_number": slide.page_number,
            "title": slide.title,
            "summary": summary,
            "content_text": slide.content_text,
            "thumbnail_url": thumb_url,
            "layout_type": slide.layout_type,
            "is_vectorized": slide.is_vectorized,
        })
    
    return {
        "document_id": document_id,
        "title": document.title,
        "original_filename": document.original_filename,
        "page_count": document.page_count,
        "status": document.status.value,
        "cos_url": document.cos_url,
        "slides": slides_preview,
        "total": len(slides_preview),
    }


@router.post("/{document_id}/slides/search", summary="文档内页面语义检索")
async def search_document_slides(
    document_id: str,
    request: dict,  # 改为接收JSON body
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    在指定文档内进行页面级语义检索
    
    Request body:
    - **query**: 搜索查询文本
    - **n_results**: 返回结果数量（默认10）
    """
    from app.services.vectorization import get_vectorization_service
    
    # 提取参数
    query = request.get("query", "")
    n_results = request.get("n_results", 10)
    
    # 验证文档权限
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
    
    if not query or not query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="搜索文本不能为空"
        )
    
    try:
        # 获取向量化服务
        vector_service = get_vectorization_service()
        
        # 在文档范围内搜索
        results = vector_service.search_similar(
            query_text=query.strip(),
            n_results=n_results,
            document_id=document_id
        )
        
        # 格式化结果
        formatted_results = []
        for result in results:
            slide = db.query(Slide).filter(Slide.id == result["slide_id"]).first()
            if slide:
                formatted_results.append({
                    "slide_id": slide.id,
                    "page_number": slide.page_number,
                    "title": slide.title,
                    "content": slide.content_text,
                    "thumbnail_url": slide.thumbnail_url,
                    "similarity": result.get("similarity", 0.0),
                    "source_url": document.cos_url,
                    "source_filename": document.original_filename,
                })
        
        return {
            "document_id": document_id,
            "query": query,
            "results": formatted_results,
            "total": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"页面检索失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"检索失败: {str(e)}"
        )
    
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


