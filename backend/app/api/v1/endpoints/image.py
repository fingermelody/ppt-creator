"""
智能图片推荐 API
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.db import get_db
from app.core import get_current_user_id
from app.models import RefinementTask, RefinedPage
from app.services.image import ImageService
from app.schemas.image import (
    GetRecommendationsRequest, RecommendationsResponse, RecommendedImage,
    SearchImagesRequest, SearchImagesResponse,
    ImageLibraryResponse, ImageInfo, ImageDetailResponse,
    UploadImageRequest, UploadImageResponse,
    InsertImageRequest, InsertImageResponse,
    AnalyzeImageRequest, ImageAnalysisResponse,
)

router = APIRouter()


@router.post("/tasks/{task_id}/pages/{page_index}/images/recommend", 
             response_model=RecommendationsResponse, 
             summary="获取智能图片推荐")
async def get_recommendations(
    task_id: str,
    page_index: int,
    request: GetRecommendationsRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """根据页面内容智能推荐相关图片"""
    # 验证任务和页面
    page = db.query(RefinedPage).join(RefinementTask).filter(
        RefinedPage.task_id == task_id,
        RefinedPage.page_index == page_index,
        RefinementTask.owner_id == user_id
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    service = ImageService(db)
    result = await service.get_recommendations(
        page_id=page.id,
        user_id=user_id,
        content=request.content,
        title=request.title or page.title,
        keywords=request.keywords,
        style=request.style,
        count=request.count,
    )
    
    return RecommendationsResponse(
        images=[
            RecommendedImage(**img) for img in result["images"]
        ],
        keywords_used=result["keywords_used"],
        total=result["total"],
    )


@router.post("/images/search", response_model=SearchImagesResponse, summary="搜索图片")
async def search_images(
    request: SearchImagesRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """搜索图片（包括用户库和外部源）"""
    service = ImageService(db)
    result = await service.search_images(
        query=request.query,
        user_id=user_id,
        source=request.source,
        category=request.category,
        orientation=request.orientation,
        color=request.color,
        page=request.page,
        page_size=request.page_size,
    )
    
    return SearchImagesResponse(
        images=[RecommendedImage(**img) for img in result["images"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        query=result["query"],
    )


@router.get("/images/library", response_model=ImageLibraryResponse, summary="获取图片库")
async def get_library(
    category: Optional[str] = Query(None, description="分类筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取用户的图片库"""
    service = ImageService(db)
    images, total = service.get_library_images(
        user_id=user_id,
        category=category,
        page=page,
        page_size=page_size,
    )
    
    return ImageLibraryResponse(
        images=[
            ImageInfo(
                id=img.id,
                url=img.url,
                thumbnail_url=img.thumbnail_url,
                source=img.source.value,
                title=img.title,
                description=img.description,
                alt_text=img.alt_text,
                width=img.width,
                height=img.height,
                tags=img.tags,
            )
            for img in images
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/images/library", response_model=UploadImageResponse, summary="上传图片到库")
async def upload_image(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None,
    category: str = "other",
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """上传图片到用户库"""
    # 验证文件类型
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的图片格式")
    
    # TODO: 实现实际的文件上传逻辑
    # 1. 上传到云存储
    # 2. 生成缩略图
    # 3. 获取图片尺寸
    
    # 临时实现
    image_url = f"/uploads/images/{uuid.uuid4()}/{file.filename}"
    
    service = ImageService(db)
    image = service.save_to_library(
        user_id=user_id,
        url=image_url,
        source="upload",
        title=title,
        description=description,
        category=category,
    )
    
    return UploadImageResponse(
        success=True,
        image_id=image.id,
        url=image.url,
        thumbnail_url=image.thumbnail_url,
    )


@router.get("/images/library/{image_id}", response_model=ImageDetailResponse, summary="获取图片详情")
async def get_image_detail(
    image_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """获取图片详情"""
    from app.models.image import ImageLibrary
    
    image = db.query(ImageLibrary).filter(
        ImageLibrary.id == image_id,
        ImageLibrary.user_id == user_id
    ).first()
    
    if not image:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    return ImageDetailResponse(
        id=image.id,
        url=image.url,
        thumbnail_url=image.thumbnail_url,
        source=image.source.value,
        title=image.title,
        description=image.description,
        alt_text=image.alt_text,
        width=image.width,
        height=image.height,
        tags=image.tags,
        ai_tags=image.ai_tags,
        ai_description=image.ai_description,
        color_palette=image.color_palette,
        use_count=image.use_count,
        created_at=image.created_at,
    )


@router.delete("/images/library/{image_id}", summary="删除图片")
async def delete_image(
    image_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """从图片库删除图片"""
    service = ImageService(db)
    success = service.delete_from_library(image_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    return {"success": True, "message": "图片已删除"}


@router.post("/tasks/{task_id}/pages/{page_index}/images/insert", 
             response_model=InsertImageResponse, 
             summary="插入图片到页面")
async def insert_image(
    task_id: str,
    page_index: int,
    request: InsertImageRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """插入图片到指定页面"""
    # 验证任务和页面
    page = db.query(RefinedPage).join(RefinementTask).filter(
        RefinedPage.task_id == task_id,
        RefinedPage.page_index == page_index,
        RefinementTask.owner_id == user_id
    ).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="页面不存在")
    
    # 记录图片使用
    service = ImageService(db)
    element_id = str(uuid.uuid4())
    
    service.record_usage(
        user_id=user_id,
        page_id=page.id,
        image_id=request.image_id,
        image_url=request.image_url,
        element_id=element_id,
    )
    
    # TODO: 实际将图片添加到页面元素中
    
    return InsertImageResponse(
        success=True,
        element_id=element_id,
        modification_id=str(uuid.uuid4()),
    )


@router.post("/images/analyze", response_model=ImageAnalysisResponse, summary="分析图片")
async def analyze_image(
    request: AnalyzeImageRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """AI 分析图片内容"""
    # TODO: 接入 AI 图片分析服务
    # 可以使用腾讯云的图片标签、图片描述等 API
    
    return ImageAnalysisResponse(
        tags=["示例标签1", "示例标签2"],
        description="这是一张示例图片的描述",
        colors=[
            {"hex": "#3498db", "percentage": 30},
            {"hex": "#2ecc71", "percentage": 25},
        ],
        category="other",
        objects=["对象1", "对象2"],
    )


@router.post("/images/save-external", response_model=UploadImageResponse, summary="保存外部图片")
async def save_external_image(
    url: str,
    source: str,
    source_id: Optional[str] = None,
    title: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """保存外部图片到用户库"""
    service = ImageService(db)
    image = service.save_to_library(
        user_id=user_id,
        url=url,
        source=source,
        source_id=source_id,
        title=title,
    )
    
    return UploadImageResponse(
        success=True,
        image_id=image.id,
        url=image.url,
        thumbnail_url=image.thumbnail_url,
    )
