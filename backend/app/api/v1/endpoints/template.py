"""
模板系统 API
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.db import get_db
from app.core import get_current_user_id
from app.services.template import TemplateService
from app.schemas.template import (
    CreateTemplateRequest, CreateTemplateResponse,
    UpdateTemplateRequest, ApplyTemplateRequest, ApplyTemplateResponse,
    TemplateListResponse, TemplateInfo, TemplateDetailResponse, TemplatePageInfo,
    UploadTemplateResponse, TemplateCategoriesResponse, TemplateCategoryInfo,
    FavoriteResponse,
)

router = APIRouter()


@router.get("", response_model=TemplateListResponse, summary="获取模板列表")
async def get_templates(
    category: Optional[str] = Query(None, description="分类筛选"),
    is_system: Optional[bool] = Query(None, description="是否系统模板"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取公开的模板列表"""
    service = TemplateService(db)
    templates, total = service.get_templates(
        user_id=user_id,
        category=category,
        is_public=True,
        is_system=is_system,
        search=search,
        page=page,
        page_size=page_size,
    )
    
    return TemplateListResponse(
        templates=[
            TemplateInfo(
                id=t.id,
                name=t.name,
                description=t.description,
                category=t.category.value,
                status=t.status.value,
                is_system=t.is_system,
                is_public=t.is_public,
                thumbnail_url=t.thumbnail_url,
                preview_images=t.preview_images,
                file_size=t.file_size,
                use_count=t.use_count,
                like_count=t.like_count,
                tags=t.tags,
                creator_id=t.creator_id,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/categories", response_model=TemplateCategoriesResponse, summary="获取模板分类")
async def get_categories(db: Session = Depends(get_db)):
    """获取所有模板分类及统计"""
    service = TemplateService(db)
    categories = service.get_categories()
    
    return TemplateCategoriesResponse(
        categories=[
            TemplateCategoryInfo(**cat)
            for cat in categories
        ]
    )


@router.get("/my", response_model=TemplateListResponse, summary="获取我的模板")
async def get_my_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取当前用户创建的模板"""
    service = TemplateService(db)
    templates, total = service.get_user_templates(user_id, page, page_size)
    
    return TemplateListResponse(
        templates=[
            TemplateInfo(
                id=t.id,
                name=t.name,
                description=t.description,
                category=t.category.value,
                status=t.status.value,
                is_system=t.is_system,
                is_public=t.is_public,
                thumbnail_url=t.thumbnail_url,
                preview_images=t.preview_images,
                file_size=t.file_size,
                use_count=t.use_count,
                like_count=t.like_count,
                tags=t.tags,
                creator_id=t.creator_id,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/favorites", response_model=TemplateListResponse, summary="获取收藏的模板")
async def get_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取用户收藏的模板"""
    service = TemplateService(db)
    templates, total = service.get_user_favorites(user_id, page, page_size)
    
    return TemplateListResponse(
        templates=[
            TemplateInfo(
                id=t.id,
                name=t.name,
                description=t.description,
                category=t.category.value,
                status=t.status.value,
                is_system=t.is_system,
                is_public=t.is_public,
                thumbnail_url=t.thumbnail_url,
                preview_images=t.preview_images,
                file_size=t.file_size,
                use_count=t.use_count,
                like_count=t.like_count,
                tags=t.tags,
                creator_id=t.creator_id,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
            for t in templates
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=CreateTemplateResponse, summary="创建模板")
async def create_template(
    request: CreateTemplateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """创建新模板"""
    service = TemplateService(db)
    template = service.create_template(
        name=request.name,
        creator_id=user_id,
        description=request.description,
        category=request.category,
        tags=request.tags,
        is_public=request.is_public,
        config=request.config,
    )
    
    return CreateTemplateResponse(
        success=True,
        template_id=template.id,
        created_at=template.created_at,
    )


@router.get("/{template_id}", response_model=TemplateDetailResponse, summary="获取模板详情")
async def get_template_detail(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取模板详情"""
    service = TemplateService(db)
    template = service.get_template_detail(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 检查访问权限
    if not template.is_public and template.creator_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问该模板")
    
    return TemplateDetailResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category.value,
        status=template.status.value,
        is_system=template.is_system,
        is_public=template.is_public,
        thumbnail_url=template.thumbnail_url,
        preview_images=template.preview_images,
        file_size=template.file_size,
        use_count=template.use_count,
        like_count=template.like_count,
        tags=template.tags,
        creator_id=template.creator_id,
        created_at=template.created_at,
        updated_at=template.updated_at,
        pages=[
            TemplatePageInfo(
                id=p.id,
                order_index=p.order_index,
                name=p.name,
                layout_type=p.layout_type,
                thumbnail_url=p.thumbnail_url,
            )
            for p in template.pages
        ] if template.pages else [],
        config=template.config,
        layouts=template.layouts,
    )


@router.put("/{template_id}", response_model=TemplateInfo, summary="更新模板")
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """更新模板信息"""
    service = TemplateService(db)
    template = service.update_template(
        template_id=template_id,
        user_id=user_id,
        name=request.name,
        description=request.description,
        category=request.category,
        tags=request.tags,
        is_public=request.is_public,
        config=request.config,
    )
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或无权修改")
    
    return TemplateInfo(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category.value,
        status=template.status.value,
        is_system=template.is_system,
        is_public=template.is_public,
        thumbnail_url=template.thumbnail_url,
        preview_images=template.preview_images,
        file_size=template.file_size,
        use_count=template.use_count,
        like_count=template.like_count,
        tags=template.tags,
        creator_id=template.creator_id,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.delete("/{template_id}", summary="删除模板")
async def delete_template(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """删除模板"""
    service = TemplateService(db)
    success = service.delete_template(template_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="模板不存在或无权删除")
    
    return {"success": True, "message": "模板已删除"}


@router.post("/{template_id}/publish", response_model=TemplateInfo, summary="发布模板")
async def publish_template(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """发布模板"""
    service = TemplateService(db)
    template = service.publish_template(template_id, user_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或无权发布")
    
    return TemplateInfo(
        id=template.id,
        name=template.name,
        description=template.description,
        category=template.category.value,
        status=template.status.value,
        is_system=template.is_system,
        is_public=template.is_public,
        thumbnail_url=template.thumbnail_url,
        preview_images=template.preview_images,
        file_size=template.file_size,
        use_count=template.use_count,
        like_count=template.like_count,
        tags=template.tags,
        creator_id=template.creator_id,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.post("/{template_id}/apply", response_model=ApplyTemplateResponse, summary="应用模板")
async def apply_template(
    template_id: str,
    request: ApplyTemplateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """应用模板到目标"""
    service = TemplateService(db)
    
    try:
        result = service.apply_template(
            template_id=template_id,
            user_id=user_id,
            target_type=request.target_type,
            target_id=request.target_id,
        )
        
        return ApplyTemplateResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{template_id}/favorite", response_model=FavoriteResponse, summary="收藏模板")
async def favorite_template(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """收藏模板"""
    service = TemplateService(db)
    service.add_favorite(user_id, template_id)
    
    template = service.get_template_detail(template_id)
    
    return FavoriteResponse(
        success=True,
        is_favorited=True,
        total_favorites=template.like_count if template else 0,
    )


@router.delete("/{template_id}/favorite", response_model=FavoriteResponse, summary="取消收藏")
async def unfavorite_template(
    template_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """取消收藏模板"""
    service = TemplateService(db)
    service.remove_favorite(user_id, template_id)
    
    template = service.get_template_detail(template_id)
    
    return FavoriteResponse(
        success=True,
        is_favorited=False,
        total_favorites=template.like_count if template else 0,
    )


@router.post("/{template_id}/upload", response_model=UploadTemplateResponse, summary="上传模板文件")
async def upload_template_file(
    template_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """上传模板 PPTX 文件"""
    service = TemplateService(db)
    template = service.get_template_detail(template_id)
    
    if not template or template.creator_id != user_id:
        raise HTTPException(status_code=404, detail="模板不存在或无权操作")
    
    # 验证文件类型
    if not file.filename.endswith('.pptx'):
        raise HTTPException(status_code=400, detail="只支持 PPTX 格式")
    
    # TODO: 实现文件上传逻辑
    # 1. 保存文件到存储
    # 2. 解析 PPTX 提取页面
    # 3. 生成缩略图
    
    return UploadTemplateResponse(
        success=True,
        template_id=template_id,
        file_path=f"/templates/{template_id}/{file.filename}",
        file_size=0,
        pages_count=0,
        thumbnail_url=None,
    )
