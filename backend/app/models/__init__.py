"""
数据模型模块
"""

from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin, generate_uuid
from app.models.user import User
from app.models.document import Document, Slide, DocumentStatus
from app.models.outline import Outline, OutlineSection, OutlineStatus, OutlineGenerationMode
from app.models.draft import Draft, DraftPage, DraftStatus
from app.models.generation import (
    GenerationTask,
    GeneratedPage,
    WebSource,
    GenerationStatus,
    SearchDepth,
)
from app.models.refinement import (
    RefinementTask,
    RefinedPage,
    PageModification,
    RefinementConversation,
    RefinementMessage,
    RefinementStatus,
    ModificationAction,
)
from app.models.version import (
    VersionHistory,
    VersionComparison,
    VersionType,
)
from app.models.template import (
    Template,
    TemplatePage,
    TemplateUsage,
    UserFavoriteTemplate,
    TemplateCategory,
    TemplateStatus,
)
from app.models.image import (
    ImageRecommendation,
    ImageLibrary,
    ImageUsage,
    ImageSource,
    ImageCategory,
)
from app.services.large_file import (
    ChunkedUpload,
    UploadStatus,
)

__all__ = [
    # 基类
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "generate_uuid",
    # 用户
    "User",
    # 文档
    "Document",
    "Slide",
    "DocumentStatus",
    # 大纲
    "Outline",
    "OutlineSection",
    "OutlineStatus",
    "OutlineGenerationMode",
    # 草稿
    "Draft",
    "DraftPage",
    "DraftStatus",
    # 生成
    "GenerationTask",
    "GeneratedPage",
    "WebSource",
    "GenerationStatus",
    "SearchDepth",
    # 精修
    "RefinementTask",
    "RefinedPage",
    "PageModification",
    "RefinementConversation",
    "RefinementMessage",
    "RefinementStatus",
    "ModificationAction",
    # 版本历史
    "VersionHistory",
    "VersionComparison",
    "VersionType",
    # 模板系统
    "Template",
    "TemplatePage",
    "TemplateUsage",
    "UserFavoriteTemplate",
    "TemplateCategory",
    "TemplateStatus",
    # 图片推荐
    "ImageRecommendation",
    "ImageLibrary",
    "ImageUsage",
    "ImageSource",
    "ImageCategory",
    # 大文件处理
    "ChunkedUpload",
    "UploadStatus",
]
