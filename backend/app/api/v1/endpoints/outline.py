"""
大纲设计 API
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.core import get_current_user_id
from app.models import Outline, OutlineSection, OutlineStatus, OutlineGenerationMode
from app.models.draft import Draft, DraftPage, DraftStatus
from app.schemas import (
    OutlineCreate,
    OutlineUpdate,
    OutlineResponse,
    OutlineDetailResponse,
    OutlineListResponse,
    OutlineSectionCreate,
    OutlineSectionUpdate,
    OutlineSectionResponse,
    SmartGenerateRequest,
    SmartGenerateResponse,
    IntelligentGenerateRequest,
    IntelligentGenerateResponse,
    WizardStep1Request,
    WizardStep1Response,
    WizardStep2Request,
    WizardStep2Response,
    WizardStep3Request,
    WizardStep3Response,
    ConfirmOutlineResponse,
    AutoSaveOutlineRequest,
    AutoSaveOutlineResponse,
)

router = APIRouter()


# ============== 大纲 CRUD ==============

@router.post("", response_model=OutlineResponse, summary="创建大纲")
async def create_outline(
    request: OutlineCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """创建新大纲"""
    outline = Outline(
        title=request.title,
        description=request.description,
        generation_mode=request.generation_mode,
        generation_config=request.generation_config,
        owner_id=user_id,
    )
    db.add(outline)
    db.commit()
    db.refresh(outline)
    
    return OutlineResponse.model_validate(outline)


@router.get("", response_model=OutlineListResponse, summary="获取大纲列表")
async def get_outlines(
    page: int = 1,
    limit: int = 20,
    status: Optional[OutlineStatus] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取用户的大纲列表"""
    query = db.query(Outline).filter(
        Outline.owner_id == user_id,
        Outline.is_deleted == False
    )
    
    if status:
        query = query.filter(Outline.status == status)
    
    total = query.count()
    outlines = query.order_by(Outline.created_at.desc()) \
        .offset((page - 1) * limit) \
        .limit(limit) \
        .all()
    
    return OutlineListResponse(
        outlines=[OutlineResponse.model_validate(o) for o in outlines],
        total=total
    )


@router.get("/{outline_id}", response_model=OutlineDetailResponse, summary="获取大纲详情")
async def get_outline(
    outline_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取大纲详情，包含章节树"""
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.owner_id == user_id,
        Outline.is_deleted == False
    ).first()
    
    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )
    
    # 获取章节并构建树形结构
    sections = db.query(OutlineSection).filter(
        OutlineSection.outline_id == outline_id
    ).order_by(OutlineSection.order_index).all()
    
    # TODO: 构建树形结构
    
    response = OutlineDetailResponse.model_validate(outline)
    response.sections = [OutlineSectionResponse.model_validate(s) for s in sections if s.parent_id is None]
    
    return response


@router.put("/{outline_id}", response_model=OutlineResponse, summary="更新大纲")
async def update_outline(
    outline_id: str,
    request: OutlineUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新大纲信息"""
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.owner_id == user_id,
        Outline.is_deleted == False
    ).first()
    
    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )
    
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(outline, field, value)
    
    db.commit()
    db.refresh(outline)
    
    return OutlineResponse.model_validate(outline)


@router.delete("/{outline_id}", summary="删除大纲")
async def delete_outline(
    outline_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """删除大纲"""
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.owner_id == user_id,
        Outline.is_deleted == False
    ).first()
    
    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )
    
    from datetime import datetime
    outline.is_deleted = True
    outline.deleted_at = datetime.utcnow()
    db.commit()
    
    return {"success": True}


# ============== 章节 CRUD ==============

