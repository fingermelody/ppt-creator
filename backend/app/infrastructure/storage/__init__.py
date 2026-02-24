"""
文件存储模块
"""

import os
import uuid
from typing import Optional
from app.core.config import settings


class StorageClient:
    """本地文件存储客户端"""
    
    def __init__(self):
        self.upload_dir = settings.UPLOAD_DIR
        self.generated_dir = settings.GENERATED_DIR
        self.thumbnail_dir = settings.THUMBNAIL_DIR
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        for d in [self.upload_dir, self.generated_dir, self.thumbnail_dir]:
            os.makedirs(d, exist_ok=True)
    
    def save_upload(self, content: bytes, filename: str) -> str:
        """保存上传文件"""
        ext = os.path.splitext(filename)[1]
        new_filename = f"{uuid.uuid4()}{ext}"
        path = os.path.join(self.upload_dir, new_filename)
        with open(path, "wb") as f:
            f.write(content)
        return path
    
    def save_generated(self, content: bytes, filename: str) -> str:
        """保存生成文件"""
        path = os.path.join(self.generated_dir, filename)
        with open(path, "wb") as f:
            f.write(content)
        return path
    
    def get_file(self, path: str) -> Optional[bytes]:
        """读取文件"""
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
        return None
    
    def delete_file(self, path: str):
        """删除文件"""
        if os.path.exists(path):
            os.remove(path)


def get_storage_client() -> StorageClient:
    """获取存储客户端"""
    return StorageClient()
