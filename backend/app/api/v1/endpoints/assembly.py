"""
PPT 组装 API
页面检索和选择
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.core import get_current_user_id
from app.models import Slide, OutlineSection, Document
from app.schemas import SlideResponse, SlideDetailResponse

router = APIRouter()


@router.get("/search", summary="语义搜索页面")
async def search_slides(
    query: str,
    limit: int = 20,
    document_ids: Optional[str] = None,  # 逗号分隔的文档ID
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    语义搜索页面
    
    - **query**: 搜索查询（支持自然语言）
    - **limit**: 返回结果数量
    - **document_ids**: 可选，限定在特定文档中搜索
    """
    # TODO: 调用向量数据库进行语义搜索
    # 目前使用简单的关键词搜索作为占位
    
    doc_ids = document_ids.split(",") if document_ids else None
    
    db_query = db.query(Slide).join(Document).filter(
        Document.owner_id == user_id,
        Document.is_deleted == False
    )
    
    if doc_ids:
        db_query = db_query.filter(Slide.document_id.in_(doc_ids))
    
    # 简单关键词匹配
    db_query = db_query.filter(Slide.content_text.ilike(f"%{query}%"))
    
    slides = db_query.limit(limit).all()
    
    return {
        "slides": [SlideResponse.model_validate(s) for s in slides],
        "total": len(slides),
        "query": query
    }


@router.get("/sections/{section_id}/recommendations", summary="获取章节推荐页面")
async def get_section_recommendations(
    section_id: str,
    limit: int = 10,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    根据章节内容推荐相关页面
    
    系统会分析章节的标题和描述，从文档库中推荐相关页面
    """
    section = db.query(OutlineSection).filter(
        OutlineSection.id == section_id
    ).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    # TODO: 使用章节信息进行语义搜索
    # 构建搜索查询
    search_query = f"{section.title} {section.description or ''} {section.content_hint or ''}"
    
    # 调用向量搜索
    # 目前使用简单的关键词搜索作为占位
    slides = db.query(Slide).join(Document).filter(
        Document.owner_id == user_id,
        Document.is_deleted == False,
        Slide.content_text.ilike(f"%{section.title}%")
    ).limit(limit).all()
    
    return {
        "section_id": section_id,
        "section_title": section.title,
        "recommendations": [SlideResponse.model_validate(s) for s in slides],
        "total": len(slides)
    }


@router.get("/slides/{slide_id}", response_model=SlideDetailResponse, summary="获取页面详情")
async def get_slide_detail(
    slide_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取页面详细信息"""
    slide = db.query(Slide).join(Document).filter(
        Slide.id == slide_id,
        Document.owner_id == user_id,
        Document.is_deleted == False
    ).first()
    
    if not slide:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="页面不存在"
        )
    
    return SlideDetailResponse.model_validate(slide)


@router.get("/slides/{slide_id}/similar", summary="获取相似页面")
async def get_similar_slides(
    slide_id: str,
    limit: int = 5,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取与指定页面相似的其他页面"""
    slide = db.query(Slide).join(Document).filter(
        Slide.id == slide_id,
        Document.owner_id == user_id,
        Document.is_deleted == False
    ).first()
    
    if not slide:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="页面不存在"
        )
    
    # TODO: 使用向量相似度搜索
    # 目前返回同文档的其他页面作为占位
    similar_slides = db.query(Slide).filter(
        Slide.document_id == slide.document_id,
        Slide.id != slide_id
    ).limit(limit).all()
    
    return {
        "source_slide_id": slide_id,
        "similar_slides": [SlideResponse.model_validate(s) for s in similar_slides]
    }


@router.post("/preview", summary="预览组装效果")
async def preview_assembly(
    slide_ids: List[str],
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    预览页面组装效果
    
    根据选择的页面 ID 列表，返回预览信息
    """
    slides = db.query(Slide).join(Document).filter(
        Slide.id.in_(slide_ids),
        Document.owner_id == user_id,
        Document.is_deleted == False
    ).all()
    
    # 保持传入的顺序
    slide_map = {s.id: s for s in slides}
    ordered_slides = [slide_map[sid] for sid in slide_ids if sid in slide_map]
    
    return {
        "slides": [SlideResponse.model_validate(s) for s in ordered_slides],
        "total_pages": len(ordered_slides),
        "missing_ids": [sid for sid in slide_ids if sid not in slide_map]
    }
