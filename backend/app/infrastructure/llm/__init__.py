"""
LLM API 客户端模块
支持多个云服务提供商的统一接口
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from app.core.config import settings


class BaseLLMProvider(ABC):
    """LLM 提供商基类"""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """聊天补全接口"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API 提供商"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.OPENAI_API_BASE
        self.model = settings.OPENAI_MODEL
    
    async def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> str:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
                timeout=settings.LLM_TIMEOUT
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


class QwenProvider(BaseLLMProvider):
    """通义千问 API 提供商"""
    
    def __init__(self):
        self.api_key = settings.QWEN_API_KEY
        self.api_base = settings.QWEN_API_BASE
        self.model = settings.QWEN_MODEL
    
    async def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 4096, **kwargs) -> str:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/services/aigc/text-generation/generation",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": {"messages": messages}, "parameters": {"temperature": temperature, "max_tokens": max_tokens}},
                timeout=settings.LLM_TIMEOUT
            )
            response.raise_for_status()
            return response.json()["output"]["text"]


class LLMAPIClient:
    """LLM API 统一客户端"""
    
    def __init__(self, provider: Optional[str] = None):
        provider = provider or settings.LLM_PROVIDER
        self.provider = self._create_provider(provider)
    
    def _create_provider(self, provider: str) -> BaseLLMProvider:
        providers = {"openai": OpenAIProvider, "qwen": QwenProvider}
        if provider not in providers:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")
        return providers[provider]()
    
    async def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        return await self.provider.chat_completion(messages, **kwargs)


def get_llm_client() -> LLMAPIClient:
    """获取 LLM 客户端实例"""
    return LLMAPIClient()
