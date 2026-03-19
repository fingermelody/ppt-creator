"""
通用 Schema 定义
"""

from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar("T")


class ResponseBase(BaseModel):
    """响应基类"""
    success: bool = True
    message: Optional[str] = None


class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1, description="页码")
    limit: int = Field(default=20, ge=1, le=100, description="每页数量")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, limit: int):
        pages = (total + limit - 1) // limit
        return cls(items=items, total=total, page=page, limit=limit, pages=pages)


class TimestampSchema(BaseModel):
    """时间戳 Schema"""
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IdSchema(BaseModel):
    """ID Schema"""
    id: str
    
    class Config:
        from_attributes = True
