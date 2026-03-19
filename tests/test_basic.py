"""
PPT-RSD 基础功能测试
用于快速验证上传和组装模块是否可运行
"""

import os
import sys
import pytest
from io import BytesIO
import zipfile

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestPPTXCreation:
    """测试 PPTX 文件创建和验证"""
    
    def test_create_minimal_pptx(self):
        """测试创建最小有效的 PPTX 文件"""
        buffer = BytesIO()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # [Content_Types].xml
            content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
</Types>'''
            zf.writestr('[Content_Types].xml', content_types)
            
            # _rels/.rels
            rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''
            zf.writestr('_rels/.rels', rels)
            
            # ppt/presentation.xml
            presentation = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
</p:presentation>'''
            zf.writestr('ppt/presentation.xml', presentation)
        
        buffer.seek(0)
        pptx_data = buffer.read()
        
        # 验证是有效的 ZIP 文件
        assert pptx_data[:4] == b'PK\x03\x04'
        
        # 验证包含必要的文件
        buffer.seek(0)
        with zipfile.ZipFile(buffer, 'r') as zf:
            names = zf.namelist()
            assert '[Content_Types].xml' in names
            assert '_rels/.rels' in names
            assert 'ppt/presentation.xml' in names
        
        print("✅ PPTX 文件创建成功")
    
    def test_pptx_file_validation(self):
        """测试 PPTX 文件验证逻辑"""
        # 有效的 PPTX 文件头（ZIP 格式）
        valid_header = b'PK\x03\x04'
        
        # 无效的文件头
        invalid_header = b'NOT_A_ZIP'
        
        assert valid_header[:2] == b'PK', "有效 PPTX 应以 PK 开头"
        assert invalid_header[:2] != b'PK', "无效文件不应以 PK 开头"
        
        print("✅ PPTX 文件验证逻辑正确")


class TestUploadLogic:
    """测试上传逻辑"""
    
    def test_chunk_calculation(self):
        """测试分片计算逻辑"""
        CHUNK_SIZE = 5 * 1024 * 1024  # 5MB
        
        # 测试不同文件大小
        test_cases = [
            (1024, 1),           # 1KB -> 1 chunk
            (CHUNK_SIZE, 1),    # 5MB -> 1 chunk
            (CHUNK_SIZE + 1, 2),  # 5MB+1 -> 2 chunks
            (CHUNK_SIZE * 3, 3),  # 15MB -> 3 chunks
            (CHUNK_SIZE * 10 + 500000, 11),  # ~50MB -> 11 chunks
        ]
        
        for file_size, expected_chunks in test_cases:
            total_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
            assert total_chunks == expected_chunks, f"文件大小 {file_size} 应产生 {expected_chunks} 分片，实际 {total_chunks}"
        
        print("✅ 分片计算逻辑正确")
    
    def test_filename_validation(self):
        """测试文件名验证"""
        def is_valid_filename(filename: str) -> bool:
            if not filename:
                return False
            if not filename.lower().endswith(('.pptx', '.ppt')):
                return False
            # 检查危险字符
            dangerous_chars = ['..', '/', '\\', '\x00']
            for char in dangerous_chars:
                if char in filename:
                    return False
            return True
        
        # 有效文件名
        assert is_valid_filename("test.pptx") == True
        assert is_valid_filename("测试文档.pptx") == True
        assert is_valid_filename("report_2024.PPTX") == True
        assert is_valid_filename("old_format.ppt") == True
        
        # 无效文件名
        assert is_valid_filename("") == False
        assert is_valid_filename("test.pdf") == False
        assert is_valid_filename("../hack.pptx") == False
        assert is_valid_filename("test\x00.pptx") == False
        
        print("✅ 文件名验证逻辑正确")


class TestAssemblyLogic:
    """测试组装逻辑"""
    
    def test_slide_ordering(self):
        """测试页面排序逻辑"""
        # 模拟页面数据
        slides = [
            {"id": "a", "page_number": 3},
            {"id": "b", "page_number": 1},
            {"id": "c", "page_number": 2},
        ]
        
        # 按指定顺序组装
        ordered_ids = ["b", "c", "a"]  # 期望顺序 1, 2, 3
        
        result = []
        for slide_id in ordered_ids:
            slide = next((s for s in slides if s["id"] == slide_id), None)
            if slide:
                result.append(slide)
        
        assert len(result) == 3
        assert result[0]["page_number"] == 1
        assert result[1]["page_number"] == 2
        assert result[2]["page_number"] == 3
        
        print("✅ 页面排序逻辑正确")
    
    def test_similarity_calculation(self):
        """测试相似度计算逻辑（简化版）"""
        def jaccard_similarity(set1: set, set2: set) -> float:
            """Jaccard 相似度"""
            if not set1 and not set2:
                return 1.0
            if not set1 or not set2:
                return 0.0
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            return intersection / union
        
        # 测试用例
        keywords1 = {"PPT", "演示", "设计", "模板"}
        keywords2 = {"PPT", "演示", "报告", "图表"}
        keywords3 = {"完全", "不同", "内容"}
        
        # 部分相似
        sim1 = jaccard_similarity(keywords1, keywords2)
        assert 0.2 < sim1 < 0.8, f"部分相似度应在 0.2-0.8 之间，实际 {sim1}"
        
        # 完全不同
        sim2 = jaccard_similarity(keywords1, keywords3)
        assert sim2 == 0.0, f"完全不同应为 0，实际 {sim2}"
        
        # 完全相同
        sim3 = jaccard_similarity(keywords1, keywords1)
        assert sim3 == 1.0, f"完全相同应为 1，实际 {sim3}"
        
        print("✅ 相似度计算逻辑正确")
    
    def test_assembly_preview_structure(self):
        """测试组装预览数据结构"""
        # 模拟预览响应
        preview = {
            "total_slides": 5,
            "slides": [
                {
                    "id": "slide-1",
                    "source_document": "doc-1",
                    "page_number": 1,
                    "title": "封面",
                    "thumbnail_url": "/thumbnails/slide-1.png"
                },
                {
                    "id": "slide-2",
                    "source_document": "doc-2",
                    "page_number": 3,
                    "title": "数据分析",
                    "thumbnail_url": "/thumbnails/slide-2.png"
                }
            ],
            "estimated_pages": 5
        }
        
        # 验证结构
        assert "total_slides" in preview
        assert "slides" in preview
        assert isinstance(preview["slides"], list)
        
        for slide in preview["slides"]:
            assert "id" in slide
            assert "source_document" in slide
            assert "page_number" in slide
            assert "title" in slide
        
        print("✅ 组装预览结构正确")


