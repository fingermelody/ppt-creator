"""
向量数据库客户端模块
"""

from typing import List, Optional, Dict, Any
from app.core.config import settings


class VectorDBClient:
    """向量数据库客户端"""
    
    def __init__(self):
        self.collection_name = settings.CHROMA_COLLECTION
        self._client = None
        self._collection = None
    
    def _get_client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
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


def get_vector_client() -> VectorDBClient:
    """获取向量数据库客户端"""
    return VectorDBClient()
