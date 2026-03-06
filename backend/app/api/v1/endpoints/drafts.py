"""
草稿管理 API
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.core import get_current_user_id
from app.models import Draft, DraftPage, DraftStatus, Slide, Document
from app.models.outline import OutlineSection
from app.schemas import (
    DraftCreate,
    DraftUpdate,
    DraftResponse,
    DraftDetailResponse,
    DraftListResponse,
    DraftPageResponse,
    DraftPageDetailResponse,
    AddPageRequest,
    AddPagesRequest,
    ReorderPagesRequest,
    DraftExportRequest,
    DraftExportResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ============== 草稿 CRUD ==============

@router.post("", response_model=DraftResponse, summary="创建草稿")
async def create_draft(
    request: DraftCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """创建新草稿"""
    draft = Draft(
        title=request.title,
        description=request.description,
        outline_id=request.outline_id,
        owner_id=user_id,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    
    return DraftResponse.model_validate(draft)


@router.get("", response_model=DraftListResponse, summary="获取草稿列表")
async def get_drafts(
    page: int = 1,
    limit: int = 20,
    status: Optional[DraftStatus] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取用户的草稿列表"""
    query = db.query(Draft).filter(
        Draft.owner_id == user_id,
        Draft.is_deleted == False
    )
    
    if status:
        query = query.filter(Draft.status == status)
    
    total = query.count()
    drafts = query.order_by(Draft.updated_at.desc()) \
        .offset((page - 1) * limit) \
        .limit(limit) \
        .all()
    
    return DraftListResponse(
        drafts=[DraftResponse.model_validate(d) for d in drafts],
        total=total
    )


