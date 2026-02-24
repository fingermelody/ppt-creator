"""
PPT 智能生成 API
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

from app.db import get_db
from app.core import get_current_user_id
from app.models import (
    GenerationTask,
    GeneratedPage,
    WebSource,
    PPTTemplate,
    GenerationStatus,
    SearchDepth,
)
from app.schemas import (
    TemplateResponse,
    TemplateListResponse,
    TemplateUploadResponse,
    GenerationTaskResponse,
    GenerationTaskDetailResponse,
    TaskListResponse,
    GenerationRequest,
    GenerationResponse,
    GenerationProgressResponse,
    GeneratedPageResponse,
    WebSourceResponse,
    RegeneratePageRequest,
    RegeneratePageResponse,
    PageSourcesResponse,
    ExportRequest,
    ExportResponse,
    SearchMoreRequest,
    SearchMoreResponse,
)

router = APIRouter()


# ============== 模板管理 ==============

@router.get("/templates", response_model=TemplateListResponse, summary="获取模板列表")
async def get_templates(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取 PPT 模板列表"""
    query = db.query(PPTTemplate)
    
    if category:
        query = query.filter(PPTTemplate.category == category)
    
    templates = query.order_by(PPTTemplate.usage_count.desc()).all()
    
    # 获取所有分类
    categories = db.query(PPTTemplate.category).distinct().all()
    categories = [c[0] for c in categories]
    
    return TemplateListResponse(
        templates=[TemplateResponse.model_validate(t) for t in templates],
        total=len(templates),
        categories=categories
    )


@router.get("/templates/{template_id}", response_model=TemplateResponse, summary="获取模板详情")
async def get_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """获取模板详情"""
    template = db.query(PPTTemplate).filter(PPTTemplate.id == template_id).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )
    
    return TemplateResponse.model_validate(template)


