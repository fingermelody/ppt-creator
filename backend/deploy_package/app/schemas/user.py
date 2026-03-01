"""
用户相关 Schema
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserBase(BaseModel):
    """用户基础 Schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """用户创建 Schema"""
    password: str = Field(..., min_length=6, max_length=100)
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    """用户更新 Schema"""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """用户响应 Schema"""
    id: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录 Schema"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token 响应 Schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
