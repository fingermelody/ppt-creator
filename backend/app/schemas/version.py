"""
版本历史管理 Schema
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ 请求模型 ============

class CreateVersionRequest(BaseModel):
    """创建版本请求"""
    description: Optional[str] = Field(None, max_length=500, description="版本描述")
    version_type: str = Field("manual", description="版本类型: auto, manual, export")


class RollbackVersionRequest(BaseModel):
    """回滚版本请求"""
    version_id: str = Field(..., description="目标版本ID")
    create_backup: bool = Field(True, description="回滚前是否创建当前状态的备份版本")


class CompareVersionsRequest(BaseModel):
    """比较版本请求"""
    version_from_id: str = Field(..., description="起始版本ID")
    version_to_id: str = Field(..., description="目标版本ID")


# ============ 响应模型 ============

class VersionInfo(BaseModel):
    """版本信息"""
    id: str
    version_number: int
    version_label: str
    version_type: str
    description: Optional[str] = None
    page_count: int
    total_elements: int
    snapshot_size: int
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True


class VersionListResponse(BaseModel):
    """版本列表响应"""
    versions: List[VersionInfo]
    total: int
    current_version: Optional[str] = None


class CreateVersionResponse(BaseModel):
    """创建版本响应"""
    success: bool
    version_id: str
    version_label: str
    created_at: datetime


class RollbackResponse(BaseModel):
    """回滚响应"""
    success: bool
    backup_version_id: Optional[str] = None
    restored_version_id: str
    restored_at: datetime
    pages_restored: int


class VersionDetailResponse(BaseModel):
    """版本详情响应"""
    id: str
    version_number: int
    version_label: str
    version_type: str
    description: Optional[str] = None
    page_count: int
    total_elements: int
    snapshot_size: int
    created_at: datetime
    created_by: str
    snapshot_preview: Optional[List[Dict[str, Any]]] = None  # 页面预览列表


class PageDiff(BaseModel):
    """页面差异"""
    page_index: int
    status: str  # added, removed, modified, unchanged
    changes: Optional[List[Dict[str, Any]]] = None


class VersionComparisonResponse(BaseModel):
    """版本比较响应"""
    version_from: VersionInfo
    version_to: VersionInfo
    summary: Dict[str, int]
    page_diffs: List[PageDiff]
    element_changes: Dict[str, int]


class VersionSnapshotResponse(BaseModel):
    """版本快照响应"""
    version_id: str
    version_label: str
    pages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
