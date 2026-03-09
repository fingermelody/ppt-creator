"""
PPT 页面智能推荐服务

根据章节标题和描述，从素材库中检索最相关的 PPT 页面
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from app.models import Slide, Document

logger = logging.getLogger(__name__)


class SlideRecommendationService:
    """PPT 页面智能推荐服务"""
    
    def __init__(self):
        self._vectorization_service = None
        self._vector_enabled = False
        
        # 尝试初始化向量化服务
        try:
            from app.services.vectorization import get_vectorization_service
            self._vectorization_service = get_vectorization_service()
            self._vector_enabled = self._vectorization_service.enabled
        except Exception as e:
            logger.warning(f"向量化服务不可用: {e}")
    
    def search_slides_by_keywords(
        self,
        db: Session,
        query: str,
        user_id: str,
        limit: int = 10,
        document_ids: Optional[List[str]] = None
    ) -> List[Slide]:
        """
        基于关键词搜索页面
        
        Args:
            db: 数据库会话
            query: 搜索查询
            user_id: 用户 ID
            limit: 返回结果数量
            document_ids: 限制搜索的文档 ID 列表
        
        Returns:
            匹配的页面列表
        """
        if not query or not query.strip():
            return []
        
        # 分词处理
        keywords = query.replace('，', ' ').replace(',', ' ').split()
        keywords = [k.strip() for k in keywords if k.strip() and len(k.strip()) >= 2]
        
        if not keywords:
            # 如果没有有效关键词，返回一些默认页面
            return self._get_default_slides(db, user_id, limit, document_ids)
        
        # 构建基础查询
        base_query = db.query(Slide).join(Document).filter(
            Document.owner_id == user_id,
            Document.is_deleted == False
        )
        
        # 添加文档过滤
        if document_ids:
            base_query = base_query.filter(Slide.document_id.in_(document_ids))
        
        # 尝试使用多个关键词的 OR 匹配
        keyword_conditions = []
        for keyword in keywords[:5]:  # 最多使用5个关键词
            keyword_conditions.append(Slide.title.ilike(f"%{keyword}%"))
            keyword_conditions.append(Slide.content_text.ilike(f"%{keyword}%"))
        
        if keyword_conditions:
            slides = base_query.filter(or_(*keyword_conditions)).limit(limit).all()
            if slides:
                return slides
        
        # 如果没有匹配结果，尝试单个关键词匹配
        for keyword in keywords:
            single_result = base_query.filter(
                or_(
                    Slide.title.ilike(f"%{keyword}%"),
                    Slide.content_text.ilike(f"%{keyword}%")
                )
            ).limit(limit).all()
            if single_result:
                return single_result
        
        # 如果仍然没有结果，返回默认页面
        return self._get_default_slides(db, user_id, limit, document_ids)
    
    def _get_default_slides(
        self,
        db: Session,
        user_id: str,
        limit: int,
        document_ids: Optional[List[str]] = None
    ) -> List[Slide]:
        """获取默认页面（当没有匹配时使用）"""
        query = db.query(Slide).join(Document).filter(
            Document.owner_id == user_id,
            Document.is_deleted == False
        )
        
        if document_ids:
            query = query.filter(Slide.document_id.in_(document_ids))
        
        # 优先返回有标题的页面
        query = query.filter(Slide.title != None, Slide.title != '')
        
        return query.order_by(Slide.page_number).limit(limit).all()
    
    def recommend_slides_for_section(
        self,
        db: Session,
        section_title: str,
        section_description: Optional[str],
        user_id: str,
        limit: int = 5,
        document_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        为章节推荐相关页面
        
        Args:
            db: 数据库会话
            section_title: 章节标题
            section_description: 章节描述
            user_id: 用户 ID
            limit: 返回结果数量
            document_ids: 限制搜索的文档 ID 列表
        
        Returns:
            推荐页面列表（包含相似度分数）
        """
        # 构建搜索查询
        query_parts = [section_title]
        if section_description:
            query_parts.append(section_description)
        
        search_query = " ".join(query_parts)
        
        # 尝试使用向量搜索
        if self._vector_enabled:
            try:
                results = self._vectorization_service.search_similar_slides(
                    query=search_query,
                    n_results=limit
                )
                
                if results:
                    # 获取页面详情
                    slide_ids = [r["metadata"].get("slide_id") for r in results if r.get("metadata")]
                    slide_ids = [sid for sid in slide_ids if sid]
                    
                    if slide_ids:
                        slides_map = {}
                        slides = db.query(Slide).filter(Slide.id.in_(slide_ids)).all()
                        for slide in slides:
                            slides_map[slide.id] = slide
                        
                        recommendations = []
                        for r in results:
                            slide_id = r["metadata"].get("slide_id")
                            if slide_id and slide_id in slides_map:
                                slide = slides_map[slide_id]
                                # 计算相似度分数（距离越小越相似）
                                distance = r.get("distance", 1)
                                similarity = max(0, min(100, (1 - distance) * 100))
                                
                                recommendations.append({
                                    "slide_id": slide.id,
                                    "document_id": slide.document_id,
                                    "page_number": slide.page_number,
                                    "title": slide.title,
                                    "content_summary": (slide.content_text or "")[:200],
                                    "thumbnail_path": slide.thumbnail_path,
                                    "similarity": similarity,
                                })
                        
                        if recommendations:
                            return recommendations
            except Exception as e:
                logger.warning(f"向量搜索失败，回退到关键词搜索: {e}")
        
        # 回退到关键词搜索
        slides = self.search_slides_by_keywords(
            db=db,
            query=search_query,
            user_id=user_id,
            limit=limit,
            document_ids=document_ids
        )
        
        # 计算简单的相似度分数
        recommendations = []
        for idx, slide in enumerate(slides):
            # 基于排序位置计算假的相似度分数
            similarity = max(10, 95 - idx * 10)
            
            recommendations.append({
                "slide_id": slide.id,
                "document_id": slide.document_id,
                "page_number": slide.page_number,
                "title": slide.title,
                "content_summary": (slide.content_text or "")[:200],
                "thumbnail_path": slide.thumbnail_path,
                "similarity": similarity,
            })
        
        return recommendations
    
    def batch_recommend_for_draft(
        self,
        db: Session,
        draft_id: str,
        sections: List[Dict[str, Any]],
        user_id: str,
        pages_per_section: Optional[Dict[str, int]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        为草稿的所有章节批量推荐页面
        
        Args:
            db: 数据库会话
            draft_id: 草稿 ID
            sections: 章节列表
            user_id: 用户 ID
            pages_per_section: 每个章节推荐的页数（可选）
        
        Returns:
            按章节 ID 分组的推荐结果
        """
        recommendations = {}
        
        for section in sections:
            section_id = section.get("id")
            section_title = section.get("title", "")
            section_description = section.get("description")
            expected_pages = section.get("expected_pages", 3)
            
            if pages_per_section and section_id in pages_per_section:
                expected_pages = pages_per_section[section_id]
            
            # 获取推荐
            section_recommendations = self.recommend_slides_for_section(
                db=db,
                section_title=section_title,
                section_description=section_description,
                user_id=user_id,
                limit=expected_pages
            )
            
            recommendations[section_id] = section_recommendations
        
        return recommendations


# 全局单例
_slide_recommendation_service = None


def get_slide_recommendation_service() -> SlideRecommendationService:
    """获取页面推荐服务实例"""
    global _slide_recommendation_service
    if _slide_recommendation_service is None:
        _slide_recommendation_service = SlideRecommendationService()
    return _slide_recommendation_service