@router.post("/{outline_id}/sections", response_model=OutlineSectionResponse, summary="添加章节")
async def add_section(
    outline_id: str,
    request: OutlineSectionCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """添加章节到大纲"""
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.owner_id == user_id,
        Outline.is_deleted == False
    ).first()
    
    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )
    
    # 计算排序索引
    max_order = db.query(OutlineSection).filter(
        OutlineSection.outline_id == outline_id,
        OutlineSection.parent_id == request.parent_id
    ).count()
    
    # 计算层级
    level = 1
    if request.parent_id:
        parent = db.query(OutlineSection).filter(
            OutlineSection.id == request.parent_id
        ).first()
        if parent:
            level = parent.level + 1
    
    section = OutlineSection(
        outline_id=outline_id,
        parent_id=request.parent_id,
        title=request.title,
        description=request.description,
        content_hint=request.content_hint,
        expected_pages=request.expected_pages,
        order_index=request.order_index if request.order_index is not None else max_order,
        level=level,
    )
    db.add(section)
    
    # 更新大纲章节数
    outline.section_count += 1
    
    db.commit()
    db.refresh(section)
    
    return OutlineSectionResponse.model_validate(section)


@router.put("/{outline_id}/sections/{section_id}", response_model=OutlineSectionResponse, summary="更新章节")
async def update_section(
    outline_id: str,
    section_id: str,
    request: OutlineSectionUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新章节信息"""
    section = db.query(OutlineSection).join(Outline).filter(
        OutlineSection.id == section_id,
        OutlineSection.outline_id == outline_id,
        Outline.owner_id == user_id
    ).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(section, field, value)
    
    db.commit()
    db.refresh(section)
    
    return OutlineSectionResponse.model_validate(section)


@router.delete("/{outline_id}/sections/{section_id}", summary="删除章节")
async def delete_section(
    outline_id: str,
    section_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """删除章节"""
    section = db.query(OutlineSection).join(Outline).filter(
        OutlineSection.id == section_id,
        OutlineSection.outline_id == outline_id,
        Outline.owner_id == user_id
    ).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="章节不存在"
        )
    
    outline = db.query(Outline).filter(Outline.id == outline_id).first()
    outline.section_count -= 1
    
    db.delete(section)
    db.commit()
    
    return {"success": True}


@router.post("/{outline_id}/sections/reorder", summary="重排章节顺序")
async def reorder_sections(
    outline_id: str,
    orders: List[dict],  # [{"section_id": "xxx", "order_index": 0, "parent_id": null}, ...]
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """批量更新章节顺序"""
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.owner_id == user_id,
        Outline.is_deleted == False
    ).first()
    
    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )
    
    for order in orders:
        section = db.query(OutlineSection).filter(
            OutlineSection.id == order["section_id"],
            OutlineSection.outline_id == outline_id
        ).first()
        if section:
            section.order_index = order["order_index"]
            if "parent_id" in order:
                section.parent_id = order["parent_id"]
    
    db.commit()
    
    return {"success": True}


# ============== 智能生成 ==============

@router.post("/smart-generate", response_model=SmartGenerateResponse, summary="智能生成大纲")
async def smart_generate(
    request: SmartGenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    智能生成大纲
    
    基于用户描述，自动生成结构化的大纲
    """
    import uuid
    
    # 创建大纲
    outline = Outline(
        title=f"智能生成的大纲",
        description=request.description,
        generation_mode=OutlineGenerationMode.INTELLIGENT,
        generation_config={"description": request.description},
        owner_id=user_id,
    )
    db.add(outline)
    db.commit()
    db.refresh(outline)
    
    # 根据描述生成章节（简化版，实际应调用 LLM）
    default_sections = [
        {"title": "引言", "description": "背景介绍", "expected_pages": 1},
        {"title": "核心内容", "description": "主要内容阐述", "expected_pages": 3},
        {"title": "详细分析", "description": "深入分析讨论", "expected_pages": 3},
        {"title": "案例展示", "description": "实际案例说明", "expected_pages": 2},
        {"title": "总结", "description": "总结与展望", "expected_pages": 1},
    ]
    
    for idx, section_data in enumerate(default_sections):
        section = OutlineSection(
            outline_id=outline.id,
            title=section_data["title"],
            description=section_data["description"],
            expected_pages=section_data["expected_pages"],
            order_index=idx,
            level=1,
        )
        db.add(section)
        outline.section_count += 1
    
    db.commit()
    db.refresh(outline)
    
    # 构建前端需要的响应格式
    outline_data = {
        "id": outline.id,
        "title": outline.title,
        "objective": request.description,
        "description": outline.description,
        "generation_type": "smart",
        "chapters": [
            {
                "id": str(uuid.uuid4()),
                "title": s.title,
                "summary": s.description or "",
                "page_count": s.expected_pages,
                "order": s.order_index + 1,
                "keywords": [],
            }
            for s in db.query(OutlineSection).filter(
                OutlineSection.outline_id == outline.id
            ).order_by(OutlineSection.order_index).all()
        ],
        "total_pages": sum(s.expected_pages for s in db.query(OutlineSection).filter(
            OutlineSection.outline_id == outline.id
        ).all()),
        "created_at": outline.created_at.isoformat(),
        "updated_at": outline.updated_at.isoformat(),
    }
    
    return SmartGenerateResponse(
        outline=outline_data,
        suggestions=["建议添加更多具体细节", "可以考虑增加案例说明"],
        confidence=0.85
    )


@router.post("/generate/intelligent", response_model=IntelligentGenerateResponse, summary="智能生成大纲")
async def intelligent_generate(
    request: IntelligentGenerateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    基于主题智能生成大纲
    
    使用 LLM 分析主题，自动生成结构化的大纲
    """
    # TODO: 调用 LLM 服务生成大纲
    # 这里先返回模拟数据
    
    outline = Outline(
        title=f"关于「{request.topic[:20]}...」的演示",
        description=request.topic,
        generation_mode=OutlineGenerationMode.INTELLIGENT,
        generation_config={
            "topic": request.topic,
            "page_count": request.page_count,
            "style": request.style,
        },
        owner_id=user_id,
    )
    db.add(outline)
    db.commit()
    db.refresh(outline)
    
    # TODO: 异步生成章节
    
    return IntelligentGenerateResponse(
        outline_id=outline.id,
        title=outline.title,
        sections=[]
    )


# ============== 向导式生成 ==============

@router.post("/generate/wizard/step1", response_model=WizardStep1Response, summary="向导第一步：分析主题")
async def wizard_step1(
    request: WizardStep1Request,
    user_id: str = Depends(get_current_user_id),
):
    """向导式生成 - 第一步：分析主题，返回建议"""
    # TODO: 调用 LLM 分析主题
    import uuid
    
    return WizardStep1Response(
        session_id=str(uuid.uuid4()),
        suggested_titles=[
            f"{request.topic} - 完整介绍",
            f"深入理解{request.topic}",
            f"{request.topic}实践指南",
        ],
        suggested_page_count=10
    )


@router.post("/generate/wizard/step2", response_model=WizardStep2Response, summary="向导第二步：生成章节建议")
async def wizard_step2(
    request: WizardStep2Request,
    user_id: str = Depends(get_current_user_id),
):
    """向导式生成 - 第二步：基于确认的标题和页数，生成章节建议"""
    # TODO: 调用 LLM 生成章节建议
    
    return WizardStep2Response(
        session_id=request.session_id,
        suggested_sections=[
            {"title": "引言", "description": "项目背景和目标", "expected_pages": 1},
            {"title": "核心概念", "description": "关键概念和术语", "expected_pages": 2},
            {"title": "详细分析", "description": "深入分析和讨论", "expected_pages": 4},
            {"title": "实践应用", "description": "实际案例和应用", "expected_pages": 2},
            {"title": "总结展望", "description": "总结和未来展望", "expected_pages": 1},
        ]
    )


@router.post("/generate/wizard/step3", response_model=WizardStep3Response, summary="向导第三步：创建大纲")
async def wizard_step3(
    request: WizardStep3Request,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """向导式生成 - 第三步：根据确认的章节创建大纲"""
    # TODO: 从会话中获取信息并创建大纲
    
    outline = Outline(
        title="向导生成的大纲",
        generation_mode=OutlineGenerationMode.WIZARD,
        generation_config={"session_id": request.session_id},
        owner_id=user_id,
    )
    db.add(outline)
    db.commit()
    db.refresh(outline)
    
    # 创建章节
    for idx, section_data in enumerate(request.sections):
        section = OutlineSection(
            outline_id=outline.id,
            title=section_data.get("title", f"章节 {idx + 1}"),
            description=section_data.get("description"),
            expected_pages=section_data.get("expected_pages", 1),
            order_index=idx,
            level=1,
        )
        db.add(section)
        outline.section_count += 1
    
    db.commit()
    db.refresh(outline)
    
    return WizardStep3Response(
        outline_id=outline.id,
        outline=OutlineDetailResponse.model_validate(outline)
    )


# ============== 大纲确认与保存 ==============

@router.post("/{outline_id}/confirm", response_model=ConfirmOutlineResponse, summary="确认大纲")
async def confirm_outline(
    outline_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    确认大纲，进入组装阶段
    
    将大纲状态更新为已完成，并自动创建一个组装草稿
    草稿会根据大纲章节自动创建对应的页面占位符
    """
    from datetime import datetime
    
    # 查询大纲
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.owner_id == user_id,
        Outline.is_deleted == False
    ).first()
    
    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )
    
    # 更新大纲状态为已完成
    outline.status = OutlineStatus.COMPLETED
    outline.updated_at = datetime.utcnow()
    
    # 创建组装草稿
    draft = Draft(
        title=outline.title,
        description=outline.description,
        outline_id=outline_id,
        status=DraftStatus.ASSEMBLING,
        owner_id=user_id,
    )
    db.add(draft)
    db.flush()  # 获取 draft.id
    
    # 获取大纲章节并创建对应的草稿页面
    sections = db.query(OutlineSection).filter(
        OutlineSection.outline_id == outline_id
    ).order_by(OutlineSection.order_index).all()
    
    page_order = 0
    total_pages = 0
    
    for section in sections:
        # 根据章节的 expected_pages 创建对应数量的页面占位符
        page_count = section.expected_pages or 1
        for i in range(page_count):
            page = DraftPage(
                draft_id=draft.id,
                title=f"{section.title} - 第{i+1}页" if page_count > 1 else section.title,
                section_id=section.id,
                order_index=page_order,
            )
            db.add(page)
            page_order += 1
            total_pages += 1
    
    # 更新草稿的总页数
    draft.page_count = total_pages
    
    db.commit()
    db.refresh(draft)
    
    return ConfirmOutlineResponse(
        success=True,
        assembly_draft_id=draft.id,
        message="大纲已确认，已创建组装草稿"
    )


