"""
向量数据库客户端模块

使用腾讯云 Elasticsearch Serverless 作为向量存储后端，
替代本地 ChromaDB，消除对 chromadb 和 sentence-transformers 的依赖。
"""

import logging
from typing import List, Optional, Dict, Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorDBClient:
    """
    Elasticsearch Serverless 向量数据库客户端
    
    使用 ES 的 dense_vector 字段存储和检索向量，
    替代 ChromaDB 的本地存储。
    """

    def __init__(self):
        self.index_name = settings.ES_INDEX_NAME or "ppt_slides"
        self._es_host = settings.ES_HOST or "http://localhost:9200"
        self._es_username = settings.ES_USERNAME or "elastic"
        self._es_password = settings.ES_PASSWORD or ""
        self._dimension = getattr(settings, "EMBEDDING_DIMENSION", 1024)
        self._initialized = False

    def _get_auth(self):
        """获取 ES 认证信息"""
        return (self._es_username, self._es_password)

    def _get_base_url(self) -> str:
        """获取 ES 基础 URL"""
        return self._es_host.rstrip("/")

    def _ensure_index(self):
        """确保索引存在，如不存在则创建（含 dense_vector 映射）"""
        if self._initialized:
            return

        url = f"{self._get_base_url()}/{self.index_name}"
        try:
            with httpx.Client(timeout=10.0, verify=False) as client:
                # 检查索引是否存在
                resp = client.head(url, auth=self._get_auth())
                if resp.status_code == 200:
                    self._initialized = True
                    logger.info(f"ES 索引 {self.index_name} 已存在")
                    return

                # 创建索引
                mapping = {
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                    },
                    "mappings": {
                        "properties": {
                            "vector_id": {"type": "keyword"},
                            "content": {"type": "text", "analyzer": "ik_max_word", "search_analyzer": "ik_smart"},
                            "embedding": {
                                "type": "dense_vector",
                                "dims": self._dimension,
                                "index": True,
                                "similarity": "cosine",
                            },
                            "document_id": {"type": "keyword"},
                            "slide_id": {"type": "keyword"},
                            "page_number": {"type": "integer"},
                            "title": {"type": "text", "analyzer": "ik_max_word"},
                            "source_url": {"type": "keyword"},
                            "source_filename": {"type": "keyword"},
                        }
                    },
                }

                resp = client.put(url, json=mapping, auth=self._get_auth())
                if resp.status_code in (200, 201):
                    self._initialized = True
                    logger.info(f"ES 索引 {self.index_name} 创建成功")
                else:
                    # 可能不支持 ik 分词器，降级使用 standard
                    logger.warning(f"ES 索引创建失败 ({resp.status_code})，尝试降级映射")
                    mapping["mappings"]["properties"]["content"] = {"type": "text"}
                    mapping["mappings"]["properties"]["title"] = {"type": "text"}
                    resp = client.put(url, json=mapping, auth=self._get_auth())
                    if resp.status_code in (200, 201):
                        self._initialized = True
                        logger.info(f"ES 索引 {self.index_name} 创建成功（降级映射）")
                    else:
                        logger.error(f"ES 索引创建失败: {resp.status_code} {resp.text}")

        except Exception as e:
            logger.error(f"ES 索引初始化失败: {e}")

    def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
    ):
        """添加文档到向量数据库"""
        self._ensure_index()

        url = f"{self._get_base_url()}/{self.index_name}/_bulk"
        bulk_body = ""

        for i, doc_id in enumerate(ids):
            meta = metadatas[i] if metadatas and i < len(metadatas) else {}
            action = {"index": {"_index": self.index_name, "_id": doc_id}}
            doc = {
                "vector_id": doc_id,
                "content": documents[i] if i < len(documents) else "",
                "embedding": embeddings[i] if i < len(embeddings) else [],
                "document_id": meta.get("document_id", ""),
                "slide_id": meta.get("slide_id", ""),
                "page_number": meta.get("page_number", 0),
                "title": meta.get("title", ""),
                "source_url": meta.get("source_url", ""),
                "source_filename": meta.get("source_filename", ""),
            }

            import json
            bulk_body += json.dumps(action) + "\n"
            bulk_body += json.dumps(doc) + "\n"

        try:
            with httpx.Client(timeout=30.0, verify=False) as client:
                resp = client.post(
                    url,
                    content=bulk_body,
                    headers={"Content-Type": "application/x-ndjson"},
                    auth=self._get_auth(),
                )
                if resp.status_code not in (200, 201):
                    logger.error(f"ES bulk 写入失败: {resp.status_code} {resp.text[:500]}")
                else:
                    data = resp.json()
                    if data.get("errors"):
                        for item in data.get("items", []):
                            if "error" in item.get("index", {}):
                                logger.error(f"ES 文档写入错误: {item['index']['error']}")
                    else:
                        logger.debug(f"ES bulk 写入成功: {len(ids)} 条文档")

        except Exception as e:
            logger.error(f"ES 写入失败: {e}")

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        向量相似度搜索

        返回格式与之前 ChromaDB 兼容:
        {
            "ids": [[id1, id2, ...]],
            "documents": [[doc1, doc2, ...]],
            "metadatas": [[meta1, meta2, ...]],
            "distances": [[dist1, dist2, ...]]
        }
        """
        self._ensure_index()

        url = f"{self._get_base_url()}/{self.index_name}/_search"

        # 构建 knn 查询
        knn_query = {
            "field": "embedding",
            "query_vector": query_embedding,
            "k": n_results,
            "num_candidates": max(n_results * 2, 50),
        }

        # 添加过滤条件
        if where:
            filters = []
            for key, value in where.items():
                filters.append({"term": {key: value}})
            knn_query["filter"] = {"bool": {"must": filters}}

        body = {
            "size": n_results,
            "knn": knn_query,
            "_source": [
                "vector_id", "content", "document_id", "slide_id",
                "page_number", "title", "source_url", "source_filename",
            ],
        }

        try:
            with httpx.Client(timeout=30.0, verify=False) as client:
                resp = client.post(url, json=body, auth=self._get_auth())
                if resp.status_code != 200:
                    logger.error(f"ES 搜索失败: {resp.status_code} {resp.text[:500]}")
                    return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])

                ids = []
                documents = []
                metadatas = []
                distances = []

                for hit in hits:
                    source = hit.get("_source", {})
                    score = hit.get("_score", 0)
                    # ES cosine similarity 返回 0-1 分数，转换为距离
                    # distance = 1 - score (越小越相似)
                    distance = max(0, 1 - score) if score else 1.0

                    ids.append(hit.get("_id", ""))
                    documents.append(source.get("content", ""))
                    metadatas.append({
                        "document_id": source.get("document_id", ""),
                        "slide_id": source.get("slide_id", ""),
                        "page_number": source.get("page_number", 0),
                        "title": source.get("title", ""),
                        "source_url": source.get("source_url", ""),
                        "source_filename": source.get("source_filename", ""),
                    })
                    distances.append(distance)

                return {
                    "ids": [ids],
                    "documents": [documents],
                    "metadatas": [metadatas],
                    "distances": [distances],
                }

        except Exception as e:
            logger.error(f"ES 搜索失败: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def delete(self, ids: List[str]):
        """删除文档"""
        self._ensure_index()

        url = f"{self._get_base_url()}/{self.index_name}/_bulk"
        bulk_body = ""
        import json
        for doc_id in ids:
            action = {"delete": {"_index": self.index_name, "_id": doc_id}}
            bulk_body += json.dumps(action) + "\n"

        try:
            with httpx.Client(timeout=30.0, verify=False) as client:
                resp = client.post(
                    url,
                    content=bulk_body,
                    headers={"Content-Type": "application/x-ndjson"},
                    auth=self._get_auth(),
                )
                if resp.status_code not in (200, 201):
                    logger.error(f"ES 删除失败: {resp.status_code}")
                else:
                    logger.debug(f"ES 删除成功: {len(ids)} 条文档")

        except Exception as e:
            logger.error(f"ES 删除失败: {e}")

    def count(self) -> int:
        """获取集合中的文档数量"""
        self._ensure_index()

        url = f"{self._get_base_url()}/{self.index_name}/_count"
        try:
            with httpx.Client(timeout=10.0, verify=False) as client:
                resp = client.get(url, auth=self._get_auth())
                if resp.status_code == 200:
                    return resp.json().get("count", 0)
        except Exception as e:
            logger.error(f"ES 计数失败: {e}")

        return 0


def get_vector_client() -> VectorDBClient:
    """获取向量数据库客户端"""
    return VectorDBClient()
