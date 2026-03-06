"""
腾讯云 COS 上传服务
专用于 PPT 文件存储
"""

import os
import logging
from datetime import datetime
from typing import Optional, Tuple
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


class COSUploadService:
    """
    腾讯云 COS 文件上传服务
    存储桶：ppt-creator-store-1253851367（广州地域）
    专用于存储 PPT 文件
    """
    
    # PPT 文件存储前缀
    PPT_PREFIX = "ppt-files"
    
    def __init__(self):
        # 从配置文件获取配置（优先使用配置文件，兼容环境变量）
        self.secret_id = settings.COS_SECRET_ID or os.getenv('COS_SECRET_ID')
        self.secret_key = settings.COS_SECRET_KEY or os.getenv('COS_SECRET_KEY')
        self.region = settings.COS_REGION or os.getenv('COS_REGION', 'ap-guangzhou')
        self.bucket = settings.COS_BUCKET or os.getenv('COS_BUCKET')
        self.domain = settings.COS_DOMAIN or os.getenv('COS_DOMAIN')
        
        # 初始化 COS 客户端
        if self.secret_id and self.secret_key and self.bucket:
            config = CosConfig(
                Region=self.region,
                SecretId=self.secret_id,
                SecretKey=self.secret_key
            )
            self.client = CosS3Client(config)
            self.enabled = True
            logger.info(f"COS 服务初始化成功，存储桶: {self.bucket}，区域: {self.region}")
        else:
            self.client = None
            self.enabled = False
            missing = []
            if not self.secret_id:
                missing.append('COS_SECRET_ID')
            if not self.secret_key:
                missing.append('COS_SECRET_KEY')
            if not self.bucket:
                missing.append('COS_BUCKET')
            logger.warning(f"COS 配置不完整，缺少: {', '.join(missing)}，文件上传功能将不可用")
    
    def _get_cos_url(self, object_key: str) -> str:
        """
        获取 COS 对象的公开访问 URL
        
        Args:
            object_key: COS 对象键
            
        Returns:
            公开访问 URL
        """
        if self.domain:
            return f"https://{self.domain}/{object_key}"
        else:
            return f"https://{self.bucket}.cos.{self.region}.myqcloud.com/{object_key}"
    
    def upload_ppt(
        self,
        file_path: str,
        document_id: str,
        original_filename: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        上传 PPT 文件到 COS 永久存储
        
        Args:
            file_path: 本地文件路径
            document_id: 文档 ID
            original_filename: 原始文件名
        
        Returns:
            (object_key, cos_url) 元组，上传失败返回 (None, None)
        """
        if not self.enabled:
            logger.error("COS 服务未启用，无法上传 PPT")
            return None, None
        
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None, None
        
        try:
            # 生成对象键：ppt-files/{year}/{month}/{document_id}/{filename}
            now = datetime.utcnow()
            file_ext = os.path.splitext(original_filename)[1].lower()
            object_key = f"{self.PPT_PREFIX}/{now.year}/{now.month:02d}/{document_id}/{document_id}{file_ext}"
            
            # 上传文件
            with open(file_path, 'rb') as fp:
                self.client.put_object(
                    Bucket=self.bucket,
                    Body=fp,
                    Key=object_key,
                    EnableMD5=False,
                    ContentType='application/vnd.openxmlformats-officedocument.presentationml.presentation'
                )
            
            cos_url = self._get_cos_url(object_key)
            logger.info(f"PPT 上传成功: {object_key}, URL: {cos_url}")
            
            return object_key, cos_url
            
        except Exception as e:
            logger.error(f"上传 PPT 失败: {e}")
            return None, None
    
    def delete_ppt(self, object_key: str) -> bool:
        """
        从 COS 删除 PPT 文件
        
        Args:
            object_key: COS 对象键
            
        Returns:
            是否删除成功
        """
        if not self.enabled:
            logger.error("COS 服务未启用")
            return False
        
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=object_key
            )
            logger.info(f"PPT 删除成功: {object_key}")
            return True
        except Exception as e:
            logger.error(f"删除 PPT 失败: {e}")
            return False
    
    def get_presigned_url(
        self,
        object_key: str,
        expires: int = 3600
    ) -> Optional[str]:
        """
        获取 COS 对象的临时签名 URL
        
        Args:
            object_key: COS 对象键
            expires: 有效期（秒，默认 1 小时）
        
        Returns:
            签名 URL 或 None
        """
        if not self.enabled:
            logger.error("COS 服务未启用")
            return None
        
        try:
            url = self.client.get_presigned_url(
                Method='GET',
                Bucket=self.bucket,
                Key=object_key,
                Expired=expires
            )
            return url
        except Exception as e:
            logger.error(f"生成签名 URL 失败: {e}")
            return None
    
    def get_preview_url(
        self,
        object_key: str,
        expires: int = 7200,
        use_ci: bool = True  # 使用腾讯云数据万象（存储桶已绑定）
    ) -> Optional[str]:
        """
        获取文档预览 URL
        
        Args:
            object_key: COS 对象键
            expires: 临时 URL 有效期（秒，默认 2 小时）
            use_ci: 是否使用腾讯云数据万象（CI）预览，默认 True
        
        Returns:
            预览 URL 或 None
        """
        url = self.get_presigned_url(object_key, expires)
        
        if url:
            if use_ci:
                # 使用腾讯云数据万象（CI）进行文档预览
                separator = '&' if '?' in url else '?'
                preview_url = f"{url}{separator}ci-process=doc-preview&dstType=html"
                return preview_url
            else:
                # 备选方案：使用微软 Office Online Viewer
                from urllib.parse import quote
                encoded_url = quote(url, safe='')
                preview_url = f"https://view.officeapps.live.com/op/embed.aspx?src={encoded_url}"
                return preview_url
        
        return None
    
    def get_download_url(
        self,
        object_key: str,
        expires: int = 3600
    ) -> Optional[str]:
        """
        获取文件下载 URL（不带预览参数）
        
        Args:
            object_key: COS 对象键
            expires: 临时 URL 有效期（秒，默认 1 小时）
        
        Returns:
            下载 URL 或 None
        """
        return self.get_presigned_url(object_key, expires)
    
    # 保持向后兼容的旧方法
    def upload_file(
        self,
        file_path: str,
        object_key: Optional[str] = None,
        expires: int = 3600
    ) -> Optional[str]:
        """
        上传文件到 COS 并返回临时访问 URL（向后兼容）
        
        Args:
            file_path: 本地文件路径
            object_key: COS 对象键（可选，默认自动生成）
            expires: 临时 URL 有效期（秒，默认 1 小时）
        
        Returns:
            临时访问 URL 或 None
        """
        if not self.enabled:
            logger.error("COS 服务未启用")
            return None
        
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
        
        try:
            # 生成对象键
            if not object_key:
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                unique_id = uuid.uuid4().hex[:8]
                filename = os.path.basename(file_path)
                object_key = f"temp/{timestamp}_{unique_id}/{filename}"
            
            # 上传文件
            with open(file_path, 'rb') as fp:
                self.client.put_object(
                    Bucket=self.bucket,
                    Body=fp,
                    Key=object_key,
                    EnableMD5=False
                )
            
            logger.info(f"文件上传成功: {object_key}")
            
            # 生成临时访问 URL
            url = self.client.get_presigned_url(
                Method='GET',
                Bucket=self.bucket,
                Key=object_key,
                Expired=expires
            )
            
            return url
            
        except Exception as e:
            logger.error(f"上传文件失败: {e}")
            return None


# 全局单例
cos_upload_service = COSUploadService()