@router.get("/{draft_id}", response_model=DraftDetailResponse, summary="获取草稿详情")
async def get_draft(
    draft_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取草稿详情，包含所有页面和关联的章节信息"""
    draft = db.query(Draft).filter(
        Draft.id == draft_id,
        Draft.owner_id == user_id,
        Draft.is_deleted == False
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="草稿不存在"
        )
    
    pages = db.query(DraftPage).filter(
        DraftPage.draft_id == draft_id
    ).order_by(DraftPage.order_index).all()
    
    response = DraftDetailResponse.model_validate(draft)
    response.pages = [DraftPageResponse.model_validate(p) for p in pages]
    
    # 如果草稿关联了大纲，获取章节信息
    if draft.outline_id:
        sections = db.query(OutlineSection).filter(
            OutlineSection.outline_id == draft.outline_id
        ).order_by(OutlineSection.order_index).all()
        
        # 构建章节信息映射
        sections_data = []
        for section in sections:
            sections_data.append({
                "id": section.id,
                "title": section.title,
                "description": section.description,
                "expected_pages": section.expected_pages,
                "order_index": section.order_index
            })
        
        # 将章节信息添加到响应中
        response.sections = sections_data
    
    return response


@router.put("/{draft_id}", response_model=DraftResponse, summary="更新草稿")
async def update_draft(
    draft_id: str,
    request: DraftUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新草稿信息"""
    draft = db.query(Draft).filter(
        Draft.id == draft_id,
        Draft.owner_id == user_id,
        Draft.is_deleted == False
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="草稿不存在"
        )
    
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(draft, field, value)
    
    db.commit()
    db.refresh(draft)
    
    return DraftResponse.model_validate(draft)


@router.delete("/{draft_id}", summary="删除草稿")
async def delete_draft(
    draft_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """删除草稿"""
    draft = db.query(Draft).filter(
        Draft.id == draft_id,
        Draft.owner_id == user_id,
        Draft.is_deleted == False
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="草稿不存在"
        )
    
    from datetime import datetime
    draft.is_deleted = True
    draft.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}


# ============== 页面操作 ==============

@router.post("/{draft_id}/pages", response_model=DraftPageResponse, summary="添加页面")
async def add_page(
    draft_id: str,
    request: AddPageRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """从文档库添加页面到草稿"""
    draft = db.query(Draft).filter(
        Draft.id == draft_id,
        Draft.owner_id == user_id,
        Draft.is_deleted == False
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="草稿不存在"
        )
    
    # 验证源页面存在
    source_slide = db.query(Slide).join(Document).filter(
        Slide.id == request.slide_id,
        Document.owner_id == user_id
    ).first()
    
    if not source_slide:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="源页面不存在"
        )
    
    # 计算排序索引
    if request.position is not None:
        order_index = request.position
        # 将后面的页面顺序后移
        db.query(DraftPage).filter(
            DraftPage.draft_id == draft_id,
            DraftPage.order_index >= request.position
        ).update({DraftPage.order_index: DraftPage.order_index + 1})
    else:
        order_index = db.query(DraftPage).filter(
            DraftPage.draft_id == draft_id
        ).count()
    
    page = DraftPage(
        draft_id=draft_id,
        source_slide_id=request.slide_id,
        section_id=request.section_id,
        title=source_slide.title,
        order_index=order_index,
        thumbnail_path=source_slide.thumbnail_path,
    )
    db.add(page)
    
    draft.page_count += 1
    
    db.commit()
    db.refresh(page)
    
    return DraftPageResponse.model_validate(page)


@router.post("/{draft_id}/pages/batch", summary="批量添加页面")
async def add_pages_batch(
    draft_id: str,
    request: AddPagesRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """批量添加页面到草稿"""
    draft = db.query(Draft).filter(
        Draft.id == draft_id,
        Draft.owner_id == user_id,
        Draft.is_deleted == False
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="草稿不存在"
        )
    
    # 获取当前最大排序索引
    current_max = db.query(DraftPage).filter(
        DraftPage.draft_id == draft_id
    ).count()
    
    added_pages = []
    for idx, slide_id in enumerate(request.slide_ids):
        source_slide = db.query(Slide).join(Document).filter(
            Slide.id == slide_id,
            Document.owner_id == user_id
        ).first()
        
        if source_slide:
            page = DraftPage(
                draft_id=draft_id,
                source_slide_id=slide_id,
                section_id=request.section_id,
                title=source_slide.title,
                order_index=current_max + idx,
                thumbnail_path=source_slide.thumbnail_path,
            )
            db.add(page)
            added_pages.append(page)
    
    draft.page_count += len(added_pages)
    
    db.commit()
    
    return {
        "success": True,
        "added_count": len(added_pages),
        "pages": [DraftPageResponse.model_validate(p) for p in added_pages]
    }


@router.delete("/{draft_id}/pages/{page_id}", summary="移除页面")
async def remove_page(
    draft_id: str,
    page_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """从草稿移除页面"""
    page = db.query(DraftPage).join(Draft).filter(
        DraftPage.id == page_id,
        DraftPage.draft_id == draft_id,
        Draft.owner_id == user_id
    ).first()
    
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="页面不存在"
        )
    
    removed_index = page.order_index
    db.delete(page)
    
    # 更新后续页面的排序索引
    db.query(DraftPage).filter(
        DraftPage.draft_id == draft_id,
        DraftPage.order_index > removed_index
    ).update({DraftPage.order_index: DraftPage.order_index - 1})
    
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    draft.page_count -= 1
    
    db.commit()
    
    return {"success": True}


@router.post("/{draft_id}/pages/reorder", summary="重排页面顺序")
async def reorder_pages(
    draft_id: str,
    request: ReorderPagesRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """重新排列草稿页面顺序"""
    draft = db.query(Draft).filter(
        Draft.id == draft_id,
        Draft.owner_id == user_id,
        Draft.is_deleted == False
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="草稿不存在"
        )
    
    for order in request.page_orders:
        page = db.query(DraftPage).filter(
            DraftPage.id == order["page_id"],
            DraftPage.draft_id == draft_id
        ).first()
        if page:
            page.order_index = order["order_index"]
    
    db.commit()
    
    return {"success": True}


# ============== 导出 ==============

@router.post("/{draft_id}/export", response_model=DraftExportResponse, summary="导出草稿")
async def export_draft(
    draft_id: str,
    request: DraftExportRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """导出草稿为 PPTX 文件"""
    from datetime import datetime
    from app.services.ppt_export import ppt_export_service
    import os
    
    draft = db.query(Draft).filter(
        Draft.id == draft_id,
        Draft.owner_id == user_id,
        Draft.is_deleted == False
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="草稿不存在"
        )
    
    # 获取草稿页面
    pages = db.query(DraftPage).filter(
        DraftPage.draft_id == draft_id
    ).order_by(DraftPage.order_index).all()
    
    # 获取章节信息
    chapters_data = []
    if draft.outline_id:
        sections = db.query(OutlineSection).filter(
            OutlineSection.outline_id == draft.outline_id
        ).order_by(OutlineSection.order_index).all()
        
        # 按章节分组页面
        section_pages = {}
        for page in pages:
            sid = page.section_id or 'unassigned'
            if sid not in section_pages:
                section_pages[sid] = []
            section_pages[sid].append(page)
        
        for section in sections:
            chapter_pages = section_pages.get(section.id, [])
            chapters_data.append({
                'title': section.title,
                'description': section.description or '',
                'pages': [
                    {
                        'title': p.title or section.title,
                        'content_summary': p.title or ''
                    }
                    for p in chapter_pages
                ]
            })
    else:
        # 没有关联大纲，创建默认章节
        chapters_data.append({
            'title': draft.title,
            'description': draft.description or '',
            'pages': [
                {
                    'title': p.title or f'页面 {i+1}',
                    'content_summary': p.title or ''
                }
                for i, p in enumerate(pages)
            ]
        })
    
    # 生成 PPT
    try:
        filepath = ppt_export_service.create_ppt(
            title=draft.title,
            chapters=chapters_data,
            description=draft.description
        )
        
        # 获取文件大小
        file_size = os.path.getsize(filepath)
        filename = os.path.basename(filepath)
        
        # 更新草稿状态
        draft.exported_file_path = filepath
        draft.status = DraftStatus.COMPLETED
        db.commit()
        
        return DraftExportResponse(
            download_url=f"/api/drafts/{draft_id}/download/{filename}",
            file_size=file_size,
            file_name=f"{draft.title}.pptx",
            exported_at=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出失败: {str(e)}"
        )


@router.post("/{draft_id}/preview", response_model=DraftExportResponse, summary="预览草稿")
async def preview_draft(
    draft_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """导出草稿为 PPTX 并生成预览 URL（上传到 COS）"""
    from datetime import datetime
    from app.services.ppt_export import ppt_export_service
    from app.services.cos_upload import cos_upload_service
    import os
    
    draft = db.query(Draft).filter(
        Draft.id == draft_id,
        Draft.owner_id == user_id,
        Draft.is_deleted == False
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="草稿不存在"
        )
    
    # 获取草稿页面
    pages = db.query(DraftPage).filter(
        DraftPage.draft_id == draft_id
    ).order_by(DraftPage.order_index).all()
    
    if not pages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="草稿没有页面，无法预览"
        )
    
    # 获取章节信息（与导出功能相同）
    chapters_data = []
    if draft.outline_id:
        sections = db.query(OutlineSection).filter(
            OutlineSection.outline_id == draft.outline_id
        ).order_by(OutlineSection.order_index).all()
        
        section_pages = {}
        for page in pages:
            sid = page.section_id or 'unassigned'
            if sid not in section_pages:
                section_pages[sid] = []
            section_pages[sid].append(page)
        
        for section in sections:
            chapter_pages = section_pages.get(section.id, [])
            chapters_data.append({
                'title': section.title,
                'description': section.description or '',
                'pages': [
                    {
                        'title': p.title or section.title,
                        'content_summary': p.title or ''
                    }
                    for p in chapter_pages
                ]
            })
    else:
        chapters_data.append({
            'title': draft.title,
            'description': draft.description or '',
            'pages': [
                {
                    'title': p.title or f'页面 {i+1}',
                    'content_summary': p.title or ''
                }
                for i, p in enumerate(pages)
            ]
        })
    
    # 生成 PPT
    try:
        filepath = ppt_export_service.create_ppt(
            title=draft.title,
            chapters=chapters_data,
            description=draft.description
        )
        
        file_size = os.path.getsize(filepath)
        filename = f"{draft.title}.pptx"
        
        # 上传到 COS 并获取预览 URL
        if cos_upload_service.enabled:
            preview_url = cos_upload_service.get_preview_url(filepath)
            
            if preview_url:
                # 更新草稿状态
                draft.exported_file_path = filepath
                draft.status = DraftStatus.COMPLETED
                db.commit()
                
                return DraftExportResponse(
                    download_url=preview_url,
                    file_size=file_size,
                    file_name=filename,
                    exported_at=datetime.utcnow()
                )
            else:
                # COS 上传失败，回退到本地文件 URL
                return DraftExportResponse(
                    download_url=f"/api/drafts/{draft_id}/download/{os.path.basename(filepath)}",
                    file_size=file_size,
                    file_name=filename,
                    exported_at=datetime.utcnow()
                )
        else:
            # COS 未配置，使用本地文件 URL
            return DraftExportResponse(
                download_url=f"/api/drafts/{draft_id}/download/{os.path.basename(filepath)}",
                file_size=file_size,
                file_name=filename,
                exported_at=datetime.utcnow()
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览准备失败: {str(e)}"
        )


@router.get("/{draft_id}/download/{filename}", summary="下载导出的文件")
async def download_export(
    draft_id: str,
    filename: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """下载导出的 PPT 文件"""
    from fastapi.responses import FileResponse
    import os
    
    draft = db.query(Draft).filter(
        Draft.id == draft_id,
        Draft.owner_id == user_id,
        Draft.is_deleted == False
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="草稿不存在"
        )
    
    filepath = f"./data/exports/{filename}"
    
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在"
        )
    
    return FileResponse(
        path=filepath,
        filename=f"{draft.title}.pptx",
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
