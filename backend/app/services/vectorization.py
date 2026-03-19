"""
向量化服务

将 PPT 页面内容转换为向量数据。
使用腾讯混元 Embedding API 生成向量，Elasticsearch Serverless 存储和检索。
不再依赖本地 SentenceTransformer 和 ChromaDB。
"""

import logging
from typing import List, Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorizationService:
    """向量化服务（API 模式）"""

    def __init__(self):
        self._embedding_provider = None
        self._vector_client = None
        self.enabled = False

        # 初始化
        self._init_services()

    def _init_services(self):
        """初始化向量化相关服务"""
        try:
            # 加载 Embedding API 提供商
            from app.infrastructure.embedding_api import get_embedding_provider
            self._embedding_provider = get_embedding_provider()
            logger.info(f"Embedding API 提供商加载成功: {settings.EMBEDDING_API_PROVIDER}")

            # 连接 ES 向量数据库
            from app.infrastructure.vector import get_vector_client
            self._vector_client = get_vector_client()

            self.enabled = True
            logger.info("向量化服务初始化成功（API 模式）")

        except Exception as e:
            logger.warning(f"向量化服务初始化失败: {e}")
            self.enabled = False

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        生成文本的向量表示（通过 API 调用）

        Args:
            text: 输入文本

        Returns:
            向量列表或 None
        """
        if not self.enabled or not self._embedding_provider:
            logger.warning("向量化服务未启用")
            return None

        if not text or not text.strip():
            logger.warning("输入文本为空")
            return None

        try:
            # 限制文本长度（混元 API 有 token 限制）
            text = text[:5000]
            embedding = self._embedding_provider.embed_text(text)
            return embedding
        except Exception as e:
            logger.error(f"生成向量失败: {e}")
            return None

    def vectorize_slide(
        self,
        slide_id: str,
        document_id: str,
        page_number: int,
        content_text: str,
        title: Optional[str] = None,
        source_url: Optional[str] = None,
        source_filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        向量化单个页面

        Args:
            slide_id: 页面 ID
            document_id: 文档 ID
            page_number: 页码（从1开始）
            content_text: 页面文本内容
            title: 页面标题
            source_url: 源 PPT 的 COS URL
            source_filename: 源 PPT 的原始文件名
            metadata: 附加元数据

        Returns:
            向量 ID 或 None
        """
        if not self.enabled:
            logger.warning("向量化服务未启用，跳过向量化")
            return None

        # 构建向量化的文本（标题 + 内容）
        full_text = ""
        if title:
            full_text = f"{title}\n{content_text}"
        else:
            full_text = content_text

        if not full_text.strip():
            logger.warning(f"页面 {slide_id} 内容为空，跳过向量化")
            return None

        # 生成向量
        embedding = self.generate_embedding(full_text)
        if not embedding:
            logger.error(f"页面 {slide_id} 向量生成失败")
            return None

        # 生成向量 ID
        vector_id = f"slide_{slide_id}"

        # 准备元数据
        doc_metadata = {
            "document_id": document_id,
            "slide_id": slide_id,
            "page_number": page_number,
            "title": title or "",
            "source_url": source_url or "",
            "source_filename": source_filename or "",
        }
        if metadata:
            doc_metadata.update(metadata)

        try:
            # 存储到 ES 向量数据库
            self._vector_client.add_documents(
                ids=[vector_id],
                documents=[full_text],
                embeddings=[embedding],
                metadatas=[doc_metadata],
            )

            logger.info(
                f"页面 {slide_id} 向量化成功，向量 ID: {vector_id}，"
                f"源: {source_filename} 第{page_number}页"
            )
            return vector_id

        except Exception as e:
            logger.error(f"存储向量失败: {e}")
            return None

    def delete_document_vectors(
        self, document_id: str, slide_ids: List[str]
    ) -> bool:
        """
        删除文档的所有向量

        Args:
            document_id: 文档 ID
            slide_ids: 页面 ID 列表

        Returns:
            是否成功
        """
        if not self.enabled or not self._vector_client:
            return True

        try:
            vector_ids = [f"slide_{sid}" for sid in slide_ids]
            if vector_ids:
                self._vector_client.delete(vector_ids)
                logger.info(
                    f"删除文档 {document_id} 的 {len(vector_ids)} 个向量"
                )
            return True
        except Exception as e:
            logger.error(f"删除向量失败: {e}")
            return False

    def search_similar_slides(
        self,
        query: str,
        n_results: int = 10,
        document_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索相似页面

        Args:
            query: 查询文本
            n_results: 返回结果数量
            document_id: 限制在特定文档内搜索

        Returns:
            搜索结果列表
        """
        if not self.enabled:
            return []

        # 生成查询向量
        query_embedding = self.generate_embedding(query)
        if not query_embedding:
            return []

        try:
            # 构建过滤条件
            where = None
            if document_id:
                where = {"document_id": document_id}

            # 搜索
            results = self._vector_client.search(
                query_embedding=query_embedding,
                n_results=n_results,
                where=where,
            )

            # 格式化结果
            formatted_results = []
            if results and "ids" in results and results["ids"]:
                ids = results["ids"][0] if results["ids"] else []
                documents = (
                    results.get("documents", [[]])[0]
                    if results.get("documents")
                    else []
                )
                metadatas = (
                    results.get("metadatas", [[]])[0]
                    if results.get("metadatas")
                    else []
                )
                distances = (
                    results.get("distances", [[]])[0]
                    if results.get("distances")
                    else []
                )

                for i, vid in enumerate(ids):
                    meta = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else 0

                    # 计算相似度分数（距离越小越相似）
                    similarity = max(0, 1 - distance)

                    formatted_results.append(
                        {
                            "vector_id": vid,
                            "content": documents[i] if i < len(documents) else "",
                            "metadata": meta,
                            "distance": distance,
                            "similarity": round(similarity, 4),
                            # 便于访问的关键字段
                            "slide_id": meta.get("slide_id", ""),
                            "document_id": meta.get("document_id", ""),
                            "page_number": meta.get("page_number", 0),
                            "title": meta.get("title", ""),
                            "source_url": meta.get("source_url", ""),
                            "source_filename": meta.get("source_filename", ""),
                        }
                    )

            return formatted_results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []


# 全局单例（延迟初始化）
_vectorization_service = None


def get_vectorization_service() -> VectorizationService:
    """获取向量化服务实例"""
    global _vectorization_service
    if _vectorization_service is None:
        _vectorization_service = VectorizationService()
    return _vectorization_service
