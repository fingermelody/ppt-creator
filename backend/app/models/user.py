"""
用户模型
"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """用户表"""
    __tablename__ = "users"
    
    # 基本信息
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # 用户信息
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # 最后登录时间
    last_login_at = Column(DateTime, nullable=True)
    
    # 关联关系
    documents = relationship("Document", back_populates="owner", lazy="dynamic")
    drafts = relationship("Draft", back_populates="owner", lazy="dynamic")
    outlines = relationship("Outline", back_populates="owner", lazy="dynamic")
    generation_tasks = relationship("GenerationTask", back_populates="owner", lazy="dynamic")
    refinement_tasks = relationship("RefinementTask", back_populates="owner", lazy="dynamic")
