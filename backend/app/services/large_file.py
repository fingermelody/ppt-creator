"""
大文件处理优化服务
支持分片上传、断点续传、进度跟踪
"""

import os
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, BinaryIO
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import Column, String, Integer, Text, DateTime, Enum as SQLEnum, JSON
from sqlalchemy.orm import Session

from app.models.base import BaseModel


class UploadStatus(str, Enum):
    """上传状态"""
    PENDING = "pending"         # 等待上传
    UPLOADING = "uploading"     # 上传中
    MERGING = "merging"         # 合并中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消


class ChunkedUpload(BaseModel):
    """分片上传记录表"""
    __tablename__ = "chunked_uploads"
    
    # 用户
    user_id = Column(String(36), nullable=False, index=True)
    
    # 文件信息
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256 哈希
    
    # 分片信息
    chunk_size = Column(Integer, default=5 * 1024 * 1024, nullable=False)  # 默认 5MB
    total_chunks = Column(Integer, nullable=False)
    uploaded_chunks = Column(Integer, default=0, nullable=False)
    
    # 状态
    status = Column(
        SQLEnum(UploadStatus),
        default=UploadStatus.PENDING,
        nullable=False
    )
    
    # 上传进度详情
    chunks_status = Column(JSON, nullable=True)  # {0: true, 1: false, ...}
    
    # 临时存储路径
    temp_dir = Column(String(500), nullable=True)
    
    # 最终文件路径
    final_path = Column(String(500), nullable=True)
    
    # 过期时间（未完成的上传会过期）
    expires_at = Column(DateTime, nullable=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)


@dataclass
class ChunkInfo:
    """分片信息"""
    index: int
    start: int
    end: int
    size: int
    hash: Optional[str] = None
    uploaded: bool = False


