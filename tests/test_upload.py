"""
PPT 上传模块测试用例
验证文档上传、分片上传、文件解析等功能
"""

import pytest
import hashlib
from io import BytesIO


class TestUploadInit:
    """上传初始化测试"""
    
    def test_init_upload_success(self, client, mock_auth_headers):
        """测试正常初始化上传"""
        response = client.post(
            "/api/v1/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": 1024000,
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "upload_id" in data
        assert data["total_chunks"] == 1
        assert data["chunk_size"] > 0
    
    def test_init_upload_large_file(self, client, mock_auth_headers):
        """测试大文件分片上传初始化"""
        file_size = 50 * 1024 * 1024  # 50MB
        chunk_size = 5 * 1024 * 1024  # 5MB
        total_chunks = (file_size + chunk_size - 1) // chunk_size
        
        response = client.post(
            "/api/v1/documents/upload/init",
            json={
                "filename": "large_presentation.pptx",
                "filesize": file_size,
                "total_chunks": total_chunks
            },
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_chunks"] == total_chunks
    
    def test_init_upload_invalid_filename(self, client, mock_auth_headers):
        """测试无效文件名"""
        response = client.post(
            "/api/v1/documents/upload/init",
            json={
                "filename": "",
                "filesize": 1024,
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        
        # 空文件名应该返回验证错误
        assert response.status_code in [400, 422]
    
    def test_init_upload_zero_size(self, client, mock_auth_headers):
        """测试零字节文件"""
        response = client.post(
            "/api/v1/documents/upload/init",
            json={
                "filename": "empty.pptx",
                "filesize": 0,
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        
        # 零字节应该返回验证错误
        assert response.status_code in [400, 422]


class TestUploadChunk:
    """分片上传测试"""
    
    def test_upload_single_chunk(self, client, mock_auth_headers, sample_pptx_file):
        """测试单分片上传"""
        # 先初始化
        init_response = client.post(
            "/api/v1/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": len(sample_pptx_file),
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        upload_id = init_response.json()["upload_id"]
        
        # 上传分片
        response = client.post(
            "/api/v1/documents/upload/chunk",
            data={
                "upload_id": upload_id,
                "chunk_index": 0
            },
            files={
                "chunk": ("chunk_0", BytesIO(sample_pptx_file), "application/octet-stream")
            },
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["received_chunks"] == 1
    
    def test_upload_multiple_chunks(self, client, mock_auth_headers, large_sample_pptx):
        """测试多分片上传"""
        chunk_size = 5 * 1024 * 1024
        total_chunks = (len(large_sample_pptx) + chunk_size - 1) // chunk_size
        
        # 初始化
        init_response = client.post(
            "/api/v1/documents/upload/init",
            json={
                "filename": "large.pptx",
                "filesize": len(large_sample_pptx),
                "total_chunks": total_chunks
            },
            headers=mock_auth_headers
        )
        upload_id = init_response.json()["upload_id"]
        
        # 上传每个分片
        for i in range(total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, len(large_sample_pptx))
            chunk_data = large_sample_pptx[start:end]
            
            response = client.post(
                "/api/v1/documents/upload/chunk",
                data={
                    "upload_id": upload_id,
                    "chunk_index": i
                },
                files={
                    "chunk": (f"chunk_{i}", BytesIO(chunk_data), "application/octet-stream")
                },
                headers=mock_auth_headers
            )
            
            assert response.status_code == 200
            assert response.json()["received_chunks"] == i + 1


class TestUploadComplete:
    """上传完成测试"""
    
    def test_complete_upload_success(self, client, mock_auth_headers, sample_pptx_file):
        """测试完成上传"""
        # 初始化
        init_response = client.post(
            "/api/v1/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": len(sample_pptx_file),
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        upload_id = init_response.json()["upload_id"]
        
        # 上传分片
        client.post(
            "/api/v1/documents/upload/chunk",
            data={
                "upload_id": upload_id,
                "chunk_index": 0
            },
            files={
                "chunk": ("chunk_0", BytesIO(sample_pptx_file), "application/octet-stream")
            },
            headers=mock_auth_headers
        )
        
        # 完成上传
        md5_hash = hashlib.md5(sample_pptx_file).hexdigest()
        response = client.post(
            "/api/v1/documents/upload/complete",
            json={
                "upload_id": upload_id,
                "filename": "测试演示文稿.pptx",
                "md5_hash": md5_hash
            },
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["status"] == "parsing"


class TestDocumentList:
    """文档列表测试"""
    
    def test_get_documents_empty(self, client, mock_auth_headers):
        """测试空文档列表"""
        response = client.get(
            "/api/v1/documents",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert data["total"] >= 0
    
    def test_get_documents_with_data(self, client, mock_auth_headers, sample_document):
        """测试有数据的文档列表"""
        response = client.get(
            "/api/v1/documents",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) >= 1
    
    def test_get_documents_pagination(self, client, mock_auth_headers):
        """测试分页"""
        response = client.get(
            "/api/v1/documents?page=1&limit=10",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10
    
    def test_get_documents_search(self, client, mock_auth_headers, sample_document):
        """测试搜索"""
        response = client.get(
            "/api/v1/documents?search=测试",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200


class TestDocumentDetail:
    """文档详情测试"""
    
    def test_get_document_detail(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试获取文档详情"""
        response = client.get(
            f"/api/v1/documents/{sample_document.id}",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_document.id
        assert "slides" in data
        assert len(data["slides"]) == 5
    
    def test_get_document_not_found(self, client, mock_auth_headers):
        """测试文档不存在"""
        response = client.get(
            "/api/v1/documents/non-existent-id",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 404
    
    def test_delete_document(self, client, mock_auth_headers, sample_document):
        """测试删除文档"""
        response = client.delete(
            f"/api/v1/documents/{sample_document.id}",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["success"] == True
        
        # 验证已删除
        get_response = client.get(
            f"/api/v1/documents/{sample_document.id}",
            headers=mock_auth_headers
        )
        assert get_response.status_code == 404


class TestDocumentSlides:
    """文档页面测试"""
    
    def test_get_document_slides(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试获取文档页面列表"""
        response = client.get(
            f"/api/v1/documents/{sample_document.id}/slides",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "slides" in data
        assert len(data["slides"]) == 5
        
        # 验证页面顺序
        for i, slide in enumerate(data["slides"]):
            assert slide["page_number"] == i + 1
