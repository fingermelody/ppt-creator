"""
PPT 模板系统模型
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, SoftDeleteMixin


class TemplateCategory(str, enum.Enum):
    """模板分类"""
    BUSINESS = "business"       # 商务
    EDUCATION = "education"     # 教育
    TECHNOLOGY = "technology"   # 科技
    CREATIVE = "creative"       # 创意
    MINIMAL = "minimal"         # 简约
    NATURE = "nature"           # 自然
    CUSTOM = "custom"           # 自定义


class TemplateStatus(str, enum.Enum):
    """模板状态"""
    DRAFT = "draft"             # 草稿
    PUBLISHED = "published"     # 已发布
    ARCHIVED = "archived"       # 已归档


class Template(BaseModel, SoftDeleteMixin):
    """PPT 模板表"""
    __tablename__ = "ppt_templates"
    
    # 基本信息
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # 分类
    category = Column(
        SQLEnum(TemplateCategory),
        default=TemplateCategory.BUSINESS,
        nullable=False
    )
    
    # 状态
    status = Column(
        SQLEnum(TemplateStatus),
        default=TemplateStatus.DRAFT,
        nullable=False
    )
    
    # 是否系统模板
    is_system = Column(Boolean, default=False, nullable=False)
    
    # 是否公开
    is_public = Column(Boolean, default=True, nullable=False)
    
    # 缩略图
    thumbnail_url = Column(String(500), nullable=True)
    preview_images = Column(JSON, nullable=True)  # 预览图列表
    
    # 模板文件
    file_path = Column(String(500), nullable=True)  # PPTX 文件路径
    file_size = Column(Integer, default=0, nullable=False)
    
    # 模板配置
    config = Column(JSON, nullable=True)  # 配色、字体等配置
    
    # 页面布局定义
    layouts = Column(JSON, nullable=True)  # 可用的页面布局
    
    # 统计
    use_count = Column(Integer, default=0, nullable=False)
    like_count = Column(Integer, default=0, nullable=False)
    
    # 标签
    tags = Column(JSON, nullable=True)
    
    # 创建者
    creator_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    creator = relationship("User", backref="templates")
    
    # 模板页面
    pages = relationship(
        "TemplatePage",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplatePage.order_index"
    )


class TemplatePage(BaseModel):
    """模板页面表"""
    __tablename__ = "template_pages"
    
    # 所属模板
    template_id = Column(String(36), ForeignKey("ppt_templates.id"), nullable=False, index=True)
    template = relationship("Template", back_populates="pages")
    
    # 页面信息
    order_index = Column(Integer, nullable=False)
    name = Column(String(255), nullable=True)
    layout_type = Column(String(50), nullable=True)  # 布局类型：title, content, two_column, etc.
    
    # 页面内容
    content_structure = Column(JSON, nullable=True)  # 内容占位符结构
    style_config = Column(JSON, nullable=True)  # 样式配置
    
    # 缩略图
    thumbnail_url = Column(String(500), nullable=True)


class TemplateUsage(BaseModel):
    """模板使用记录表"""
    __tablename__ = "template_usages"
    
    # 模板
    template_id = Column(String(36), ForeignKey("ppt_templates.id"), nullable=False, index=True)
    template = relationship("Template")
    
    # 用户
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User")
    
    # 使用场景
    usage_type = Column(String(50), nullable=True)  # draft, outline, etc.
    target_id = Column(String(36), nullable=True)  # 关联的草稿/大纲ID


class UserFavoriteTemplate(BaseModel):
    """用户收藏的模板"""
    __tablename__ = "user_favorite_templates"
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    template_id = Column(String(36), ForeignKey("ppt_templates.id"), nullable=False, index=True)
    
    user = relationship("User")
    template = relationship("Template")
