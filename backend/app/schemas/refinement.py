"""
PPT 精修相关 Schema
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.refinement import RefinementStatus, ModificationAction


class ElementPosition(BaseModel):
    """元素位置"""
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None


class ElementSize(BaseModel):
    """元素尺寸"""
    width: float
    height: float


class ElementStyle(BaseModel):
    """元素样式"""
    font_family: Optional[str] = None
    font_size: Optional[int] = None
    color: Optional[str] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    alignment: Optional[str] = None


class ElementResponse(BaseModel):
    """元素响应"""
    id: str
    type: str
    position: ElementPosition
    content: Any
    style: Optional[ElementStyle] = None


class RefinedPageResponse(BaseModel):
    """精修页面响应 Schema"""
    id: str
    page_index: int
    title: Optional[str] = None
    thumbnail_path: Optional[str] = None
    elements: Optional[List[ElementResponse]] = None
    
    class Config:
        from_attributes = True


class RefinedPageDetailResponse(RefinedPageResponse):
    """精修页面详情响应 Schema"""
    content: Optional[Any] = None
    history_step: int
    total_history_steps: int
    can_undo: bool = False
    can_redo: bool = False


class RefinementTaskResponse(BaseModel):
    """精修任务响应 Schema"""
    id: str
    title: Optional[str] = None
    draft_id: str
    status: RefinementStatus
    total_pages: int
    version: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RefinementTaskDetailResponse(RefinementTaskResponse):
    """精修任务详情响应 Schema"""
    pages: List[RefinedPageResponse] = []
    exported_file_path: Optional[str] = None


class CreateTaskRequest(BaseModel):
    """创建精修任务请求"""
    draft_id: str
    title: Optional[str] = None


class CreateTaskResponse(BaseModel):
    """创建精修任务响应"""
    task_id: str
    total_pages: int
    created_at: datetime


class SaveTaskResponse(BaseModel):
    """保存任务响应"""
    success: bool
    saved_at: datetime
    version: str


class ExportRefinedResponse(BaseModel):
    """导出精修PPT响应"""
    download_url: str
    file_size: int
    exported_at: datetime


# 对话相关
class ChatMessageRequest(BaseModel):
    """对话消息请求"""
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[dict] = None


class ChatMessageResponse(BaseModel):
    """对话消息响应"""
    success: bool
    message_id: str
    assistant_message: str
    modification: Optional[Any] = None
    updated_page: Optional[RefinedPageDetailResponse] = None


class ChatHistoryResponse(BaseModel):
    """对话历史响应"""
    conversation_id: str
    messages: List[dict]


# 元素编辑相关
class EditTextRequest(BaseModel):
    """编辑文本请求"""
    text: str
    preserve_style: bool = True


class EditTableRequest(BaseModel):
    """编辑表格请求"""
    operation: str  # update_cell, add_row, delete_row, add_column, delete_column
    data: Any


class ReplaceImageRequest(BaseModel):
    """替换图片请求"""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None


class EditStyleRequest(BaseModel):
    """编辑样式请求"""
    font_family: Optional[str] = None
    font_size: Optional[int] = None
    color: Optional[str] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None
    alignment: Optional[str] = None


class MoveElementRequest(BaseModel):
    """移动元素请求"""
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None


class ResizeElementRequest(BaseModel):
    """调整元素大小请求"""
    width: float
    height: float


class AddElementRequest(BaseModel):
    """添加元素请求"""
    type: str  # text, image, shape, chart, table
    position: ElementPosition
    content: Any
    style: Optional[ElementStyle] = None


class DuplicateElementRequest(BaseModel):
    """复制元素请求"""
    offset: Optional[dict] = None  # {"x": 20, "y": 20}


class ChangeOrderRequest(BaseModel):
    """调整层级请求"""
    action: str  # bring_to_front, send_to_back, bring_forward, send_backward


class ElementOperationResponse(BaseModel):
    """元素操作响应"""
    success: bool
    modification_id: str
    updated_element: Optional[Any] = None


class DeleteElementResponse(BaseModel):
    """删除元素响应"""
    success: bool
    modification_id: str


class AddElementResponse(BaseModel):
    """添加元素响应"""
    success: bool
    element_id: str
    modification_id: str
    created_element: Any


# 撤销/重做相关
class ModificationHistoryItem(BaseModel):
    """修改历史项"""
    id: str
    page_index: int
    element_id: Optional[str] = None
    action: ModificationAction
    description: Optional[str] = None
    created_at: datetime


class ModificationHistoryResponse(BaseModel):
    """修改历史响应"""
    history: List[ModificationHistoryItem]
    current_step: int
    total_steps: int
    can_undo: bool
    can_redo: bool


class UndoRedoResponse(BaseModel):
    """撤销/重做响应"""
    success: bool
    current_step: int
    total_steps: int
    updated_page: RefinedPageDetailResponse
    can_undo: bool
    can_redo: bool


class GoToStepRequest(BaseModel):
    """跳转到历史步骤请求"""
    step: int


# 建议和快捷操作
class SuggestionResponse(BaseModel):
    """建议响应"""
    id: str
    type: str  # content, style, layout
    title: str
    description: str
    preview: Optional[str] = None


class SuggestionsResponse(BaseModel):
    """建议列表响应"""
    suggestions: List[SuggestionResponse]


class QuickActionResponse(BaseModel):
    """快捷操作响应"""
    id: str
    type: str
    label: str
    icon: Optional[str] = None


class QuickActionsResponse(BaseModel):
    """快捷操作列表响应"""
    actions: List[QuickActionResponse]


# 批量操作
class BatchDeleteRequest(BaseModel):
    """批量删除请求"""
    element_ids: List[str]


class BatchDeleteResponse(BaseModel):
    """批量删除响应"""
    success: bool
    modification_id: str
    deleted_count: int


class BatchStyleRequest(BaseModel):
    """批量样式请求"""
    element_ids: List[str]
    style: ElementStyle


class BatchStyleResponse(BaseModel):
    """批量样式响应"""
    success: bool
    modification_id: str
    updated_count: int


class AlignElementsRequest(BaseModel):
    """对齐元素请求"""
    element_ids: List[str]
    alignment: str  # left, center, right, top, middle, bottom, distribute_h, distribute_v


class AlignElementsResponse(BaseModel):
    """对齐元素响应"""
    success: bool
    modification_id: str
    updated_elements: List[Any]


# 任务列表相关
class RefinementTaskListItem(BaseModel):
    """精修任务列表项"""
    id: str
    title: Optional[str] = None
    draft_id: str
    status: RefinementStatus
    page_count: int
    modification_count: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RefinementTaskListResponse(BaseModel):
    """精修任务列表响应"""
    tasks: List[RefinementTaskListItem]
    total: int
    page: int
    page_size: int
