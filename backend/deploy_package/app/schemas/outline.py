"""
大纲相关 Schema
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.outline import OutlineStatus, OutlineGenerationMode


class OutlineSectionBase(BaseModel):
    """大纲章节基础 Schema"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    content_hint: Optional[str] = None
    expected_pages: int = Field(default=1, ge=1)


class OutlineSectionCreate(OutlineSectionBase):
    """章节创建 Schema"""
    parent_id: Optional[str] = None
    order_index: Optional[int] = None


class OutlineSectionUpdate(BaseModel):
    """章节更新 Schema"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    content_hint: Optional[str] = None
    expected_pages: Optional[int] = Field(None, ge=1)
    order_index: Optional[int] = None


class OutlineSectionResponse(OutlineSectionBase):
    """章节响应 Schema"""
    id: str
    outline_id: str
    parent_id: Optional[str] = None
    order_index: int
    level: int
    is_page_selected: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class OutlineSectionTreeResponse(OutlineSectionResponse):
    """章节树形响应 Schema"""
    children: List["OutlineSectionTreeResponse"] = []


class OutlineBase(BaseModel):
    """大纲基础 Schema"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None


class OutlineCreate(OutlineBase):
    """大纲创建 Schema"""
    generation_mode: OutlineGenerationMode = OutlineGenerationMode.MANUAL
    generation_config: Optional[dict] = None


class OutlineUpdate(BaseModel):
    """大纲更新 Schema"""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[OutlineStatus] = None


class OutlineResponse(OutlineBase):
    """大纲响应 Schema"""
    id: str
    generation_mode: OutlineGenerationMode
    status: OutlineStatus
    section_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OutlineDetailResponse(OutlineResponse):
    """大纲详情响应 Schema"""
    sections: List[OutlineSectionTreeResponse] = []
    generation_config: Optional[dict] = None


class OutlineListResponse(BaseModel):
    """大纲列表响应"""
    outlines: List[OutlineResponse]
    total: int


# 智能生成相关
class IntelligentGenerateRequest(BaseModel):
    """智能生成大纲请求"""
    topic: str = Field(..., min_length=10, max_length=2000)
    page_count: int = Field(default=10, ge=5, le=30)
    style: Optional[str] = None  # business, education, technology, etc.


class IntelligentGenerateResponse(BaseModel):
    """智能生成大纲响应"""
    outline_id: str
    title: str
    sections: List[OutlineSectionResponse]


# 向导式生成相关
class WizardStep1Request(BaseModel):
    """向导第一步：主题"""
    topic: str = Field(..., min_length=5, max_length=500)


class WizardStep1Response(BaseModel):
    """向导第一步响应"""
    session_id: str
    suggested_titles: List[str]
    suggested_page_count: int


class WizardStep2Request(BaseModel):
    """向导第二步：确认标题和页数"""
    session_id: str
    title: str
    page_count: int = Field(..., ge=5, le=30)


class WizardStep2Response(BaseModel):
    """向导第二步响应"""
    session_id: str
    suggested_sections: List[dict]


class WizardStep3Request(BaseModel):
    """向导第三步：确认章节"""
    session_id: str
    sections: List[dict]


class WizardStep3Response(BaseModel):
    """向导第三步响应"""
    outline_id: str
    outline: OutlineDetailResponse


# 确认大纲相关
class ConfirmOutlineResponse(BaseModel):
    """确认大纲响应"""
    success: bool = True
    assembly_draft_id: str  # 自动创建的组装草稿ID
    message: str = "大纲已确认，已创建组装草稿"


class AutoSaveOutlineRequest(BaseModel):
    """自动保存大纲请求"""
    title: str
    description: Optional[str] = None
    sections: List[dict] = []  # 章节列表


class AutoSaveOutlineResponse(BaseModel):
    """自动保存大纲响应"""
    success: bool = True
    saved_at: datetime