class LargeFileService:
    """大文件处理服务"""
    
    # 默认配置
    DEFAULT_CHUNK_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_CHUNK_SIZE = 100 * 1024 * 1024    # 100MB
    MIN_CHUNK_SIZE = 1 * 1024 * 1024      # 1MB
    UPLOAD_EXPIRE_HOURS = 24              # 上传任务过期时间
    MAX_CONCURRENT_CHUNKS = 5             # 最大并发上传数
    
    def __init__(self, db: Session, upload_dir: str = "/tmp/uploads"):
        self.db = db
        self.upload_dir = upload_dir
    
    def init_upload(
        self,
        user_id: str,
        file_name: str,
        file_size: int,
        file_type: Optional[str] = None,
        file_hash: Optional[str] = None,
        chunk_size: Optional[int] = None,
    ) -> ChunkedUpload:
        """
        初始化分片上传
        
        Args:
            user_id: 用户ID
            file_name: 文件名
            file_size: 文件大小（字节）
            file_type: 文件类型
            file_hash: 文件哈希（用于秒传和校验）
            chunk_size: 分片大小
        
        Returns:
            上传任务记录
        """
        # 计算分片大小
        if chunk_size is None:
            chunk_size = self._calculate_optimal_chunk_size(file_size)
        else:
            chunk_size = max(self.MIN_CHUNK_SIZE, min(chunk_size, self.MAX_CHUNK_SIZE))
        
        # 计算分片数量
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        
        # 检查是否存在相同文件（秒传）
        if file_hash:
            existing = self._check_existing_file(file_hash)
            if existing:
                return existing
        
        # 创建临时目录
        import uuid
        upload_id = str(uuid.uuid4())
        temp_dir = os.path.join(self.upload_dir, "temp", upload_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        # 初始化分片状态
        chunks_status = {str(i): False for i in range(total_chunks)}
        
        # 创建上传记录
        upload = ChunkedUpload(
            user_id=user_id,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            file_hash=file_hash,
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            status=UploadStatus.PENDING,
            chunks_status=chunks_status,
            temp_dir=temp_dir,
            expires_at=datetime.utcnow() + timedelta(hours=self.UPLOAD_EXPIRE_HOURS),
        )
        
        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)
        
        return upload
    
    def upload_chunk(
        self,
        upload_id: str,
        chunk_index: int,
        chunk_data: bytes,
        chunk_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        上传单个分片
        
        Args:
            upload_id: 上传任务ID
            chunk_index: 分片索引
            chunk_data: 分片数据
            chunk_hash: 分片哈希（用于校验）
        
        Returns:
            上传结果
        """
        upload = self.db.query(ChunkedUpload).filter(
            ChunkedUpload.id == upload_id
        ).first()
        
        if not upload:
            return {"success": False, "error": "上传任务不存在"}
        
        if upload.status in [UploadStatus.COMPLETED, UploadStatus.CANCELLED]:
            return {"success": False, "error": "上传任务已结束"}
        
        if chunk_index < 0 or chunk_index >= upload.total_chunks:
            return {"success": False, "error": "无效的分片索引"}
        
        # 校验分片哈希
        if chunk_hash:
            actual_hash = hashlib.sha256(chunk_data).hexdigest()
            if actual_hash != chunk_hash:
                return {"success": False, "error": "分片数据校验失败"}
        
        # 保存分片
        chunk_path = os.path.join(upload.temp_dir, f"chunk_{chunk_index}")
        with open(chunk_path, 'wb') as f:
            f.write(chunk_data)
        
        # 更新状态
        chunks_status = upload.chunks_status or {}
        chunks_status[str(chunk_index)] = True
        upload.chunks_status = chunks_status
        upload.uploaded_chunks = sum(1 for v in chunks_status.values() if v)
        upload.status = UploadStatus.UPLOADING
        
        self.db.commit()
        
        # 检查是否所有分片都已上传
        if upload.uploaded_chunks >= upload.total_chunks:
            # 触发合并
            return self._merge_chunks(upload)
        
        return {
            "success": True,
            "chunk_index": chunk_index,
            "uploaded_chunks": upload.uploaded_chunks,
            "total_chunks": upload.total_chunks,
            "progress": upload.uploaded_chunks / upload.total_chunks * 100,
        }
    
    def get_upload_status(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """获取上传状态"""
        upload = self.db.query(ChunkedUpload).filter(
            ChunkedUpload.id == upload_id
        ).first()
        
        if not upload:
            return None
        
        # 计算缺失的分片
        missing_chunks = []
        chunks_status = upload.chunks_status or {}
        for i in range(upload.total_chunks):
            if not chunks_status.get(str(i), False):
                missing_chunks.append(i)
        
        return {
            "id": upload.id,
            "file_name": upload.file_name,
            "file_size": upload.file_size,
            "status": upload.status.value,
            "total_chunks": upload.total_chunks,
            "uploaded_chunks": upload.uploaded_chunks,
            "progress": upload.uploaded_chunks / upload.total_chunks * 100 if upload.total_chunks > 0 else 0,
            "missing_chunks": missing_chunks,
            "final_path": upload.final_path,
            "error_message": upload.error_message,
            "expires_at": upload.expires_at.isoformat() if upload.expires_at else None,
        }
    
    def resume_upload(self, upload_id: str) -> Optional[Dict[str, Any]]:
        """
        获取断点续传信息
        
        Returns:
            需要上传的分片列表
        """
        status = self.get_upload_status(upload_id)
        if not status:
            return None
        
        if status["status"] in ["completed", "cancelled"]:
            return status
        
        # 返回需要上传的分片信息
        upload = self.db.query(ChunkedUpload).filter(
            ChunkedUpload.id == upload_id
        ).first()
        
        missing_chunks_info = []
        for chunk_index in status["missing_chunks"]:
            start = chunk_index * upload.chunk_size
            end = min(start + upload.chunk_size, upload.file_size)
            missing_chunks_info.append({
                "index": chunk_index,
                "start": start,
                "end": end,
                "size": end - start,
            })
        
        return {
            **status,
            "missing_chunks_info": missing_chunks_info,
            "chunk_size": upload.chunk_size,
        }
    
    def cancel_upload(self, upload_id: str, user_id: str) -> bool:
        """取消上传"""
        upload = self.db.query(ChunkedUpload).filter(
            ChunkedUpload.id == upload_id,
            ChunkedUpload.user_id == user_id
        ).first()
        
        if not upload:
            return False
        
        upload.status = UploadStatus.CANCELLED
        
        # 清理临时文件
        self._cleanup_temp_files(upload.temp_dir)
        
        self.db.commit()
        return True
    
    def _merge_chunks(self, upload: ChunkedUpload) -> Dict[str, Any]:
        """合并分片"""
        upload.status = UploadStatus.MERGING
        self.db.commit()
        
        try:
            # 确定最终文件路径
            final_dir = os.path.join(self.upload_dir, "files", upload.user_id)
            os.makedirs(final_dir, exist_ok=True)
            
            # 生成唯一文件名
            import uuid
            ext = os.path.splitext(upload.file_name)[1]
            final_name = f"{uuid.uuid4()}{ext}"
            final_path = os.path.join(final_dir, final_name)
            
            # 按顺序合并分片
            with open(final_path, 'wb') as outfile:
                for i in range(upload.total_chunks):
                    chunk_path = os.path.join(upload.temp_dir, f"chunk_{i}")
                    with open(chunk_path, 'rb') as chunk_file:
                        outfile.write(chunk_file.read())
            
            # 校验文件哈希
            if upload.file_hash:
                actual_hash = self._calculate_file_hash(final_path)
                if actual_hash != upload.file_hash:
                    raise ValueError("文件哈希不匹配")
            
            # 更新记录
            upload.final_path = final_path
            upload.status = UploadStatus.COMPLETED
            
            # 清理临时文件
            self._cleanup_temp_files(upload.temp_dir)
            
            self.db.commit()
            
            return {
                "success": True,
                "status": "completed",
                "final_path": final_path,
                "file_size": upload.file_size,
            }
            
        except Exception as e:
            upload.status = UploadStatus.FAILED
            upload.error_message = str(e)
            self.db.commit()
            
            return {
                "success": False,
                "status": "failed",
                "error": str(e),
            }
    
    def _calculate_optimal_chunk_size(self, file_size: int) -> int:
        """计算最优分片大小"""
        # 根据文件大小动态调整
        if file_size < 10 * 1024 * 1024:  # < 10MB
            return 1 * 1024 * 1024  # 1MB
        elif file_size < 100 * 1024 * 1024:  # < 100MB
            return 5 * 1024 * 1024  # 5MB
        elif file_size < 1024 * 1024 * 1024:  # < 1GB
            return 10 * 1024 * 1024  # 10MB
        else:
            return 20 * 1024 * 1024  # 20MB
    
    def _check_existing_file(self, file_hash: str) -> Optional[ChunkedUpload]:
        """检查是否存在相同文件（秒传）"""
        existing = self.db.query(ChunkedUpload).filter(
            ChunkedUpload.file_hash == file_hash,
            ChunkedUpload.status == UploadStatus.COMPLETED,
            ChunkedUpload.final_path != None
        ).first()
        
        if existing and existing.final_path and os.path.exists(existing.final_path):
            return existing
        
        return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _cleanup_temp_files(self, temp_dir: str):
        """清理临时文件"""
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"清理临时文件失败: {e}")
    
    def cleanup_expired_uploads(self) -> int:
        """清理过期的上传任务"""
        now = datetime.utcnow()
        expired = self.db.query(ChunkedUpload).filter(
            ChunkedUpload.status.in_([UploadStatus.PENDING, UploadStatus.UPLOADING]),
            ChunkedUpload.expires_at < now
        ).all()
        
        count = 0
        for upload in expired:
            upload.status = UploadStatus.CANCELLED
            self._cleanup_temp_files(upload.temp_dir)
            count += 1
        
        self.db.commit()
        return count


# ============ 内存优化相关 ============

class StreamingProcessor:
    """流式处理器 - 用于处理大文件时优化内存使用"""
    
    BUFFER_SIZE = 8192  # 8KB 缓冲区
    
    @staticmethod
    def stream_file_read(file_path: str, chunk_size: int = 8192):
        """流式读取文件"""
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    @staticmethod
    def calculate_hash_streaming(file_path: str) -> str:
        """流式计算文件哈希"""
        sha256_hash = hashlib.sha256()
        for chunk in StreamingProcessor.stream_file_read(file_path):
            sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    @staticmethod
    async def async_stream_read(file_path: str, chunk_size: int = 8192):
        """异步流式读取"""
        import aiofiles
        async with aiofiles.open(file_path, 'rb') as f:
            while True:
                chunk = await f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