@router.post("/{outline_id}/auto-save", response_model=AutoSaveOutlineResponse, summary="自动保存大纲")
async def auto_save_outline(
    outline_id: str,
    request: AutoSaveOutlineRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    自动保存大纲
    
    保存大纲的标题、描述和章节信息
    """
    from datetime import datetime
    
    # 查询大纲
    outline = db.query(Outline).filter(
        Outline.id == outline_id,
        Outline.owner_id == user_id,
        Outline.is_deleted == False
    ).first()
    
    if not outline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="大纲不存在"
        )
    
    # 更新大纲基本信息
    outline.title = request.title
    outline.description = request.description
    outline.updated_at = datetime.utcnow()
    
    # 更新章节信息
    if request.sections:
        # 获取现有章节
        existing_sections = db.query(OutlineSection).filter(
            OutlineSection.outline_id == outline_id
        ).all()
        existing_section_map = {s.id: s for s in existing_sections}
        
        # 更新或创建章节
        for idx, section_data in enumerate(request.sections):
            section_id = section_data.get("id")
            if section_id and section_id in existing_section_map:
                # 更新现有章节
                section = existing_section_map[section_id]
                section.title = section_data.get("title", section.title)
                section.description = section_data.get("summary", section.description)
                section.expected_pages = section_data.get("page_count", section.expected_pages)
                section.order_index = idx
            else:
                # 创建新章节
                new_section = OutlineSection(
                    outline_id=outline_id,
                    title=section_data.get("title", f"章节 {idx + 1}"),
                    description=section_data.get("summary"),
                    expected_pages=section_data.get("page_count", 1),
                    order_index=idx,
                    level=1,
                )
                db.add(new_section)
        
        # 更新章节数量
        outline.section_count = len(request.sections)
    
    db.commit()
    db.refresh(outline)
    
    return AutoSaveOutlineResponse(
        success=True,
        saved_at=outline.updated_at
    )
