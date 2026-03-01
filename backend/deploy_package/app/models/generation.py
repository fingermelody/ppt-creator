"""
PPT 智能生成模型
"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel, SoftDeleteMixin


class GenerationStatus(str, enum.Enum):
    """生成状态"""
    PENDING = "pending"              # 等待开始
    SEARCHING = "searching"          # 正在搜索信息
    ANALYZING = "analyzing"          # 分析内容
    GENERATING = "generating"        # 生成PPT
    APPLYING_STYLE = "applying_style"  # 应用风格
    COMPLETED = "completed"          # 完成
    FAILED = "failed"                # 失败
    CANCELLED = "cancelled"          # 已取消


class SearchDepth(str, enum.Enum):
    """搜索深度"""
    QUICK = "quick"      # 快速搜索 3-5 来源
    NORMAL = "normal"    # 标准搜索 5-10 来源
    DEEP = "deep"        # 深度搜索 10-20 来源


class GenerationTask(BaseModel, SoftDeleteMixin):
    """生成任务表"""
    __tablename__ = "generation_tasks"
    
    # 基本信息
    title = Column(String(255), nullable=True)
    topic = Column(Text, nullable=False)  # 主题描述
    
    # 生成参数
    page_count = Column(Integer, default=10, nullable=False)
    language = Column(String(10), default="zh", nullable=False)
    search_depth = Column(
        SQLEnum(SearchDepth),
        default=SearchDepth.NORMAL,
        nullable=False
    )
    include_images = Column(Integer, default=1, nullable=False)
    include_charts = Column(Integer, default=1, nullable=False)
    
    # 模板/风格
    template_id = Column(String(36), ForeignKey("ppt_templates.id"), nullable=True)
    template = relationship("PPTTemplate")
    custom_style_path = Column(String(500), nullable=True)  # 自定义风格文件路径
    
    # 状态
    status = Column(
        SQLEnum(GenerationStatus),
        default=GenerationStatus.PENDING,
        nullable=False
    )
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    current_step = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # 结果统计
    total_pages = Column(Integer, default=0, nullable=False)
    sources_found = Column(Integer, default=0, nullable=False)
    
    # 导出信息
    exported_file_path = Column(String(500), nullable=True)
    
    # 所属用户
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="generation_tasks")
    
    # 关联页面
    pages = relationship(
        "GeneratedPage",
        back_populates="task",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="GeneratedPage.page_index"
    )
    
    # 网络来源
    sources = relationship(
        "WebSource",
        back_populates="task",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )


class GeneratedPage(BaseModel):
    """生成的页面表"""
    __tablename__ = "generated_pages"
    
    # 所属任务
    task_id = Column(String(36), ForeignKey("generation_tasks.id"), nullable=False, index=True)
    task = relationship("GenerationTask", back_populates="pages")
    
    # 页面信息
    page_index = Column(Integer, nullable=False)
    title = Column(String(500), nullable=True)
    
    # 页面内容
    content = Column(JSON, nullable=True)
    
    # 缩略图
    thumbnail_path = Column(String(500), nullable=True)
    
    # 引用来源
    source_ids = Column(JSON, nullable=True)  # 引用的 WebSource IDs


class WebSource(BaseModel):
    """网络搜索来源表"""
    __tablename__ = "web_sources"
    
    # 所属任务
    task_id = Column(String(36), ForeignKey("generation_tasks.id"), nullable=False, index=True)
    task = relationship("GenerationTask", back_populates="sources")
    
    # 来源信息
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    snippet = Column(Text, nullable=True)
    
    # 内容
    full_content = Column(Text, nullable=True)  # 抓取的完整内容
    
    # 相关度评分
    relevance = Column(Float, default=0.0, nullable=False)
    
    # 是否被使用
    is_used = Column(Integer, default=0, nullable=False)


class PPTTemplate(BaseModel):
    """PPT 模板表"""
    __tablename__ = "ppt_templates"
    
    # 模板信息
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # business, education, technology, etc.
    
    # 文件路径
    file_path = Column(String(500), nullable=False)
    preview_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    
    # 配色方案
    color_scheme = Column(JSON, nullable=True)
    font_family = Column(String(100), nullable=True)
    
    # 状态
    is_premium = Column(Integer, default=0, nullable=False)
    is_custom = Column(Integer, default=0, nullable=False)  # 是否为用户自定义
    
    # 使用统计
    usage_count = Column(Integer, default=0, nullable=False)
    
    # 所属用户（自定义模板）
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
