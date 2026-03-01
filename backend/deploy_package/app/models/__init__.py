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
    PPTTemplate,
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
    "PPTTemplate",
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
]
