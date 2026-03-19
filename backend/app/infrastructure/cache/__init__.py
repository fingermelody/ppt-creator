"""
缓存客户端模块
"""

from typing import Optional, Any
import json
from app.core.config import settings


class CacheClient:
    """Redis 缓存客户端"""
    
    def __init__(self):
        self._client = None
        self.prefix = settings.REDIS_PREFIX
    
    def _get_client(self):
        if self._client is None:
            import redis
            self._client = redis.from_url(settings.REDIS_URL)
        return self._client
    
    def _key(self, key: str) -> str:
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        value = self._get_client().get(self._key(key))
        return json.loads(value) if value else None
    
    def set(self, key: str, value: Any, expire: int = 3600):
        """设置缓存值"""
        self._get_client().setex(self._key(key), expire, json.dumps(value))
    
    def delete(self, key: str):
        """删除缓存"""
        self._get_client().delete(self._key(key))


def get_cache_client() -> CacheClient:
    """获取缓存客户端"""
    return CacheClient()
