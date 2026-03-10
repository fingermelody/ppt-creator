"""
大文件处理 Schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ============ 请求模型 ============

class InitUploadRequest(BaseModel):
    """初始化上传请求"""
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., gt=0, description="文件大小（字节）")
    file_type: Optional[str] = Field(None, description="文件MIME类型")
    file_hash: Optional[str] = Field(None, description="文件SHA-256哈希（用于秒传和校验）")
    chunk_size: Optional[int] = Field(None, ge=1024*1024, le=100*1024*1024, description="分片大小（1MB-100MB）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "presentation.pptx",
                "file_size": 52428800,
                "file_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "file_hash": "a1b2c3d4e5f6...",
                "chunk_size": 5242880
            }
        }


class UploadChunkRequest(BaseModel):
    """上传分片请求（用于表单数据之外的元数据）"""
    chunk_index: int = Field(..., ge=0, description="分片索引")
    chunk_hash: Optional[str] = Field(None, description="分片SHA-256哈希（用于校验）")


class CancelUploadRequest(BaseModel):
    """取消上传请求"""
    confirm: bool = Field(True, description="确认取消")


# ============ 响应模型 ============

class ChunkInfoResponse(BaseModel):
    """分片信息响应"""
    index: int = Field(..., description="分片索引")
    start: int = Field(..., description="分片起始字节")
    end: int = Field(..., description="分片结束字节")
    size: int = Field(..., description="分片大小")
    uploaded: bool = Field(False, description="是否已上传")


class InitUploadResponse(BaseModel):
    """初始化上传响应"""
    upload_id: str = Field(..., description="上传任务ID")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    chunk_size: int = Field(..., description="分片大小")
    total_chunks: int = Field(..., description="总分片数")
    expires_at: datetime = Field(..., description="上传过期时间")
    instant_upload: bool = Field(False, description="是否秒传成功")
    final_path: Optional[str] = Field(None, description="秒传成功时的文件路径")
    
    class Config:
        json_schema_extra = {
            "example": {
                "upload_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_name": "presentation.pptx",
                "file_size": 52428800,
                "chunk_size": 5242880,
                "total_chunks": 10,
                "expires_at": "2026-03-11T00:00:00",
                "instant_upload": False,
                "final_path": None
            }
        }


class UploadChunkResponse(BaseModel):
    """上传分片响应"""
    success: bool = Field(..., description="是否成功")
    chunk_index: int = Field(..., description="分片索引")
    uploaded_chunks: int = Field(..., description="已上传分片数")
    total_chunks: int = Field(..., description="总分片数")
    progress: float = Field(..., ge=0, le=100, description="上传进度百分比")
    error: Optional[str] = Field(None, description="错误信息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "chunk_index": 3,
                "uploaded_chunks": 4,
                "total_chunks": 10,
                "progress": 40.0,
                "error": None
            }
        }


class UploadStatusResponse(BaseModel):
    """上传状态响应"""
    id: str = Field(..., description="上传任务ID")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    status: str = Field(..., description="上传状态")
    total_chunks: int = Field(..., description="总分片数")
    uploaded_chunks: int = Field(..., description="已上传分片数")
    progress: float = Field(..., ge=0, le=100, description="上传进度百分比")
    missing_chunks: List[int] = Field(default_factory=list, description="缺失的分片索引")
    final_path: Optional[str] = Field(None, description="最终文件路径")
    error_message: Optional[str] = Field(None, description="错误信息")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "file_name": "presentation.pptx",
                "file_size": 52428800,
                "status": "uploading",
                "total_chunks": 10,
                "uploaded_chunks": 4,
                "progress": 40.0,
                "missing_chunks": [4, 5, 6, 7, 8, 9],
                "final_path": None,
                "error_message": None,
                "expires_at": "2026-03-11T00:00:00"
            }
        }


class ResumeUploadResponse(BaseModel):
    """断点续传响应"""
    id: str = Field(..., description="上传任务ID")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小")
    status: str = Field(..., description="上传状态")
    chunk_size: int = Field(..., description="分片大小")
    total_chunks: int = Field(..., description="总分片数")
    uploaded_chunks: int = Field(..., description="已上传分片数")
    progress: float = Field(..., ge=0, le=100, description="上传进度百分比")
    missing_chunks: List[int] = Field(default_factory=list, description="缺失的分片索引")
    missing_chunks_info: List[ChunkInfoResponse] = Field(default_factory=list, description="缺失分片详细信息")
    final_path: Optional[str] = Field(None, description="最终文件路径")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class UploadCompleteResponse(BaseModel):
    """上传完成响应"""
    success: bool = Field(..., description="是否成功")
    status: str = Field(..., description="状态")
    final_path: Optional[str] = Field(None, description="最终文件路径")
    file_size: Optional[int] = Field(None, description="文件大小")
    file_url: Optional[str] = Field(None, description="文件访问URL")
    error: Optional[str] = Field(None, description="错误信息")


class CleanupExpiredResponse(BaseModel):
    """清理过期上传响应"""
    success: bool = Field(True, description="是否成功")
    cleaned_count: int = Field(..., description="清理的上传任务数")
    message: str = Field(..., description="清理结果消息")


# ============ 列表响应 ============

class UploadListItem(BaseModel):
    """上传列表项"""
    id: str
    file_name: str
    file_size: int
    file_type: Optional[str]
    status: str
    progress: float
    created_at: datetime
    expires_at: Optional[datetime]


class UploadListResponse(BaseModel):
    """上传列表响应"""
    items: List[UploadListItem] = Field(default_factory=list, description="上传列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页")
    page_size: int = Field(10, description="每页数量")
