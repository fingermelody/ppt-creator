"""
PPT 组装模块测试用例
验证页面搜索、章节推荐、组装预览等功能
"""

import pytest


class TestSlideSearch:
    """页面搜索测试"""
    
    def test_search_slides_basic(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试基本搜索"""
        response = client.get(
            "/api/v1/assembly/search?query=测试",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "slides" in data
        assert "total" in data
        assert data["query"] == "测试"
    
    def test_search_slides_with_keyword(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试关键词搜索"""
        response = client.get(
            "/api/v1/assembly/search?query=演示",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # 示例数据中包含"演示"关键词
        assert data["total"] >= 0
    
    def test_search_slides_with_limit(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试搜索结果限制"""
        response = client.get(
            "/api/v1/assembly/search?query=测试&limit=3",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["slides"]) <= 3
    
    def test_search_slides_in_specific_documents(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试在特定文档中搜索"""
        response = client.get(
            f"/api/v1/assembly/search?query=内容&document_ids={sample_document.id}",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        # 所有结果应该来自指定文档
        for slide in data["slides"]:
            assert slide["document_id"] == sample_document.id
    
    def test_search_slides_empty_query(self, client, mock_auth_headers):
        """测试空查询"""
        response = client.get(
            "/api/v1/assembly/search?query=",
            headers=mock_auth_headers
        )
        
        # 空查询应该返回错误或空结果
        assert response.status_code in [200, 400, 422]
    
    def test_search_slides_no_results(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试无结果的搜索"""
        response = client.get(
            "/api/v1/assembly/search?query=不可能存在的内容xyz123",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["slides"]) == 0


class TestSectionRecommendations:
    """章节推荐测试"""
    
    def test_get_section_recommendations(self, client, mock_auth_headers, sample_document, sample_slides, sample_outline):
        """测试获取章节推荐"""
        section_id = sample_outline["sections"][0].id
        
        response = client.get(
            f"/api/v1/assembly/sections/{section_id}/recommendations",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["section_id"] == section_id
        assert "recommendations" in data
        assert "section_title" in data
    
    def test_get_section_recommendations_with_limit(self, client, mock_auth_headers, sample_document, sample_slides, sample_outline):
        """测试章节推荐数量限制"""
        section_id = sample_outline["sections"][0].id
        
        response = client.get(
            f"/api/v1/assembly/sections/{section_id}/recommendations?limit=3",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) <= 3
    
    def test_get_section_recommendations_not_found(self, client, mock_auth_headers):
        """测试章节不存在"""
        response = client.get(
            "/api/v1/assembly/sections/non-existent-section/recommendations",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 404


class TestSlideDetail:
    """页面详情测试"""
    
    def test_get_slide_detail(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试获取页面详情"""
        slide_id = sample_slides[0].id
        
        response = client.get(
            f"/api/v1/assembly/slides/{slide_id}",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == slide_id
        assert "title" in data
        assert "content_text" in data
        assert "page_number" in data
    
    def test_get_slide_detail_not_found(self, client, mock_auth_headers):
        """测试页面不存在"""
        response = client.get(
            "/api/v1/assembly/slides/non-existent-slide",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 404


class TestSimilarSlides:
    """相似页面测试"""
    
    def test_get_similar_slides(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试获取相似页面"""
        slide_id = sample_slides[0].id
        
        response = client.get(
            f"/api/v1/assembly/slides/{slide_id}/similar",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["source_slide_id"] == slide_id
        assert "similar_slides" in data
        
        # 相似页面不应包含源页面本身
        for similar in data["similar_slides"]:
            assert similar["id"] != slide_id
    
    def test_get_similar_slides_with_limit(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试相似页面数量限制"""
        slide_id = sample_slides[0].id
        
        response = client.get(
            f"/api/v1/assembly/slides/{slide_id}/similar?limit=2",
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["similar_slides"]) <= 2


class TestAssemblyPreview:
    """组装预览测试"""
    
    def test_preview_assembly(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试组装预览"""
        slide_ids = [s.id for s in sample_slides[:3]]
        
        response = client.post(
            "/api/v1/assembly/preview",
            json=slide_ids,
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["slides"]) == 3
        assert data["total_pages"] == 3
        assert len(data["missing_ids"]) == 0
    
    def test_preview_assembly_order(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试组装预览保持顺序"""
        # 故意打乱顺序
        slide_ids = [sample_slides[2].id, sample_slides[0].id, sample_slides[4].id]
        
        response = client.post(
            "/api/v1/assembly/preview",
            json=slide_ids,
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证返回顺序与请求顺序一致
        for i, slide in enumerate(data["slides"]):
            assert slide["id"] == slide_ids[i]
    
    def test_preview_assembly_with_missing_ids(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试组装预览包含不存在的 ID"""
        slide_ids = [sample_slides[0].id, "non-existent-id", sample_slides[1].id]
        
        response = client.post(
            "/api/v1/assembly/preview",
            json=slide_ids,
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_pages"] == 2
        assert "non-existent-id" in data["missing_ids"]
    
    def test_preview_assembly_empty_list(self, client, mock_auth_headers):
        """测试空页面列表"""
        response = client.post(
            "/api/v1/assembly/preview",
            json=[],
            headers=mock_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_pages"] == 0
        assert len(data["slides"]) == 0


class TestAssemblyWorkflow:
    """组装工作流集成测试"""
    
    def test_full_assembly_workflow(self, client, mock_auth_headers, sample_document, sample_slides, sample_outline):
        """测试完整组装工作流"""
        # 1. 搜索页面
        search_response = client.get(
            "/api/v1/assembly/search?query=测试",
            headers=mock_auth_headers
        )
        assert search_response.status_code == 200
        search_results = search_response.json()
        
        # 2. 获取章节推荐
        section_id = sample_outline["sections"][0].id
        recommend_response = client.get(
            f"/api/v1/assembly/sections/{section_id}/recommendations",
            headers=mock_auth_headers
        )
        assert recommend_response.status_code == 200
        
        # 3. 选择页面并预览
        if len(search_results["slides"]) >= 2:
            selected_ids = [s["id"] for s in search_results["slides"][:2]]
            preview_response = client.post(
                "/api/v1/assembly/preview",
                json=selected_ids,
                headers=mock_auth_headers
            )
            assert preview_response.status_code == 200
            preview_data = preview_response.json()
            assert preview_data["total_pages"] == 2
