"""
Embedding API 客户端模块

使用腾讯混元 Embedding API 生成文本向量，替代本地 SentenceTransformer。
支持多个提供商：腾讯混元（默认）、OpenAI。
"""

import hashlib
import hmac
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    """Embedding 提供商基类"""

    @abstractmethod
    def embed_text(self, text: str) -> Optional[List[float]]:
        """生成单个文本的向量表示"""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """批量生成文本向量"""
        pass


class HunyuanEmbeddingProvider(BaseEmbeddingProvider):
    """
    腾讯混元 Embedding API 提供商

    使用 Hunyuan Embedding API (hunyuan-embedding) 生成文本向量。
    文档: https://cloud.tencent.com/document/product/1729/97731
    """

    API_HOST = "hunyuan.tencentcloudapi.com"
    API_SERVICE = "hunyuan"
    API_ACTION = "GetEmbedding"
    API_VERSION = "2023-09-01"

    def __init__(self):
        self.secret_id = settings.HUNYUAN_SECRET_ID or ""
        self.secret_key = settings.HUNYUAN_SECRET_KEY or ""
        if not self.secret_id or not self.secret_key:
            logger.warning("混元 Embedding API 凭证未配置")

    def _sign_request(self, payload: str) -> dict:
        """生成腾讯云 API v3 签名"""
        timestamp = int(time.time())
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")

        # 1. 拼接规范请求串
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        content_type = "application/json; charset=utf-8"
        canonical_headers = (
            f"content-type:{content_type}\n"
            f"host:{self.API_HOST}\n"
            f"x-tc-action:{self.API_ACTION.lower()}\n"
        )
        signed_headers = "content-type;host;x-tc-action"
        hashed_payload = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request = (
            f"{http_request_method}\n{canonical_uri}\n{canonical_querystring}\n"
            f"{canonical_headers}\n{signed_headers}\n{hashed_payload}"
        )

        # 2. 拼接待签名字符串
        algorithm = "TC3-HMAC-SHA256"
        credential_scope = f"{date}/{self.API_SERVICE}/tc3_request"
        hashed_canonical_request = hashlib.sha256(
            canonical_request.encode("utf-8")
        ).hexdigest()
        string_to_sign = (
            f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashed_canonical_request}"
        )

        # 3. 计算签名
        def _hmac_sha256(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

        secret_date = _hmac_sha256(
            f"TC3{self.secret_key}".encode("utf-8"), date
        )
        secret_service = _hmac_sha256(secret_date, self.API_SERVICE)
        secret_signing = _hmac_sha256(secret_service, "tc3_request")
        signature = hmac.new(
            secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        # 4. 拼接 Authorization
        authorization = (
            f"{algorithm} Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        return {
            "Content-Type": content_type,
            "Host": self.API_HOST,
            "X-TC-Action": self.API_ACTION,
            "X-TC-Version": self.API_VERSION,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Region": settings.COS_REGION or "ap-guangzhou",
            "Authorization": authorization,
        }

    def _call_api(self, texts: List[str]) -> Optional[List[List[float]]]:
        """调用混元 Embedding API"""
        if not self.secret_id or not self.secret_key:
            logger.error("混元 Embedding API 凭证未配置")
            return None

        payload = json.dumps({"Input": texts})
        headers = self._sign_request(payload)

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"https://{self.API_HOST}",
                    headers=headers,
                    content=payload,
                )
                response.raise_for_status()
                data = response.json()

                if "Response" in data and "Data" in data["Response"]:
                    embeddings = []
                    for item in data["Response"]["Data"]:
                        embeddings.append(item["Embedding"])
                    return embeddings
                elif "Response" in data and "Error" in data["Response"]:
                    error = data["Response"]["Error"]
                    logger.error(
                        f"混元 Embedding API 错误: {error.get('Code')} - {error.get('Message')}"
                    )
                    return None
                else:
                    logger.error(f"混元 Embedding API 返回格式异常: {data}")
                    return None

        except httpx.HTTPStatusError as e:
            logger.error(f"混元 Embedding API HTTP 错误: {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"混元 Embedding API 调用失败: {e}")
            return None

    def embed_text(self, text: str) -> Optional[List[float]]:
        """生成单个文本的向量"""
        result = self._call_api([text])
        if result and len(result) > 0:
            return result[0]
        return None

    def embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        """批量生成文本向量（混元 API 单次最多支持 16 条）"""
        all_embeddings = []
        batch_size = 16

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            result = self._call_api(batch)
            if result is None:
                return None
            all_embeddings.extend(result)

        return all_embeddings


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI Embedding API 提供商（备选）"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY or ""
        self.api_base = settings.OPENAI_API_BASE or "https://api.openai.com/v1"
        self.model = "text-embedding-3-small"

    def _call_api(self, texts: List[str]) -> Optional[List[List[float]]]:
        """调用 OpenAI Embedding API"""
        if not self.api_key:
            logger.error("OpenAI API Key 未配置")
            return None

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/embeddings",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model, "input": texts},
                )
                response.raise_for_status()
                data = response.json()
                return [item["embedding"] for item in data["data"]]

        except Exception as e:
            logger.error(f"OpenAI Embedding API 调用失败: {e}")
            return None

    def embed_text(self, text: str) -> Optional[List[float]]:
        result = self._call_api([text])
        if result and len(result) > 0:
            return result[0]
        return None

    def embed_batch(self, texts: List[str]) -> Optional[List[List[float]]]:
        return self._call_api(texts)


# 提供商工厂
_PROVIDERS = {
    "hunyuan": HunyuanEmbeddingProvider,
    "openai": OpenAIEmbeddingProvider,
}


def get_embedding_provider() -> BaseEmbeddingProvider:
    """获取 Embedding 提供商实例"""
    provider_name = getattr(settings, "EMBEDDING_API_PROVIDER", "hunyuan")
    provider_cls = _PROVIDERS.get(provider_name)
    if not provider_cls:
        raise ValueError(f"不支持的 Embedding 提供商: {provider_name}")
    return provider_cls()