@router.post("/templates/upload", response_model=TemplateUploadResponse, summary="上传自定义模板")
async def upload_template(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """上传自定义模板"""
    # TODO: 实现文件保存和预览生成
    import uuid
    
    template = PPTTemplate(
        name=file.filename.rsplit(".", 1)[0] if file.filename else "自定义模板",
        category="custom",
        file_path=f"/data/templates/{uuid.uuid4()}.pptx",
        is_custom=1,
        owner_id=user_id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return TemplateUploadResponse(
        template_id=template.id,
        preview_url=template.preview_url or "",
        name=template.name
    )


@router.delete("/templates/{template_id}", summary="删除自定义模板")
async def delete_template(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """删除自定义模板"""
    template = db.query(PPTTemplate).filter(
        PPTTemplate.id == template_id,
        PPTTemplate.owner_id == user_id,
        PPTTemplate.is_custom == 1
    ).first()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在或无权删除"
        )
    
    db.delete(template)
    db.commit()
    
    return {"success": True}


# ============== 生成任务管理 ==============

@router.get("/tasks", response_model=TaskListResponse, summary="获取任务列表")
async def get_tasks(
    page: int = 1,
    limit: int = 20,
    status: Optional[GenerationStatus] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取用户的生成任务列表"""
    query = db.query(GenerationTask).filter(
        GenerationTask.owner_id == user_id,
        GenerationTask.is_deleted == False
    )
    
    if status:
        query = query.filter(GenerationTask.status == status)
    
    total = query.count()
    tasks = query.order_by(GenerationTask.created_at.desc()) \
        .offset((page - 1) * limit) \
        .limit(limit) \
        .all()
    
    return TaskListResponse(
        tasks=[GenerationTaskResponse.model_validate(t) for t in tasks],
        total=total
    )


@router.get("/tasks/{task_id}", response_model=GenerationTaskDetailResponse, summary="获取任务详情")
async def get_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取生成任务详情"""
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.owner_id == user_id,
        GenerationTask.is_deleted == False
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    pages = db.query(GeneratedPage).filter(
        GeneratedPage.task_id == task_id
    ).order_by(GeneratedPage.page_index).all()
    
    sources = db.query(WebSource).filter(
        WebSource.task_id == task_id
    ).order_by(WebSource.relevance.desc()).all()
    
    response = GenerationTaskDetailResponse.model_validate(task)
    response.pages = [GeneratedPageResponse.model_validate(p) for p in pages]
    response.sources = [WebSourceResponse.model_validate(s) for s in sources]
    
    return response


@router.post("/tasks", response_model=GenerationResponse, summary="开始生成")
async def start_generation(
    request: GenerationRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    开始生成 PPT
    
    系统会根据主题进行联网搜索，收集相关信息，然后使用 AI 生成 PPT
    """
    task = GenerationTask(
        topic=request.topic,
        title=request.title,
        page_count=request.page_count,
        template_id=request.template_id,
        include_images=1 if request.include_images else 0,
        include_charts=1 if request.include_charts else 0,
        language=request.language,
        search_depth=request.search_depth,
        status=GenerationStatus.PENDING,
        owner_id=user_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    
    # TODO: 触发异步生成任务
    # celery_app.send_task('generate_ppt', args=[task.id])
    
    return GenerationResponse(
        task_id=task.id,
        status=task.status,
        message="生成任务已创建，正在处理中...",
        estimated_time=60 * (1 + (1 if request.search_depth == SearchDepth.DEEP else 0))
    )


@router.get("/tasks/{task_id}/progress", response_model=GenerationProgressResponse, summary="获取生成进度")
async def get_progress(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取生成进度"""
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.owner_id == user_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    return GenerationProgressResponse(
        task_id=task.id,
        status=task.status,
        progress=task.progress,
        current_step=task.current_step or "",
        message=task.message or "",
        sources_found=task.sources_found,
        pages_generated=task.total_pages
    )


@router.post("/tasks/{task_id}/cancel", summary="取消生成")
async def cancel_generation(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取消生成任务"""
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.owner_id == user_id,
        GenerationTask.status.in_([GenerationStatus.PENDING, GenerationStatus.SEARCHING, 
                                   GenerationStatus.ANALYZING, GenerationStatus.GENERATING])
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在或无法取消"
        )
    
    task.status = GenerationStatus.CANCELLED
    db.commit()
    
    # TODO: 取消 Celery 任务
    
    return {"success": True, "message": "任务已取消"}


@router.delete("/tasks/{task_id}", summary="删除任务")
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """删除生成任务"""
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.owner_id == user_id,
        GenerationTask.is_deleted == False
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    from datetime import datetime
    task.is_deleted = True
    task.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}


# ============== 页面操作 ==============

@router.post("/tasks/{task_id}/pages/{page_index}/regenerate", response_model=RegeneratePageResponse, summary="重新生成页面")
async def regenerate_page(
    task_id: str,
    page_index: int,
    request: RegeneratePageRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """重新生成指定页面"""
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.owner_id == user_id,
        GenerationTask.status == GenerationStatus.COMPLETED
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在或未完成"
        )
    
    page = db.query(GeneratedPage).filter(
        GeneratedPage.task_id == task_id,
        GeneratedPage.page_index == page_index
    ).first()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="页面不存在"
        )
    
    # TODO: 调用 LLM 重新生成页面
    
    return RegeneratePageResponse(
        success=True,
        page=GeneratedPageResponse.model_validate(page),
        message="页面重新生成成功"
    )


@router.get("/tasks/{task_id}/pages/{page_index}/sources", response_model=PageSourcesResponse, summary="获取页面来源")
async def get_page_sources(
    task_id: str,
    page_index: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取页面的引用来源"""
    page = db.query(GeneratedPage).join(GenerationTask).filter(
        GeneratedPage.task_id == task_id,
        GeneratedPage.page_index == page_index,
        GenerationTask.owner_id == user_id
    ).first()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="页面不存在"
        )
    
    source_ids = page.source_ids or []
    sources = db.query(WebSource).filter(
        WebSource.id.in_(source_ids)
    ).all() if source_ids else []
    
    return PageSourcesResponse(
        sources=[WebSourceResponse.model_validate(s) for s in sources],
        citations=[]  # TODO: 提取具体引用
    )


# ============== 导出 ==============

@router.post("/tasks/{task_id}/export", response_model=ExportResponse, summary="导出 PPT")
async def export_ppt(
    task_id: str,
    request: ExportRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """导出生成的 PPT"""
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.owner_id == user_id,
        GenerationTask.status == GenerationStatus.COMPLETED
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在或未完成"
        )
    
    # TODO: 实现导出逻辑
    from datetime import datetime
    
    return ExportResponse(
        download_url=f"/api/downloads/generation/{task_id}.{request.format}",
        file_size=0,
        file_name=f"{task.title or 'presentation'}.{request.format}",
        exported_at=datetime.utcnow()
    )


# ============== 搜索来源 ==============

@router.post("/tasks/{task_id}/search", response_model=SearchMoreResponse, summary="搜索更多来源")
async def search_more_sources(
    task_id: str,
    request: SearchMoreRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """手动触发搜索更多来源"""
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id,
        GenerationTask.owner_id == user_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # TODO: 调用搜索服务
    
    return SearchMoreResponse(
        success=True,
        new_sources=[],
        total_sources=task.sources_found
    )


@router.delete("/tasks/{task_id}/sources/{source_id}", summary="移除来源")
async def remove_source(
    task_id: str,
    source_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """移除某个来源"""
    source = db.query(WebSource).join(GenerationTask).filter(
        WebSource.id == source_id,
        WebSource.task_id == task_id,
        GenerationTask.owner_id == user_id
    ).first()
    
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="来源不存在"
        )
    
    db.delete(source)
    
    task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
    task.sources_found -= 1
    
    db.commit()
    
    return {"success": True}


# ============== SSE 流式进度 ==============

@router.get("/tasks/{task_id}/stream", summary="流式获取进度")
async def stream_progress(
    task_id: str,
    token: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """使用 SSE 流式获取生成进度"""
    # TODO: 验证 token 并获取 user_id
    
    task = db.query(GenerationTask).filter(
        GenerationTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    async def event_generator():
        import asyncio
        
        while True:
            # 刷新任务状态
            db.refresh(task)
            
            progress_data = {
                "type": "progress",
                "payload": {
                    "task_id": task.id,
                    "status": task.status.value,
                    "progress": task.progress,
                    "current_step": task.current_step or "",
                    "message": task.message or "",
                    "sources_found": task.sources_found,
                    "pages_generated": task.total_pages,
                }
            }
            
            yield f"data: {json.dumps(progress_data)}\n\n"
            
            if task.status == GenerationStatus.COMPLETED:
                complete_data = {
                    "type": "complete",
                    "payload": GenerationTaskResponse.model_validate(task).model_dump()
                }
                yield f"data: {json.dumps(complete_data)}\n\n"
                break
            elif task.status == GenerationStatus.FAILED:
                error_data = {
                    "type": "error",
                    "payload": {"message": task.error_message or "生成失败"}
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
            elif task.status == GenerationStatus.CANCELLED:
                error_data = {
                    "type": "error",
                    "payload": {"message": "任务已取消"}
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                break
            
            await asyncio.sleep(1)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
