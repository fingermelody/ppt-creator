"""
数据库模块
"""

from app.db.base import Base, engine, SessionLocal, get_db

# 导入所有模型以确保它们注册到 Base
from app.models import (
    User,
    Document, Slide,
    Outline, OutlineSection,
    Draft, DraftPage,
    GenerationTask, GeneratedPage, WebSource,
    RefinementTask, RefinedPage, PageModification, RefinementConversation, RefinementMessage,
)

__all__ = ["Base", "engine", "SessionLocal", "get_db"]
