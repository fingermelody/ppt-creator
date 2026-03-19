"""
文档上传功能测试
测试分片上传的完整流程：初始化、分片上传、完成上传
"""

import pytest
import io
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 导入应用
from app.main import app
from app.db import get_db, Base
from app.core import get_current_user_id

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_user_id():
    """覆盖用户认证依赖"""
    return "test-user-123"


# 覆盖依赖
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user_id] = override_get_current_user_id


@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    # 清理
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_file():
    """创建测试文件"""
    content = b"Test file content" * 1000  # 约 17KB
    return io.BytesIO(content)


class TestUploadInit:
    """上传初始化测试"""

    def test_init_upload_success(self, client):
        """测试成功初始化上传"""
        response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": 1024000,
                "total_chunks": 2
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "upload_id" in data
        assert "chunk_size" in data
        assert data["total_chunks"] == 2
        assert len(data["upload_id"]) > 0

    def test_init_upload_missing_filename(self, client):
        """测试缺少文件名"""
        response = client.post(
            "/api/documents/upload/init",
            json={
                "filesize": 1024000,
                "total_chunks": 2
            }
        )
        assert response.status_code == 422

    def test_init_upload_invalid_filesize(self, client):
        """测试无效的文件大小"""
        response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": 0,  # 无效大小
                "total_chunks": 1
            }
        )
        assert response.status_code == 422

    def test_init_upload_invalid_chunks(self, client):
        """测试无效的分片数"""
        response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": 1024,
                "total_chunks": 0  # 无效分片数
            }
        )
        assert response.status_code == 422


class TestUploadChunk:
    """分片上传测试"""

    def test_upload_chunk_success(self, client, test_file):
        """测试成功上传分片"""
        # 先初始化上传
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": 17000,
                "total_chunks": 1
            }
        )
        upload_id = init_response.json()["upload_id"]

        # 上传分片
        response = client.post(
            "/api/documents/upload/chunk",
            data={
                "upload_id": upload_id,
                "chunk_index": "0"
            },
            files={
                "chunk": ("chunk0", test_file, "application/octet-stream")
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["received_chunks"] == 1

    def test_upload_chunk_missing_upload_id(self, client, test_file):
        """测试缺少 upload_id"""
        response = client.post(
            "/api/documents/upload/chunk",
            data={
                "chunk_index": "0"
            },
            files={
                "chunk": ("chunk0", test_file, "application/octet-stream")
            }
        )
        assert response.status_code == 422

    def test_upload_multiple_chunks(self, client):
        """测试多分片上传"""
        # 初始化上传
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "large.pptx",
                "filesize": 100000,
                "total_chunks": 3
            }
        )
        upload_id = init_response.json()["upload_id"]

        # 上传多个分片
        for i in range(3):
            chunk_content = f"chunk_{i}_content".encode() * 100
            response = client.post(
                "/api/documents/upload/chunk",
                data={
                    "upload_id": upload_id,
                    "chunk_index": str(i)
                },
                files={
                    "chunk": (f"chunk{i}", io.BytesIO(chunk_content), "application/octet-stream")
                }
            )
            assert response.status_code == 200
            assert response.json()["received_chunks"] == i + 1


class TestUploadComplete:
    """完成上传测试"""

    def test_complete_upload_success(self, client, test_file):
        """测试成功完成上传"""
        # 初始化上传
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "complete_test.pptx",
                "filesize": 17000,
                "total_chunks": 1
            }
        )
        upload_id = init_response.json()["upload_id"]

        # 上传分片
        client.post(
            "/api/documents/upload/chunk",
            data={
                "upload_id": upload_id,
                "chunk_index": "0"
            },
            files={
                "chunk": ("chunk0", test_file, "application/octet-stream")
            }
        )

        # 完成上传 - 使用 title 字段（前端实际传递的字段）
        response = client.post(
            "/api/documents/upload/complete",
            json={
                "upload_id": upload_id,
                "title": "My Test Presentation"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["status"] == "parsing"

    def test_complete_upload_missing_upload_id(self, client):
        """测试缺少 upload_id"""
        response = client.post(
            "/api/documents/upload/complete",
            json={
                "title": "Test"
            }
        )
        assert response.status_code == 422

    def test_complete_upload_missing_title(self, client):
        """测试缺少 title（修复后应该必填）"""
        # 初始化上传
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": 1000,
                "total_chunks": 1
            }
        )
        upload_id = init_response.json()["upload_id"]

        response = client.post(
            "/api/documents/upload/complete",
            json={
                "upload_id": upload_id
            }
        )
        # 修复后 title 应该是必填的
        assert response.status_code == 422


class TestFullUploadFlow:
    """完整上传流程测试"""

    def test_full_upload_flow(self, client):
        """测试完整的上传流程"""
        # 1. 初始化上传
        filename = "presentation.pptx"
        file_content = b"PPTX_MOCK_CONTENT" * 1000
        filesize = len(file_content)
        chunk_size = 5 * 1024  # 5KB per chunk
        total_chunks = (filesize + chunk_size - 1) // chunk_size

        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": filename,
                "filesize": filesize,
                "total_chunks": total_chunks
            }
        )
        assert init_response.status_code == 200
        upload_id = init_response.json()["upload_id"]

        # 2. 分片上传
        for i in range(total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, filesize)
            chunk_data = file_content[start:end]

            chunk_response = client.post(
                "/api/documents/upload/chunk",
                data={
                    "upload_id": upload_id,
                    "chunk_index": str(i)
                },
                files={
                    "chunk": (f"chunk{i}", io.BytesIO(chunk_data), "application/octet-stream")
                }
            )
            assert chunk_response.status_code == 200
            assert chunk_response.json()["success"] == True

        # 3. 完成上传
        complete_response = client.post(
            "/api/documents/upload/complete",
            json={
                "upload_id": upload_id,
                "title": "My Presentation"
            }
        )
        assert complete_response.status_code == 200
        data = complete_response.json()
        assert "document_id" in data
        assert data["status"] == "parsing"

    def test_upload_flow_with_large_file(self, client):
        """测试大文件上传流程"""
        # 模拟 10MB 文件
        file_content = b"X" * (10 * 1024 * 1024)
        filesize = len(file_content)
        chunk_size = 5 * 1024 * 1024  # 5MB per chunk
        total_chunks = (filesize + chunk_size - 1) // chunk_size

        # 初始化
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "large_file.pptx",
                "filesize": filesize,
                "total_chunks": total_chunks
            }
        )
        assert init_response.status_code == 200
        upload_id = init_response.json()["upload_id"]

        # 上传分片
        for i in range(total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, filesize)
            # 使用较小的测试数据避免内存问题
            chunk_data = b"TEST" * 1000

            chunk_response = client.post(
                "/api/documents/upload/chunk",
                data={
                    "upload_id": upload_id,
                    "chunk_index": str(i)
                },
                files={
                    "chunk": (f"chunk{i}", io.BytesIO(chunk_data), "application/octet-stream")
                }
            )
            assert chunk_response.status_code == 200

        # 完成上传
        complete_response = client.post(
            "/api/documents/upload/complete",
            json={
                "upload_id": upload_id,
                "title": "Large Presentation"
            }
        )
        assert complete_response.status_code == 200


class TestHealthEndpoint:
    """健康检查端点测试"""

    def test_health_check(self, client):
        """测试健康检查接口"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