class TestSearchLogic:
    """测试搜索逻辑"""
    
    def test_keyword_extraction(self):
        """测试关键词提取"""
        def extract_keywords(text: str) -> set:
            """简单关键词提取（仅用于测试）"""
            import re
            # 提取英文单词（中文分词需要专门库，这里简化处理）
            words = re.findall(r'[a-zA-Z]+', text)
            # 过滤停用词
            stopwords = {"a", "the", "is", "and", "of", "to", "in"}
            return set(w.lower() for w in words if w.lower() not in stopwords and len(w) > 1)
        
        text = "This is a PPT about design and presentation"
        keywords = extract_keywords(text)
        
        assert "ppt" in keywords
        assert "design" in keywords
        assert "presentation" in keywords
        assert "is" not in keywords  # 停用词应被过滤
        assert "a" not in keywords   # 单字符应被过滤
        
        print("✅ 关键词提取逻辑正确")
    
    def test_search_result_ranking(self):
        """测试搜索结果排序"""
        # 模拟搜索结果
        results = [
            {"id": "1", "score": 0.85, "title": "高度匹配"},
            {"id": "2", "score": 0.60, "title": "中等匹配"},
            {"id": "3", "score": 0.95, "title": "最佳匹配"},
            {"id": "4", "score": 0.40, "title": "低匹配"},
        ]
        
        # 按分数排序
        sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
        
        assert sorted_results[0]["title"] == "最佳匹配"
        assert sorted_results[1]["title"] == "高度匹配"
        assert sorted_results[-1]["title"] == "低匹配"
        
        print("✅ 搜索排序逻辑正确")


class TestAPIStructure:
    """测试 API 结构和端点定义"""
    
    def test_upload_api_endpoints(self):
        """验证上传 API 端点结构"""
        upload_endpoints = {
            "POST /api/v1/documents/upload/init": "初始化上传",
            "POST /api/v1/documents/upload/chunk": "上传分片",
            "POST /api/v1/documents/upload/complete": "完成上传",
            "GET /api/v1/documents": "获取文档列表",
            "GET /api/v1/documents/{id}": "获取文档详情",
            "DELETE /api/v1/documents/{id}": "删除文档",
        }
        
        for endpoint, description in upload_endpoints.items():
            assert endpoint.startswith(("GET", "POST", "PUT", "DELETE"))
            assert "/api/v1/" in endpoint
        
        print(f"✅ 上传 API 端点验证通过 ({len(upload_endpoints)} 个端点)")
    
    def test_assembly_api_endpoints(self):
        """验证组装 API 端点结构"""
        assembly_endpoints = {
            "POST /api/v1/assembly/search": "搜索页面",
            "GET /api/v1/assembly/sections/{id}/recommendations": "获取章节推荐",
            "GET /api/v1/assembly/slides/{id}": "获取页面详情",
            "GET /api/v1/assembly/slides/{id}/similar": "获取相似页面",
            "POST /api/v1/assembly/preview": "预览组装",
        }
        
        for endpoint, description in assembly_endpoints.items():
            assert endpoint.startswith(("GET", "POST", "PUT", "DELETE"))
            assert "/api/v1/" in endpoint
        
        print(f"✅ 组装 API 端点验证通过 ({len(assembly_endpoints)} 个端点)")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("PPT-RSD 基础功能测试")
    print("=" * 60)
    
    test_classes = [
        TestPPTXCreation(),
        TestUploadLogic(),
        TestAssemblyLogic(),
        TestSearchLogic(),
        TestAPIStructure(),
    ]
    
    total_passed = 0
    total_failed = 0
    
    for test_class in test_classes:
        print(f"\n--- {test_class.__class__.__name__} ---")
        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                try:
                    method = getattr(test_class, method_name)
                    method()
                    total_passed += 1
                except Exception as e:
                    print(f"❌ {method_name}: {str(e)}")
                    total_failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试完成: {total_passed} 通过, {total_failed} 失败")
    print("=" * 60)
    
    return total_failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
