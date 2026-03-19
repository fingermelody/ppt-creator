"""
智能图片推荐服务
"""

import re
import httpx
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.image import (
    ImageRecommendation, ImageLibrary, ImageUsage,
    ImageSource, ImageCategory
)
from app.core.config import settings


class ImageService:
    """智能图片推荐服务"""
    
    # 图片源配置
    UNSPLASH_API_URL = "https://api.unsplash.com"
    PEXELS_API_URL = "https://api.pexels.com/v1"
    PIXABAY_API_URL = "https://pixabay.com/api"
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_recommendations(
        self,
        page_id: str,
        user_id: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        style: Optional[str] = None,
        count: int = 10,
    ) -> Dict[str, Any]:
        """
        获取智能图片推荐
        
        Args:
            page_id: 页面ID
            user_id: 用户ID
            content: 页面内容
            title: 页面标题
            keywords: 关键词列表
            style: 风格偏好
            count: 推荐数量
        
        Returns:
            推荐结果
        """
        # 提取关键词
        extracted_keywords = self._extract_keywords(content, title, keywords)
        
        # 从多个源获取图片
        images = []
        
        # 从 Unsplash 获取
        unsplash_images = await self._fetch_from_unsplash(
            extracted_keywords, 
            count=count // 2
        )
        images.extend(unsplash_images)
        
        # 从 Pexels 获取
        pexels_images = await self._fetch_from_pexels(
            extracted_keywords,
            count=count // 2
        )
        images.extend(pexels_images)
        
        # 按相关性排序
        images = self._rank_by_relevance(images, extracted_keywords)
        
        # 保存推荐记录
        recommendation = ImageRecommendation(
            page_id=page_id,
            user_id=user_id,
            images=[{
                "url": img.get("url"),
                "source": img.get("source"),
            } for img in images[:count]],
            search_keywords=extracted_keywords,
            content_context=content[:500] if content else None,
        )
        self.db.add(recommendation)
        self.db.commit()
        
        return {
            "images": images[:count],
            "keywords_used": extracted_keywords,
            "total": len(images),
        }
    
    def _extract_keywords(
        self,
        content: Optional[str],
        title: Optional[str],
        keywords: Optional[List[str]],
    ) -> List[str]:
        """从内容中提取关键词"""
        extracted = set()
        
        # 使用提供的关键词
        if keywords:
            extracted.update(keywords)
        
        # 从标题提取
        if title:
            # 简单分词
            words = re.findall(r'\b\w+\b', title.lower())
            # 过滤常见词
            stop_words = {'的', '和', '是', '在', '了', 'the', 'a', 'an', 'is', 'are', 'and', 'or'}
            words = [w for w in words if w not in stop_words and len(w) > 1]
            extracted.update(words[:5])
        
        # 从内容提取（简化版）
        if content:
            # 可以接入更复杂的 NLP 关键词提取
            words = re.findall(r'\b\w+\b', content.lower())
            from collections import Counter
            word_freq = Counter(words)
            # 取频率最高的词
            stop_words = {'的', '和', '是', '在', '了', 'the', 'a', 'an', 'is', 'are', 'and', 'or', 'to', 'for'}
            top_words = [
                word for word, _ in word_freq.most_common(20)
                if word not in stop_words and len(word) > 2
            ][:5]
            extracted.update(top_words)
        
        return list(extracted)[:10]
    
    async def _fetch_from_unsplash(
        self,
        keywords: List[str],
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """从 Unsplash 获取图片"""
        images = []
        
        try:
            query = " ".join(keywords[:3])
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.UNSPLASH_API_URL}/search/photos",
                    params={
                        "query": query,
                        "per_page": count,
                        "orientation": "landscape",
                    },
                    headers={
                        "Authorization": f"Client-ID {getattr(settings, 'UNSPLASH_ACCESS_KEY', '')}"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for photo in data.get("results", []):
                        images.append({
                            "url": photo.get("urls", {}).get("regular", ""),
                            "thumbnail_url": photo.get("urls", {}).get("thumb", ""),
                            "source": "unsplash",
                            "source_id": photo.get("id"),
                            "title": photo.get("description") or photo.get("alt_description"),
                            "description": photo.get("alt_description"),
                            "alt_text": photo.get("alt_description"),
                            "width": photo.get("width"),
                            "height": photo.get("height"),
                            "relevance_score": 0.8,
                            "keywords_matched": keywords[:3],
                        })
        except Exception as e:
            print(f"Unsplash fetch error: {e}")
        
        return images
    
    async def _fetch_from_pexels(
        self,
        keywords: List[str],
        count: int = 10,
    ) -> List[Dict[str, Any]]:
        """从 Pexels 获取图片"""
        images = []
        
        try:
            query = " ".join(keywords[:3])
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.PEXELS_API_URL}/search",
                    params={
                        "query": query,
                        "per_page": count,
                        "orientation": "landscape",
                    },
                    headers={
                        "Authorization": getattr(settings, 'PEXELS_API_KEY', '')
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for photo in data.get("photos", []):
                        images.append({
                            "url": photo.get("src", {}).get("large", ""),
                            "thumbnail_url": photo.get("src", {}).get("medium", ""),
                            "source": "pexels",
                            "source_id": str(photo.get("id")),
                            "title": photo.get("alt"),
                            "description": photo.get("alt"),
                            "alt_text": photo.get("alt"),
                            "width": photo.get("width"),
                            "height": photo.get("height"),
                            "relevance_score": 0.7,
                            "keywords_matched": keywords[:3],
                        })
        except Exception as e:
            print(f"Pexels fetch error: {e}")
        
        return images
    
    def _rank_by_relevance(
        self,
        images: List[Dict[str, Any]],
        keywords: List[str],
    ) -> List[Dict[str, Any]]:
        """按相关性排序"""
        for img in images:
            score = img.get("relevance_score", 0.5)
            
            # 根据匹配的关键词数量调整分数
            matched = img.get("keywords_matched", [])
            if matched:
                score += len(matched) * 0.1
            
            # 根据图片尺寸调整（更大的图片通常更清晰）
            width = img.get("width", 0)
            if width > 1920:
                score += 0.1
            
            img["relevance_score"] = min(score, 1.0)
        
        return sorted(images, key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    async def search_images(
        self,
        query: str,
        user_id: str,
        source: Optional[str] = None,
        category: Optional[str] = None,
        orientation: Optional[str] = None,
        color: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """搜索图片"""
        images = []
        
        # 搜索用户图片库
        if not source or source == "library":
            library_images = self._search_library(
                user_id, query, category, page, page_size
            )
            for img in library_images:
                images.append({
                    "url": img.url,
                    "thumbnail_url": img.thumbnail_url,
                    "source": "library",
                    "source_id": img.id,
                    "title": img.title,
                    "description": img.description,
                    "alt_text": img.alt_text,
                    "width": img.width,
                    "height": img.height,
                    "relevance_score": 0.9,
                    "keywords_matched": [],
                })
        
        # 搜索外部源
        if not source or source in ["unsplash", "all"]:
            unsplash_images = await self._fetch_from_unsplash([query], page_size // 2)
            images.extend(unsplash_images)
        
        if not source or source in ["pexels", "all"]:
            pexels_images = await self._fetch_from_pexels([query], page_size // 2)
            images.extend(pexels_images)
        
        return {
            "images": images[:page_size],
            "total": len(images),
            "page": page,
            "page_size": page_size,
            "query": query,
        }
    
    def _search_library(
        self,
        user_id: str,
        query: str,
        category: Optional[str],
        page: int,
        page_size: int,
    ) -> List[ImageLibrary]:
        """搜索用户图片库"""
        db_query = self.db.query(ImageLibrary).filter(
            ImageLibrary.user_id == user_id
        )
        
        # 搜索标题和描述
        if query:
            db_query = db_query.filter(
                ImageLibrary.title.ilike(f"%{query}%") |
                ImageLibrary.description.ilike(f"%{query}%")
            )
        
        # 分类筛选
        if category:
            try:
                category_enum = ImageCategory(category)
                db_query = db_query.filter(ImageLibrary.category == category_enum)
            except ValueError:
                pass
        
        return db_query.offset((page - 1) * page_size).limit(page_size).all()
    
    def get_library_images(
        self,
        user_id: str,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[ImageLibrary], int]:
        """获取用户图片库"""
        query = self.db.query(ImageLibrary).filter(
            ImageLibrary.user_id == user_id
        )
        
        if category:
            try:
                category_enum = ImageCategory(category)
                query = query.filter(ImageLibrary.category == category_enum)
            except ValueError:
                pass
        
        total = query.count()
        images = query.order_by(
            ImageLibrary.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        return images, total
    
    def save_to_library(
        self,
        user_id: str,
        url: str,
        source: str = "upload",
        source_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: str = "other",
        width: Optional[int] = None,
        height: Optional[int] = None,
        file_size: Optional[int] = None,
    ) -> ImageLibrary:
        """保存图片到用户库"""
        try:
            source_enum = ImageSource(source)
        except ValueError:
            source_enum = ImageSource.UPLOAD
        
        try:
            category_enum = ImageCategory(category)
        except ValueError:
            category_enum = ImageCategory.OTHER
        
        image = ImageLibrary(
            user_id=user_id,
            url=url,
            source=source_enum,
            source_id=source_id,
            title=title,
            description=description,
            tags=tags,
            category=category_enum,
            width=width,
            height=height,
            file_size=file_size,
        )
        
        self.db.add(image)
        self.db.commit()
        self.db.refresh(image)
        
        return image
    
    def record_usage(
        self,
        user_id: str,
        page_id: str,
        image_id: Optional[str] = None,
        image_url: Optional[str] = None,
        element_id: Optional[str] = None,
    ) -> ImageUsage:
        """记录图片使用"""
        usage = ImageUsage(
            user_id=user_id,
            page_id=page_id,
            image_id=image_id,
            image_url=image_url,
            element_id=element_id,
        )
        
        self.db.add(usage)
        
        # 如果是库中的图片，增加使用次数
        if image_id:
            image = self.db.query(ImageLibrary).filter(
                ImageLibrary.id == image_id
            ).first()
            if image:
                image.use_count += 1
        
        self.db.commit()
        self.db.refresh(usage)
        
        return usage
    
    def delete_from_library(self, image_id: str, user_id: str) -> bool:
        """从图片库删除"""
        image = self.db.query(ImageLibrary).filter(
            ImageLibrary.id == image_id,
            ImageLibrary.user_id == user_id
        ).first()
        
        if not image:
            return False
        
        self.db.delete(image)
        self.db.commit()
        return True
