"""
测试配置模块
"""

import os
import pytest
from typing import Generator
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# 设置测试环境变量
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.db.base import Base
from app.db import get_db
import app.models  # noqa: F401 — register all models with Base


# 创建测试数据库引擎
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    创建测试数据库会话
    每个测试函数都会获得一个干净的数据库
    """
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # 清理所有表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """
    创建测试客户端
    """
    from fastapi.testclient import TestClient
    from app.main import app
    
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_id() -> str:
    """模拟用户ID"""
    return "test-user-001"


@pytest.fixture
def sample_outline_data() -> dict:
    """示例大纲数据"""
    return {
        "title": "测试PPT大纲",
        "topic": "人工智能发展趋势",
        "sections": [
            {
                "title": "引言",
                "content": "介绍AI的背景和发展历史",
                "order": 1
            },
            {
                "title": "技术发展",
                "content": "详细讲解AI技术的演进",
                "order": 2
            },
            {
                "title": "应用场景",
                "content": "展示AI在各行业的应用",
                "order": 3
            },
            {
                "title": "未来展望",
                "content": "分析AI的发展趋势",
                "order": 4
            }
        ]
    }


@pytest.fixture
def sample_template_data() -> dict:
    """示例模板数据"""
    return {
        "name": "商务简约模板",
        "description": "适合商务演示的简约风格模板",
        "category": "business",
        "thumbnail_url": "https://example.com/thumb.png",
        "preview_images": ["https://example.com/preview1.png"],
        "color_scheme": {
            "primary": "#2563EB",
            "secondary": "#1E40AF",
            "background": "#FFFFFF",
            "text": "#1F2937"
        }
    }


@pytest.fixture
def sample_version_data() -> dict:
    """示例版本数据"""
    return {
        "ppt_id": "test-ppt-001",
        "version_type": "manual",
        "description": "手动保存的版本",
        "content_snapshot": {
            "pages": [
                {"id": 1, "title": "首页", "content": "欢迎"}
            ]
        }
    }
