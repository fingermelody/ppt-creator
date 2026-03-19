"""
模板系统服务
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.template import (
    Template, TemplatePage, TemplateUsage, UserFavoriteTemplate,
    TemplateCategory, TemplateStatus
)


class TemplateService:
    """模板系统服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_template(
        self,
        name: str,
        creator_id: Optional[str] = None,
        description: Optional[str] = None,
        category: str = "business",
        tags: Optional[List[str]] = None,
        is_public: bool = True,
        is_system: bool = False,
        config: Optional[Dict[str, Any]] = None,
    ) -> Template:
        """创建模板"""
        # 解析分类
        try:
            category_enum = TemplateCategory(category)
        except ValueError:
            category_enum = TemplateCategory.BUSINESS
        
        template = Template(
            name=name,
            description=description,
            category=category_enum,
            status=TemplateStatus.DRAFT,
            is_system=is_system,
            is_public=is_public,
            tags=tags,
            config=config,
            creator_id=creator_id,
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    def get_templates(
        self,
        user_id: Optional[str] = None,
        category: Optional[str] = None,
        is_public: Optional[bool] = None,
        is_system: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Template], int]:
        """获取模板列表"""
        query = self.db.query(Template).filter(
            Template.is_deleted == False,
            Template.status == TemplateStatus.PUBLISHED
        )
        
        # 分类筛选
        if category:
            try:
                category_enum = TemplateCategory(category)
                query = query.filter(Template.category == category_enum)
            except ValueError:
                pass
        
        # 公开性筛选
        if is_public is not None:
            query = query.filter(Template.is_public == is_public)
        
        # 系统模板筛选
        if is_system is not None:
            query = query.filter(Template.is_system == is_system)
        
        # 搜索
        if search:
            query = query.filter(
                Template.name.ilike(f"%{search}%") |
                Template.description.ilike(f"%{search}%")
            )
        
        # 如果指定用户，也显示用户自己的非公开模板
        if user_id:
            query = self.db.query(Template).filter(
                Template.is_deleted == False,
                Template.status == TemplateStatus.PUBLISHED,
                (Template.is_public == True) | (Template.creator_id == user_id)
            )
            if category:
                try:
                    category_enum = TemplateCategory(category)
                    query = query.filter(Template.category == category_enum)
                except ValueError:
                    pass
        
        total = query.count()
        
        templates = query.order_by(
            Template.use_count.desc(),
            Template.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        return templates, total
    
    def get_template_detail(self, template_id: str) -> Optional[Template]:
        """获取模板详情"""
        return self.db.query(Template).filter(
            Template.id == template_id,
            Template.is_deleted == False
        ).first()
    
    def get_user_templates(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Template], int]:
        """获取用户创建的模板"""
        query = self.db.query(Template).filter(
            Template.creator_id == user_id,
            Template.is_deleted == False
        )
        
        total = query.count()
        
        templates = query.order_by(
            Template.updated_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        return templates, total
    
    def update_template(
        self,
        template_id: str,
        user_id: str,
        **kwargs
    ) -> Optional[Template]:
        """更新模板"""
        template = self.db.query(Template).filter(
            Template.id == template_id,
            Template.creator_id == user_id,
            Template.is_deleted == False
        ).first()
        
        if not template:
            return None
        
        # 更新字段
        for key, value in kwargs.items():
            if value is not None and hasattr(template, key):
                if key == "category":
                    try:
                        value = TemplateCategory(value)
                    except ValueError:
                        continue
                setattr(template, key, value)
        
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    def delete_template(self, template_id: str, user_id: str) -> bool:
        """删除模板（软删除）"""
        template = self.db.query(Template).filter(
            Template.id == template_id,
            Template.creator_id == user_id,
            Template.is_deleted == False,
            Template.is_system == False  # 系统模板不能删除
        ).first()
        
        if not template:
            return False
        
        template.is_deleted = True
        template.deleted_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def publish_template(self, template_id: str, user_id: str) -> Optional[Template]:
        """发布模板"""
        template = self.db.query(Template).filter(
            Template.id == template_id,
            Template.creator_id == user_id,
            Template.is_deleted == False
        ).first()
        
        if not template:
            return None
        
        template.status = TemplateStatus.PUBLISHED
        self.db.commit()
        self.db.refresh(template)
        
        return template
    
    def apply_template(
        self,
        template_id: str,
        user_id: str,
        target_type: str,
        target_id: str,
    ) -> Dict[str, Any]:
        """
        应用模板到目标（草稿/大纲）
        
        Returns:
            应用结果
        """
        template = self.get_template_detail(template_id)
        if not template:
            raise ValueError("模板不存在")
        
        # 记录使用
        usage = TemplateUsage(
            template_id=template_id,
            user_id=user_id,
            usage_type=target_type,
            target_id=target_id,
        )
        self.db.add(usage)
        
        # 更新使用次数
        template.use_count += 1
        
        # 根据目标类型应用模板
        pages_created = 0
        
        if target_type == "draft":
            pages_created = self._apply_to_draft(template, target_id)
        elif target_type == "outline":
            pages_created = self._apply_to_outline(template, target_id)
        
        self.db.commit()
        
        return {
            "success": True,
            "applied_at": datetime.utcnow(),
            "pages_created": pages_created,
        }
    
    def _apply_to_draft(self, template: Template, draft_id: str) -> int:
        """应用模板到草稿"""
        # 这里实现具体的模板应用逻辑
        # 可以根据模板的页面结构创建草稿页面
        from app.models.draft import Draft, DraftPage
        
        draft = self.db.query(Draft).filter(Draft.id == draft_id).first()
        if not draft:
            return 0
        
        # 应用模板配置到草稿
        if template.config:
            # 可以存储到草稿的某个字段中
            pass
        
        return len(template.pages) if template.pages else 0
    
    def _apply_to_outline(self, template: Template, outline_id: str) -> int:
        """应用模板到大纲"""
        # 类似的实现
        return 0
    
    def add_favorite(self, user_id: str, template_id: str) -> bool:
        """收藏模板"""
        # 检查是否已收藏
        existing = self.db.query(UserFavoriteTemplate).filter(
            UserFavoriteTemplate.user_id == user_id,
            UserFavoriteTemplate.template_id == template_id
        ).first()
        
        if existing:
            return True  # 已经收藏过了
        
        favorite = UserFavoriteTemplate(
            user_id=user_id,
            template_id=template_id,
        )
        self.db.add(favorite)
        
        # 更新模板的收藏数
        template = self.get_template_detail(template_id)
        if template:
            template.like_count += 1
        
        self.db.commit()
        return True
    
    def remove_favorite(self, user_id: str, template_id: str) -> bool:
        """取消收藏"""
        favorite = self.db.query(UserFavoriteTemplate).filter(
            UserFavoriteTemplate.user_id == user_id,
            UserFavoriteTemplate.template_id == template_id
        ).first()
        
        if not favorite:
            return False
        
        self.db.delete(favorite)
        
        # 更新模板的收藏数
        template = self.get_template_detail(template_id)
        if template and template.like_count > 0:
            template.like_count -= 1
        
        self.db.commit()
        return True
    
    def get_user_favorites(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[Template], int]:
        """获取用户收藏的模板"""
        query = self.db.query(Template).join(
            UserFavoriteTemplate,
            UserFavoriteTemplate.template_id == Template.id
        ).filter(
            UserFavoriteTemplate.user_id == user_id,
            Template.is_deleted == False
        )
        
        total = query.count()
        
        templates = query.order_by(
            UserFavoriteTemplate.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        return templates, total
    
    def is_favorited(self, user_id: str, template_id: str) -> bool:
        """检查用户是否收藏了模板"""
        return self.db.query(UserFavoriteTemplate).filter(
            UserFavoriteTemplate.user_id == user_id,
            UserFavoriteTemplate.template_id == template_id
        ).first() is not None
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """获取所有模板分类及统计"""
        categories = []
        category_names = {
            "business": "商务",
            "education": "教育",
            "technology": "科技",
            "creative": "创意",
            "minimal": "简约",
            "nature": "自然",
            "custom": "自定义",
        }
        
        for cat in TemplateCategory:
            count = self.db.query(Template).filter(
                Template.category == cat,
                Template.is_deleted == False,
                Template.status == TemplateStatus.PUBLISHED,
                Template.is_public == True
            ).count()
            
            categories.append({
                "category": cat.value,
                "name": category_names.get(cat.value, cat.value),
                "count": count,
                "icon": f"icon-{cat.value}",
            })
        
        return categories
    
    def add_template_page(
        self,
        template_id: str,
        name: str,
        layout_type: str,
        content_structure: Optional[Dict[str, Any]] = None,
        style_config: Optional[Dict[str, Any]] = None,
    ) -> TemplatePage:
        """添加模板页面"""
        # 获取当前最大顺序
        max_order = self.db.query(func.max(TemplatePage.order_index)).filter(
            TemplatePage.template_id == template_id
        ).scalar() or -1
        
        page = TemplatePage(
            template_id=template_id,
            order_index=max_order + 1,
            name=name,
            layout_type=layout_type,
            content_structure=content_structure,
            style_config=style_config,
        )
        
        self.db.add(page)
        self.db.commit()
        self.db.refresh(page)
        
        return page
