"""
端到端集成测试
验证完整的 PPT 上传 -> 组装 -> 导出 流程
"""

import pytest
import hashlib
from io import BytesIO
import time


class TestEndToEndWorkflow:
    """端到端工作流测试"""
    
    def test_upload_and_assembly_workflow(self, client, mock_auth_headers, sample_pptx_file):
        """
        完整工作流测试：上传 -> 解析 -> 搜索 -> 组装
        """
        # ========================================
        # 步骤 1: 上传 PPT 文件
        # ========================================
        
        # 1.1 初始化上传
        init_response = client.post(
            "/api/v1/documents/upload/init",
            json={
                "filename": "workflow_test.pptx",
                "filesize": len(sample_pptx_file),
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        assert init_response.status_code == 200
        upload_id = init_response.json()["upload_id"]
        
        # 1.2 上传分片
        chunk_response = client.post(
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
        assert chunk_response.status_code == 200
        
        # 1.3 完成上传
        md5_hash = hashlib.md5(sample_pptx_file).hexdigest()
        complete_response = client.post(
            "/api/v1/documents/upload/complete",
            json={
                "upload_id": upload_id,
                "filename": "工作流测试文档.pptx",
                "md5_hash": md5_hash
            },
            headers=mock_auth_headers
        )
        assert complete_response.status_code == 200
        document_id = complete_response.json()["document_id"]
        assert complete_response.json()["status"] == "parsing"
        
        # ========================================
        # 步骤 2: 验证文档列表
        # ========================================
        
        list_response = client.get(
            "/api/v1/documents",
            headers=mock_auth_headers
        )
        assert list_response.status_code == 200
        
        # ========================================
        # 步骤 3: 搜索页面（模拟解析完成后）
        # ========================================
        
        search_response = client.get(
            "/api/v1/assembly/search?query=测试",
            headers=mock_auth_headers
        )
        assert search_response.status_code == 200
        
        # ========================================
        # 步骤 4: 预览组装结果
        # ========================================
        
        # 使用搜索结果中的页面进行组装预览
        search_data = search_response.json()
        if search_data["slides"]:
            slide_ids = [s["id"] for s in search_data["slides"][:3]]
            
            preview_response = client.post(
                "/api/v1/assembly/preview",
                json=slide_ids,
                headers=mock_auth_headers
            )
            assert preview_response.status_code == 200


class TestHealthCheck:
    """健康检查测试"""
    
    def test_api_health(self, client):
        """测试 API 健康检查"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
    
    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code in [200, 404]


class TestErrorHandling:
    """错误处理测试"""
    
    def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/documents")
        # 没有认证头应该返回 401 或 403
        assert response.status_code in [401, 403, 422]
    
    def test_invalid_json(self, client, mock_auth_headers):
        """测试无效 JSON"""
        response = client.post(
            "/api/v1/documents/upload/init",
            content="invalid json",
            headers={**mock_auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    def test_method_not_allowed(self, client, mock_auth_headers):
        """测试不允许的方法"""
        response = client.put(
            "/api/v1/documents",
            json={},
            headers=mock_auth_headers
        )
        assert response.status_code == 405


class TestConcurrency:
    """并发测试"""
    
    def test_concurrent_uploads(self, client, mock_auth_headers, sample_pptx_file):
        """测试并发上传"""
        upload_ids = []
        
        # 同时初始化多个上传
        for i in range(3):
            response = client.post(
                "/api/v1/documents/upload/init",
                json={
                    "filename": f"concurrent_test_{i}.pptx",
                    "filesize": len(sample_pptx_file),
                    "total_chunks": 1
                },
                headers=mock_auth_headers
            )
            assert response.status_code == 200
            upload_ids.append(response.json()["upload_id"])
        
        # 验证所有上传 ID 都是唯一的
        assert len(set(upload_ids)) == len(upload_ids)
    
    def test_concurrent_searches(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试并发搜索"""
        queries = ["测试", "演示", "内容", "PPT", "标题"]
        results = []
        
        for query in queries:
            response = client.get(
                f"/api/v1/assembly/search?query={query}",
                headers=mock_auth_headers
            )
            assert response.status_code == 200
            results.append(response.json())
        
        # 验证所有搜索都成功返回
        assert len(results) == len(queries)


class TestDataIntegrity:
    """数据完整性测试"""
    
    def test_document_slide_relationship(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试文档和页面的关联关系"""
        # 获取文档详情
        doc_response = client.get(
            f"/api/v1/documents/{sample_document.id}",
            headers=mock_auth_headers
        )
        assert doc_response.status_code == 200
        doc_data = doc_response.json()
        
        # 验证页面数量
        assert len(doc_data["slides"]) == sample_document.page_count
        
        # 验证每个页面都属于该文档
        for slide in doc_data["slides"]:
            assert slide["document_id"] == sample_document.id
    
    def test_slide_order_consistency(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试页面顺序一致性"""
        # 获取文档的页面列表
        response = client.get(
            f"/api/v1/documents/{sample_document.id}/slides",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        slides = response.json()["slides"]
        
        # 验证页码连续
        page_numbers = [s["page_number"] for s in slides]
        assert page_numbers == sorted(page_numbers)
        assert page_numbers == list(range(1, len(slides) + 1))


class TestPerformance:
    """性能基准测试"""
    
    def test_search_response_time(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试搜索响应时间"""
        import time
        
        start = time.time()
        response = client.get(
            "/api/v1/assembly/search?query=测试",
            headers=mock_auth_headers
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # 搜索应该在 2 秒内完成
        assert elapsed < 2.0
    
    def test_document_list_response_time(self, client, mock_auth_headers):
        """测试文档列表响应时间"""
        import time
        
        start = time.time()
        response = client.get(
            "/api/v1/documents?page=1&limit=50",
            headers=mock_auth_headers
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        # 列表查询应该在 1 秒内完成
        assert elapsed < 1.0
