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
from app.models.draft import Draft, DraftPage
from app.schemas import SlideResponse, SlideDetailResponse
from app.services.slide_recommendation import get_slide_recommendation_service

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
    doc_id_list = document_ids.split(",") if document_ids else None
    
    # 使用推荐服务搜索
    recommendation_service = get_slide_recommendation_service()
    slides = recommendation_service.search_slides_by_keywords(
        db=db,
        query=query,
        user_id=user_id,
        limit=limit,
        document_ids=doc_id_list
    )
    
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
    
    # 使用推荐服务
    recommendation_service = get_slide_recommendation_service()
    recommendations = recommendation_service.recommend_slides_for_section(
        db=db,
        section_title=section.title,
        section_description=section.description,
        user_id=user_id,
        limit=limit
    )
    
    return {
        "section_id": section_id,
        "section_title": section.title,
        "recommendations": recommendations,
        "total": len(recommendations)
    }


@router.post("/drafts/{draft_id}/auto-match", summary="为草稿自动匹配页面")
async def auto_match_draft_pages(
    draft_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    为草稿的所有章节自动匹配推荐页面
    
    根据章节的标题和描述，从素材库中检索最相关的页面，
    并将推荐的页面关联到草稿页面
    """
    # 获取草稿
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
    
    if not draft.outline_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="草稿没有关联大纲，无法自动匹配"
        )
    
    # 获取章节信息
    sections = db.query(OutlineSection).filter(
        OutlineSection.outline_id == draft.outline_id
    ).order_by(OutlineSection.order_index).all()
    
    if not sections:
        return {
            "success": True,
            "message": "没有章节需要匹配",
            "matched_count": 0
        }
    
    # 使用推荐服务批量推荐
    recommendation_service = get_slide_recommendation_service()
    sections_data = [
        {
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "expected_pages": s.expected_pages or 1
        }
        for s in sections
    ]
    
    recommendations = recommendation_service.batch_recommend_for_draft(
        db=db,
        draft_id=draft_id,
        sections=sections_data,
        user_id=user_id
    )
    
    # 更新草稿页面
    matched_count = 0
    for section_id, section_recs in recommendations.items():
        # 获取该章节的草稿页面
        section_pages = db.query(DraftPage).filter(
            DraftPage.draft_id == draft_id,
            DraftPage.section_id == section_id,
            DraftPage.source_slide_id == None  # 只更新未绑定的页面
        ).order_by(DraftPage.order_index).all()
        
        # 将推荐的页面绑定到草稿页面
        for i, page in enumerate(section_pages):
            if i < len(section_recs):
                rec = section_recs[i]
                page.source_slide_id = rec["slide_id"]
                page.thumbnail_path = rec.get("thumbnail_path")
                page.title = rec.get("title") or page.title
                matched_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "message": f"成功匹配 {matched_count} 个页面",
        "matched_count": matched_count,
        "recommendations": recommendations
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
    
    # 使用页面的标题和内容搜索相似页面
    recommendation_service = get_slide_recommendation_service()
    search_query = f"{slide.title or ''} {slide.content_text or ''}"[:500]
    
    recommendations = recommendation_service.recommend_slides_for_section(
        db=db,
        section_title=slide.title or "",
        section_description=slide.content_text or "",
        user_id=user_id,
        limit=limit + 1  # 多取一个，排除自身
    )
    
    # 过滤掉自身
    similar_slides = [r for r in recommendations if r["slide_id"] != slide_id][:limit]
    
    return {
        "source_slide_id": slide_id,
        "similar_slides": similar_slides
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
