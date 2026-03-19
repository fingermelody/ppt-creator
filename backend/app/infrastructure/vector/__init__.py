"""
向量数据库客户端模块
支持本地持久化模式和远程 HTTP 模式
"""

import os
import logging
from typing import List, Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorDBClient:
    """向量数据库客户端"""
    
    def __init__(self):
        self.collection_name = settings.CHROMA_COLLECTION
        self._client = None
        self._collection = None
        # 默认使用本地持久化模式
        self._use_local = getattr(settings, 'CHROMA_USE_LOCAL', True)
        # 本地数据存储路径
        self._persist_directory = getattr(settings, 'CHROMA_PERSIST_DIR', './data/chromadb')
    
    def _get_client(self):
        if self._client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            if self._use_local:
                # 使用本地持久化模式
                persist_path = os.path.abspath(self._persist_directory)
                os.makedirs(persist_path, exist_ok=True)
                
                self._client = chromadb.PersistentClient(
                    path=persist_path,
                    settings=ChromaSettings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                logger.info(f"ChromaDB 本地持久化模式已启用，数据目录: {persist_path}")
            else:
                # 使用远程 HTTP 模式
                self._client = chromadb.HttpClient(
                    host=settings.CHROMA_HOST, 
                    port=settings.CHROMA_PORT
                )
                logger.info(f"ChromaDB HTTP 模式已启用，服务器: {settings.CHROMA_HOST}:{settings.CHROMA_PORT}")
                
        return self._client
    
    def _get_collection(self):
        if self._collection is None:
            self._collection = self._get_client().get_or_create_collection(name=self.collection_name)
        return self._collection
    
    def add_documents(self, ids: List[str], documents: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict]] = None):
        """添加文档到向量数据库"""
        self._get_collection().add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
    
    def search(self, query_embedding: List[float], n_results: int = 10, where: Optional[Dict] = None) -> Dict[str, Any]:
        """向量相似度搜索"""
        return self._get_collection().query(query_embeddings=[query_embedding], n_results=n_results, where=where)
    
    def delete(self, ids: List[str]):
        """删除文档"""
        self._get_collection().delete(ids=ids)
    
    def count(self) -> int:
        """获取集合中的文档数量"""
        return self._get_collection().count()


def get_vector_client() -> VectorDBClient:
    """获取向量数据库客户端"""
    return VectorDBClient()
