"""
应用配置模块
支持从环境变量和 .env 文件加载配置
"""

import os
from functools import lru_cache
from typing import Optional, List
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


# 获取项目根目录（backend 目录的父目录）
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """应用配置类"""
    
    # ============== 基础配置 ==============
    APP_NAME: str = "PPT-RSD"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api"
    
    # ============== 服务器配置 ==============
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # ============== CORS 配置 ==============
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://ppt.bottlepeace.com",
        "https://ai-generator-1gp9p3g64d04e869-1253851367.tcloudbaseapp.com",
    ]
    
    # ============== 数据库配置（MySQL）==============
    DATABASE_URL: str = Field(
        default="mysql+pymysql://root:password@localhost:3306/ppt_rsd",
        description="MySQL 数据库连接字符串 (TDSQL-C)"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # ============== Redis 配置 ==============
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis 连接字符串"
    )
    REDIS_PREFIX: str = "ppt_rsd:"
    
    # ============== Elasticsearch Serverless 配置 ==============
    ES_HOST: str = Field(
        default="http://space-k4t5xi0i.ap-guangzhou.qcloudes.com",
        description="腾讯云 ES Serverless 访问地址"
    )
    ES_APP_ID: str = Field(
        default="space-k4t5xi0i",
        description="ES Serverless 应用 ID"
    )
    ES_USERNAME: str = Field(
        default="elastic",
        description="ES Serverless 访问用户名"
    )
    ES_PASSWORD: str = Field(
        default="caonidaye@123",
        description="ES Serverless 访问密码"
    )
    ES_INDEX_NAME: str = "ppt_slides"
    ES_USE_SSL: bool = True

    # ============== ChromaDB 配置（已弃用，使用 ES 替代）==============
    # 保留配置项以向后兼容，实际使用 ES Serverless
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION: str = "ppt_slides"
    CHROMA_USE_LOCAL: bool = True
    CHROMA_PERSIST_DIR: str = "./data/chromadb"
    
    # ============== 文件存储配置 ==============
    UPLOAD_DIR: str = "/data/uploads"
    GENERATED_DIR: str = "/data/generated"
    THUMBNAIL_DIR: str = "/data/thumbnails"
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    ALLOWED_EXTENSIONS: List[str] = [".pptx", ".ppt"]
    CHUNK_SIZE: int = 5 * 1024 * 1024  # 5MB
    
    # ============== 腾讯云 COS 配置 ==============
    COS_SECRET_ID: Optional[str] = None
    COS_SECRET_KEY: Optional[str] = None
    COS_REGION: str = "ap-guangzhou"
    COS_BUCKET: Optional[str] = None
    COS_DOMAIN: Optional[str] = None
    
    # ============== JWT 认证配置 ==============
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT 密钥"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # ============== LLM API 配置 ==============
    LLM_PROVIDER: str = Field(
        default="qwen",
        description="LLM 提供商: openai, claude, qwen, hunyuan, custom"
    )
    
    # OpenAI 配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # Claude 配置
    CLAUDE_API_KEY: Optional[str] = None
    CLAUDE_API_BASE: str = "https://api.anthropic.com"
    CLAUDE_MODEL: str = "claude-3-opus-20240229"
    
    # 通义千问配置
    QWEN_API_KEY: Optional[str] = None
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/api/v1"
    QWEN_MODEL: str = "qwen-max"
    
    # 腾讯混元配置
    HUNYUAN_SECRET_ID: Optional[str] = None
    HUNYUAN_SECRET_KEY: Optional[str] = None
    HUNYUAN_MODEL: str = "hunyuan-pro"
    
    # 自定义 API 配置
    CUSTOM_API_URL: Optional[str] = None
    CUSTOM_API_KEY: Optional[str] = None
    CUSTOM_API_MODEL: Optional[str] = None
    CUSTOM_REQUEST_TEMPLATE: Optional[str] = None
    CUSTOM_RESPONSE_PATH: Optional[str] = None
    
    # LLM 通用配置
    LLM_TIMEOUT: int = 120
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.7
    
    # ============== 向量化配置（API 模式）==============
    # 使用腾讯混元 Embedding API 替代本地 SentenceTransformer
    EMBEDDING_API_PROVIDER: str = Field(
        default="hunyuan",
        description="Embedding API 提供商: hunyuan, openai"
    )
    # 混元 Embedding 使用与 LLM 相同的腾讯云凭证 (HUNYUAN_SECRET_ID/KEY)
    EMBEDDING_DIMENSION: int = 1024  # 混元 embedding 维度
    
    # ============== 网络搜索配置 ==============
    SEARCH_ENGINE: str = Field(
        default="bing",
        description="搜索引擎: bing, google, serper"
    )
    BING_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None
    SERPER_API_KEY: Optional[str] = None
    SEARCH_MAX_RESULTS: int = 10
    SEARCH_TIMEOUT: int = 30
    
    # ============== Celery 配置 ==============
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # ============== 日志配置 ==============
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    class Config:
        env_file = str(ENV_FILE_PATH)
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 忽略额外的环境变量


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


# 导出配置实例
settings = get_settings()
