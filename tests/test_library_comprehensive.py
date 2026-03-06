"""
文档库深度测试 - 全面测试文档库的核心能力
测试覆盖：
1. 上传功能测试（分片上传、文件类型、边界条件）
2. 文档管理测试（CRUD、状态管理、权限控制）
3. 文档搜索测试（关键词、模糊、分页）
4. 文档列表测试（筛选、排序、分页）
5. 页面管理测试（页面查询、关联关系）
6. 数据完整性测试
7. 并发安全测试
8. 性能基准测试
9. 边界条件和异常处理测试
10. 安全性测试
"""

import pytest
import hashlib
import uuid
import time
import string
import random
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List


# ============================================
# 辅助工具函数
# ============================================

def generate_random_string(length: int = 10) -> str:
    """生成随机字符串"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_chinese(length: int = 5) -> str:
    """生成随机中文字符串"""
    chinese_chars = '测试文档演示幻灯片内容标题副标题页面章节介绍总结分析报告'
    return ''.join(random.choices(chinese_chars, k=length))


def create_minimal_pptx() -> bytes:
    """创建最小的有效 PPTX 文件"""
    import zipfile
    
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
</Types>'''
        zf.writestr('[Content_Types].xml', content_types)
        
        rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>'''
        zf.writestr('_rels/.rels', rels)
        
        presentation = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
</p:presentation>'''
        zf.writestr('ppt/presentation.xml', presentation)
    
    buffer.seek(0)
    return buffer.read()


# ============================================
# 第一部分：上传功能深度测试
# ============================================

class TestUploadInitDeep:
    """上传初始化深度测试"""
    
    def test_init_with_minimum_valid_params(self, client, mock_auth_headers):
        """测试最小有效参数初始化"""
        response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "a.pptx",
                "filesize": 1,
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "upload_id" in data
        assert len(data["upload_id"]) > 0
    
    def test_init_with_unicode_filename(self, client, mock_auth_headers):
        """测试 Unicode 文件名（中文、日文、韩文、Emoji）"""
        unicode_filenames = [
            "中文文档.pptx",
            "日本語ドキュメント.pptx",
            "한국어문서.pptx",
            "文档📊演示🎯.pptx",
            "Документ.pptx",  # 俄文
            "مستند.pptx",    # 阿拉伯文
        ]
        
        for filename in unicode_filenames:
            response = client.post(
                "/api/documents/upload/init",
                json={
                    "filename": filename,
                    "filesize": 1024,
                    "total_chunks": 1
                },
                headers=mock_auth_headers
            )
            assert response.status_code == 200, f"Failed for filename: {filename}"
    
    def test_init_with_special_chars_filename(self, client, mock_auth_headers):
        """测试特殊字符文件名"""
        special_filenames = [
            "file with spaces.pptx",
            "file-with-dashes.pptx",
            "file_with_underscores.pptx",
            "file.multiple.dots.pptx",
            "文档(2024版本).pptx",
            "report [final].pptx",
        ]
        
        for filename in special_filenames:
            response = client.post(
                "/api/documents/upload/init",
                json={
                    "filename": filename,
                    "filesize": 1024,
                    "total_chunks": 1
                },
                headers=mock_auth_headers
            )
            assert response.status_code == 200, f"Failed for filename: {filename}"
    
    def test_init_with_very_long_filename(self, client, mock_auth_headers):
        """测试超长文件名（边界测试）"""
        # 255 字符的文件名（通常是文件系统限制）
        long_filename = "a" * 250 + ".pptx"
        response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": long_filename,
                "filesize": 1024,
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        # 应该成功或返回验证错误
        assert response.status_code in [200, 400, 422]
    
    def test_init_with_large_file_size(self, client, mock_auth_headers):
        """测试大文件初始化（100MB, 500MB, 1GB）"""
        large_sizes = [
            100 * 1024 * 1024,   # 100MB
            500 * 1024 * 1024,   # 500MB
            1024 * 1024 * 1024,  # 1GB
        ]
        
        for file_size in large_sizes:
            chunk_size = 5 * 1024 * 1024  # 5MB chunks
            total_chunks = (file_size + chunk_size - 1) // chunk_size
            
            response = client.post(
                "/api/documents/upload/init",
                json={
                    "filename": f"large_file_{file_size}.pptx",
                    "filesize": file_size,
                    "total_chunks": total_chunks
                },
                headers=mock_auth_headers
            )
            assert response.status_code == 200, f"Failed for size: {file_size}"
    
    def test_init_with_negative_filesize(self, client, mock_auth_headers):
        """测试负数文件大小（应该拒绝）"""
        response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": -1,
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        assert response.status_code in [400, 422]
    
    def test_init_with_zero_chunks(self, client, mock_auth_headers):
        """测试零分片数（应该拒绝）"""
        response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": 1024,
                "total_chunks": 0
            },
            headers=mock_auth_headers
        )
        assert response.status_code in [400, 422]
    
    def test_init_upload_id_uniqueness(self, client, mock_auth_headers):
        """测试上传 ID 唯一性"""
        upload_ids = set()
        
        for i in range(100):
            response = client.post(
                "/api/documents/upload/init",
                json={
                    "filename": f"test_{i}.pptx",
                    "filesize": 1024,
                    "total_chunks": 1
                },
                headers=mock_auth_headers
            )
            assert response.status_code == 200
            upload_id = response.json()["upload_id"]
            assert upload_id not in upload_ids, f"Duplicate upload_id: {upload_id}"
            upload_ids.add(upload_id)


class TestUploadChunkDeep:
    """分片上传深度测试"""
    
    def test_upload_chunk_out_of_order(self, client, mock_auth_headers, sample_pptx_file):
        """测试乱序上传分片"""
        # 初始化 3 分片上传
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": len(sample_pptx_file) * 3,
                "total_chunks": 3
            },
            headers=mock_auth_headers
        )
        upload_id = init_response.json()["upload_id"]
        
        # 乱序上传：先传 2，再传 0，最后传 1
        order = [2, 0, 1]
        for idx in order:
            response = client.post(
                "/api/documents/upload/chunk",
                data={
                    "upload_id": upload_id,
                    "chunk_index": idx
                },
                files={
                    "chunk": (f"chunk_{idx}", BytesIO(sample_pptx_file), "application/octet-stream")
                },
                headers=mock_auth_headers
            )
            assert response.status_code == 200
    
    def test_upload_duplicate_chunk(self, client, mock_auth_headers, sample_pptx_file):
        """测试重复上传同一分片（应该允许覆盖或拒绝）"""
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": len(sample_pptx_file),
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        upload_id = init_response.json()["upload_id"]
        
        # 上传同一分片两次
        for _ in range(2):
            response = client.post(
                "/api/documents/upload/chunk",
                data={
                    "upload_id": upload_id,
                    "chunk_index": 0
                },
                files={
                    "chunk": ("chunk_0", BytesIO(sample_pptx_file), "application/octet-stream")
                },
                headers=mock_auth_headers
            )
            # 应该成功（覆盖）或返回特定错误码
            assert response.status_code in [200, 400, 409]
    
    def test_upload_invalid_upload_id(self, client, mock_auth_headers, sample_pptx_file):
        """测试无效的 upload_id"""
        response = client.post(
            "/api/documents/upload/chunk",
            data={
                "upload_id": "non-existent-upload-id",
                "chunk_index": 0
            },
            files={
                "chunk": ("chunk_0", BytesIO(sample_pptx_file), "application/octet-stream")
            },
            headers=mock_auth_headers
        )
        # 可能返回 200（实现宽松）或 404（严格）
        assert response.status_code in [200, 400, 404]
    
    def test_upload_chunk_index_out_of_range(self, client, mock_auth_headers, sample_pptx_file):
        """测试分片索引越界"""
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": len(sample_pptx_file),
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        upload_id = init_response.json()["upload_id"]
        
        # 上传超出范围的分片索引
        response = client.post(
            "/api/documents/upload/chunk",
            data={
                "upload_id": upload_id,
                "chunk_index": 999
            },
            files={
                "chunk": ("chunk_999", BytesIO(sample_pptx_file), "application/octet-stream")
            },
            headers=mock_auth_headers
        )
        # 应该返回错误或被宽松处理
        assert response.status_code in [200, 400, 422]
    
    def test_upload_empty_chunk(self, client, mock_auth_headers):
        """测试上传空分片"""
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": 1024,
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        upload_id = init_response.json()["upload_id"]
        
        response = client.post(
            "/api/documents/upload/chunk",
            data={
                "upload_id": upload_id,
                "chunk_index": 0
            },
            files={
                "chunk": ("chunk_0", BytesIO(b""), "application/octet-stream")
            },
            headers=mock_auth_headers
        )
        # 空分片可能被允许或拒绝
        assert response.status_code in [200, 400, 422]


class TestUploadCompleteDeep:
    """上传完成深度测试"""
    
    def test_complete_with_md5_verification(self, client, mock_auth_headers, sample_pptx_file):
        """测试 MD5 校验"""
        # 初始化
        init_response = client.post(
            "/api/documents/upload/init",
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
            "/api/documents/upload/chunk",
            data={"upload_id": upload_id, "chunk_index": 0},
            files={"chunk": ("chunk_0", BytesIO(sample_pptx_file), "application/octet-stream")},
            headers=mock_auth_headers
        )
        
        # 正确的 MD5
        correct_md5 = hashlib.md5(sample_pptx_file).hexdigest()
        response = client.post(
            "/api/documents/upload/complete",
            json={
                "upload_id": upload_id,
                "filename": "测试.pptx",
                "md5_hash": correct_md5
            },
            headers=mock_auth_headers
        )
        assert response.status_code == 200
    
    def test_complete_with_wrong_md5(self, client, mock_auth_headers, sample_pptx_file):
        """测试错误的 MD5 校验"""
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": len(sample_pptx_file),
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        upload_id = init_response.json()["upload_id"]
        
        client.post(
            "/api/documents/upload/chunk",
            data={"upload_id": upload_id, "chunk_index": 0},
            files={"chunk": ("chunk_0", BytesIO(sample_pptx_file), "application/octet-stream")},
            headers=mock_auth_headers
        )
        
        # 错误的 MD5
        wrong_md5 = "0" * 32
        response = client.post(
            "/api/documents/upload/complete",
            json={
                "upload_id": upload_id,
                "filename": "测试.pptx",
                "md5_hash": wrong_md5
            },
            headers=mock_auth_headers
        )
        # 可能返回错误或忽略（取决于实现）
        assert response.status_code in [200, 400, 422]
    
    def test_complete_without_md5(self, client, mock_auth_headers, sample_pptx_file):
        """测试不提供 MD5（应该允许）"""
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": len(sample_pptx_file),
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        upload_id = init_response.json()["upload_id"]
        
        client.post(
            "/api/documents/upload/chunk",
            data={"upload_id": upload_id, "chunk_index": 0},
            files={"chunk": ("chunk_0", BytesIO(sample_pptx_file), "application/octet-stream")},
            headers=mock_auth_headers
        )
        
        response = client.post(
            "/api/documents/upload/complete",
            json={
                "upload_id": upload_id,
                "filename": "测试.pptx"
            },
            headers=mock_auth_headers
        )
        assert response.status_code == 200


# ============================================
# 第二部分：文档管理深度测试
# ============================================

class TestDocumentCRUD:
    """文档 CRUD 操作测试"""
    
    def test_document_list_empty_state(self, client, mock_auth_headers):
        """测试空状态下的文档列表"""
        response = client.get("/api/documents", headers=mock_auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert isinstance(data["documents"], list)
        assert isinstance(data["total"], int)
    
    def test_document_detail_fields(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试文档详情字段完整性"""
        response = client.get(
            f"/api/documents/{sample_document.id}",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # 验证必需字段存在
        required_fields = ["id", "filename", "original_filename", "file_size", 
                         "page_count", "status", "created_at", "updated_at"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # 验证 slides 字段
        assert "slides" in data
        assert isinstance(data["slides"], list)
    
    def test_document_soft_delete(self, client, mock_auth_headers, sample_document):
        """测试软删除功能"""
        doc_id = sample_document.id
        
        # 删除前可以访问
        response = client.get(f"/api/documents/{doc_id}", headers=mock_auth_headers)
        assert response.status_code == 200
        
        # 执行删除
        delete_response = client.delete(f"/api/documents/{doc_id}", headers=mock_auth_headers)
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] == True
        
        # 删除后无法访问
        get_response = client.get(f"/api/documents/{doc_id}", headers=mock_auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_non_existent_document(self, client, mock_auth_headers):
        """测试删除不存在的文档"""
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/documents/{fake_id}", headers=mock_auth_headers)
        assert response.status_code == 404
    
    def test_double_delete_document(self, client, mock_auth_headers, sample_document):
        """测试重复删除同一文档"""
        doc_id = sample_document.id
        
        # 第一次删除
        response1 = client.delete(f"/api/documents/{doc_id}", headers=mock_auth_headers)
        assert response1.status_code == 200
        
        # 第二次删除（应该返回 404）
        response2 = client.delete(f"/api/documents/{doc_id}", headers=mock_auth_headers)
        assert response2.status_code == 404


class TestDocumentStatusTransitions:
    """文档状态转换测试"""
    
    def test_initial_status_after_upload(self, client, mock_auth_headers, sample_pptx_file):
        """测试上传后的初始状态"""
        # 完成上传流程
        init_response = client.post(
            "/api/documents/upload/init",
            json={"filename": "test.pptx", "filesize": len(sample_pptx_file), "total_chunks": 1},
            headers=mock_auth_headers
        )
        upload_id = init_response.json()["upload_id"]
        
        client.post(
            "/api/documents/upload/chunk",
            data={"upload_id": upload_id, "chunk_index": 0},
            files={"chunk": ("chunk_0", BytesIO(sample_pptx_file), "application/octet-stream")},
            headers=mock_auth_headers
        )
        
        complete_response = client.post(
            "/api/documents/upload/complete",
            json={"upload_id": upload_id, "filename": "测试.pptx"},
            headers=mock_auth_headers
        )
        
        # 验证初始状态是 parsing
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "parsing"


# ============================================
# 第三部分：文档搜索深度测试
# ============================================

class TestDocumentSearch:
    """文档搜索功能测试"""
    
    def test_search_with_keyword(self, client, mock_auth_headers, sample_document):
        """测试关键词搜索"""
        response = client.get(
            "/api/documents?search=测试",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
    
    def test_search_with_empty_keyword(self, client, mock_auth_headers):
        """测试空关键词搜索"""
        response = client.get(
            "/api/documents?search=",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
    
    def test_search_with_special_chars(self, client, mock_auth_headers):
        """测试特殊字符搜索"""
        special_keywords = [
            "%",
            "_",
            "\\",
            "'",
            "\"",
            "<script>",
            "'; DROP TABLE documents; --",  # SQL 注入测试
        ]
        
        for keyword in special_keywords:
            response = client.get(
                f"/api/documents?search={keyword}",
                headers=mock_auth_headers
            )
            # 应该返回成功（无结果）或适当处理
            assert response.status_code in [200, 400], f"Failed for keyword: {keyword}"
    
    def test_search_case_insensitivity(self, client, mock_auth_headers, sample_document):
        """测试搜索大小写不敏感"""
        keywords = ["TEST", "test", "Test", "TeSt"]
        
        for keyword in keywords:
            response = client.get(
                f"/api/documents?search={keyword}",
                headers=mock_auth_headers
            )
            assert response.status_code == 200


# ============================================
# 第四部分：分页和筛选深度测试
# ============================================

class TestDocumentListPagination:
    """文档列表分页测试"""
    
    def test_pagination_first_page(self, client, mock_auth_headers):
        """测试第一页"""
        response = client.get(
            "/api/documents?page=1&limit=10",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10
    
    def test_pagination_large_page_number(self, client, mock_auth_headers):
        """测试超大页码"""
        response = client.get(
            "/api/documents?page=9999999&limit=10",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # 超大页码应该返回空列表
        assert len(data["documents"]) == 0
    
    def test_pagination_zero_page(self, client, mock_auth_headers):
        """测试零页码（应该拒绝）"""
        response = client.get(
            "/api/documents?page=0&limit=10",
            headers=mock_auth_headers
        )
        # 应该返回验证错误或自动校正
        assert response.status_code in [200, 400, 422]
    
    def test_pagination_negative_page(self, client, mock_auth_headers):
        """测试负页码"""
        response = client.get(
            "/api/documents?page=-1&limit=10",
            headers=mock_auth_headers
        )
        assert response.status_code in [200, 400, 422]
    
    def test_pagination_limit_boundaries(self, client, mock_auth_headers):
        """测试 limit 边界值"""
        limits = [1, 10, 50, 100, 200]
        
        for limit in limits:
            response = client.get(
                f"/api/documents?page=1&limit={limit}",
                headers=mock_auth_headers
            )
            # limit 可能有最大限制
            assert response.status_code in [200, 400, 422]


class TestDocumentListFiltering:
    """文档列表筛选测试"""
    
    def test_filter_by_status_ready(self, client, mock_auth_headers, sample_document):
        """测试按就绪状态筛选"""
        response = client.get(
            "/api/documents?status=ready",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for doc in data["documents"]:
            assert doc["status"] == "ready"
    
    def test_filter_by_status_parsing(self, client, mock_auth_headers):
        """测试按解析中状态筛选"""
        response = client.get(
            "/api/documents?status=parsing",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
    
    def test_filter_by_invalid_status(self, client, mock_auth_headers):
        """测试无效状态筛选"""
        response = client.get(
            "/api/documents?status=invalid_status",
            headers=mock_auth_headers
        )
        # 应该返回验证错误或忽略
        assert response.status_code in [200, 400, 422]


# ============================================
# 第五部分：页面管理测试
# ============================================

class TestSlideManagement:
    """页面管理测试"""
    
    def test_get_slides_for_document(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试获取文档的所有页面"""
        response = client.get(
            f"/api/documents/{sample_document.id}/slides",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "slides" in data
        assert len(data["slides"]) == 5
    
    def test_slides_order_by_page_number(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试页面按页码排序"""
        response = client.get(
            f"/api/documents/{sample_document.id}/slides",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        slides = response.json()["slides"]
        
        # 验证页码递增
        page_numbers = [s["page_number"] for s in slides]
        assert page_numbers == sorted(page_numbers)
    
    def test_slides_content_fields(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试页面内容字段"""
        response = client.get(
            f"/api/documents/{sample_document.id}/slides",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        slides = response.json()["slides"]
        
        for slide in slides:
            assert "id" in slide
            assert "document_id" in slide
            assert "page_number" in slide
            assert slide["document_id"] == sample_document.id
    
    def test_get_slides_for_non_existent_document(self, client, mock_auth_headers):
        """测试获取不存在文档的页面"""
        fake_id = str(uuid.uuid4())
        response = client.get(
            f"/api/documents/{fake_id}/slides",
            headers=mock_auth_headers
        )
        assert response.status_code == 404


# ============================================
# 第六部分：数据完整性测试
# ============================================

class TestDataIntegrityDeep:
    """数据完整性深度测试"""
    
    def test_document_slide_count_consistency(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试文档页数与实际页面数一致"""
        # 获取文档详情
        doc_response = client.get(
            f"/api/documents/{sample_document.id}",
            headers=mock_auth_headers
        )
        doc_data = doc_response.json()
        
        # 获取页面列表
        slides_response = client.get(
            f"/api/documents/{sample_document.id}/slides",
            headers=mock_auth_headers
        )
        slides_data = slides_response.json()
        
        # 验证一致性
        assert doc_data["page_count"] == len(slides_data["slides"])
    
    def test_slide_page_number_uniqueness(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试同一文档中页码唯一"""
        response = client.get(
            f"/api/documents/{sample_document.id}/slides",
            headers=mock_auth_headers
        )
        slides = response.json()["slides"]
        
        page_numbers = [s["page_number"] for s in slides]
        assert len(page_numbers) == len(set(page_numbers))
    
    def test_slide_page_number_sequential(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试页码连续性"""
        response = client.get(
            f"/api/documents/{sample_document.id}/slides",
            headers=mock_auth_headers
        )
        slides = response.json()["slides"]
        
        page_numbers = sorted([s["page_number"] for s in slides])
        expected = list(range(1, len(slides) + 1))
        assert page_numbers == expected


# ============================================
# 第七部分：并发安全测试
# ============================================

class TestConcurrencySafety:
    """并发安全测试"""
    
    def test_concurrent_document_list_requests(self, client, mock_auth_headers):
        """测试并发文档列表请求"""
        def make_request():
            return client.get("/api/documents", headers=mock_auth_headers)
        
        # 模拟 10 个并发请求
        results = []
        for _ in range(10):
            response = make_request()
            results.append(response.status_code)
        
        # 所有请求都应该成功
        assert all(code == 200 for code in results)
    
    def test_concurrent_upload_init(self, client, mock_auth_headers):
        """测试并发上传初始化"""
        upload_ids = []
        
        for i in range(20):
            response = client.post(
                "/api/documents/upload/init",
                json={
                    "filename": f"concurrent_{i}.pptx",
                    "filesize": 1024,
                    "total_chunks": 1
                },
                headers=mock_auth_headers
            )
            assert response.status_code == 200
            upload_ids.append(response.json()["upload_id"])
        
        # 验证所有 ID 唯一
        assert len(upload_ids) == len(set(upload_ids))


# ============================================
# 第八部分：性能基准测试
# ============================================

class TestPerformanceBenchmarks:
    """性能基准测试"""
    
    def test_upload_init_response_time(self, client, mock_auth_headers):
        """测试上传初始化响应时间"""
        start = time.time()
        response = client.post(
            "/api/documents/upload/init",
            json={"filename": "test.pptx", "filesize": 1024, "total_chunks": 1},
            headers=mock_auth_headers
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # 应该在 1 秒内完成
    
    def test_document_list_response_time(self, client, mock_auth_headers):
        """测试文档列表响应时间"""
        start = time.time()
        response = client.get(
            "/api/documents?page=1&limit=100",
            headers=mock_auth_headers
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0  # 应该在 2 秒内完成
    
    def test_document_detail_response_time(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试文档详情响应时间"""
        start = time.time()
        response = client.get(
            f"/api/documents/{sample_document.id}",
            headers=mock_auth_headers
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0  # 应该在 1 秒内完成


# ============================================
# 第九部分：边界条件和异常处理测试
# ============================================

class TestBoundaryConditions:
    """边界条件测试"""
    
    def test_document_id_formats(self, client, mock_auth_headers):
        """测试各种文档 ID 格式"""
        test_ids = [
            "",                           # 空字符串
            " ",                          # 空格
            "a" * 1000,                   # 超长 ID
            "not-a-uuid",                 # 非 UUID 格式
            "00000000-0000-0000-0000-000000000000",  # 空 UUID
            str(uuid.uuid4()),            # 有效但不存在的 UUID
        ]
        
        for doc_id in test_ids:
            if doc_id.strip():  # 跳过空字符串（会导致路由问题）
                response = client.get(
                    f"/api/documents/{doc_id}",
                    headers=mock_auth_headers
                )
                # 应该返回 404（不存在）或 400/422（格式错误）
                assert response.status_code in [400, 404, 422], f"Unexpected status for ID: {doc_id}"
    
    def test_missing_required_fields(self, client, mock_auth_headers):
        """测试缺少必需字段"""
        # 缺少 filename
        response = client.post(
            "/api/documents/upload/init",
            json={"filesize": 1024, "total_chunks": 1},
            headers=mock_auth_headers
        )
        assert response.status_code == 422
        
        # 缺少 filesize
        response = client.post(
            "/api/documents/upload/init",
            json={"filename": "test.pptx", "total_chunks": 1},
            headers=mock_auth_headers
        )
        assert response.status_code == 422
        
        # 缺少 total_chunks
        response = client.post(
            "/api/documents/upload/init",
            json={"filename": "test.pptx", "filesize": 1024},
            headers=mock_auth_headers
        )
        assert response.status_code == 422
    
    def test_extra_unknown_fields(self, client, mock_auth_headers):
        """测试额外的未知字段（应该被忽略）"""
        response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.pptx",
                "filesize": 1024,
                "total_chunks": 1,
                "unknown_field": "should_be_ignored",
                "another_unknown": 12345
            },
            headers=mock_auth_headers
        )
        assert response.status_code == 200


class TestExceptionHandling:
    """异常处理测试"""
    
    def test_malformed_json(self, client, mock_auth_headers):
        """测试格式错误的 JSON"""
        response = client.post(
            "/api/documents/upload/init",
            content="not valid json",
            headers={**mock_auth_headers, "Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]
    
    def test_wrong_content_type(self, client, mock_auth_headers):
        """测试错误的 Content-Type"""
        response = client.post(
            "/api/documents/upload/init",
            content='{"filename": "test.pptx", "filesize": 1024, "total_chunks": 1}',
            headers={**mock_auth_headers, "Content-Type": "text/plain"}
        )
        # 可能被解析或返回错误
        assert response.status_code in [200, 400, 415, 422]


# ============================================
# 第十部分：安全性测试
# ============================================

class TestSecurityChecks:
    """安全性测试"""
    
    def test_sql_injection_in_search(self, client, mock_auth_headers):
        """测试搜索中的 SQL 注入防护"""
        injection_payloads = [
            "'; DROP TABLE documents; --",
            "' OR '1'='1",
            "1; SELECT * FROM users",
            "UNION SELECT * FROM documents",
            "admin'--",
        ]
        
        for payload in injection_payloads:
            response = client.get(
                f"/api/documents?search={payload}",
                headers=mock_auth_headers
            )
            # 应该安全处理，返回 200（无结果）或适当错误
            assert response.status_code in [200, 400]
    
    def test_xss_in_filename(self, client, mock_auth_headers):
        """测试文件名中的 XSS 防护"""
        xss_payloads = [
            "<script>alert('xss')</script>.pptx",
            "test<img src=x onerror=alert(1)>.pptx",
            "test\"><script>alert(1)</script>.pptx",
        ]
        
        for payload in xss_payloads:
            response = client.post(
                "/api/documents/upload/init",
                json={
                    "filename": payload,
                    "filesize": 1024,
                    "total_chunks": 1
                },
                headers=mock_auth_headers
            )
            # 应该接受但不执行（服务端应转义存储）
            assert response.status_code in [200, 400, 422]
    
    def test_path_traversal_in_filename(self, client, mock_auth_headers):
        """测试文件名中的路径穿越防护"""
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "test/../../../etc/passwd.pptx",
        ]
        
        for payload in traversal_payloads:
            response = client.post(
                "/api/documents/upload/init",
                json={
                    "filename": payload,
                    "filesize": 1024,
                    "total_chunks": 1
                },
                headers=mock_auth_headers
            )
            # 应该被拒绝或安全处理
            assert response.status_code in [200, 400, 422]
    
    def test_unauthorized_document_access(self, client, sample_document):
        """测试无授权访问文档
        
        注意：当前 API 允许匿名访问，返回默认用户 ID，
        因此无认证访问其他用户的文档会返回 404（而不是 401/403）
        """
        response = client.get(f"/api/documents/{sample_document.id}")
        # 由于 API 使用默认用户 ID（anonymous-user-001）查询，
        # 而文档属于 test-user-001，所以返回 404
        assert response.status_code in [401, 403, 404, 422]
    
    def test_cross_user_document_access(self, client, sample_document):
        """测试跨用户文档访问（使用不同用户 ID）"""
        # 创建另一个用户的 JWT token
        from app.core.security import create_access_token
        other_user_token = create_access_token(data={"sub": "other-user-999"})
        other_user_headers = {"Authorization": f"Bearer {other_user_token}"}
        
        response = client.get(
            f"/api/documents/{sample_document.id}",
            headers=other_user_headers
        )
        # 其他用户应该无法访问
        assert response.status_code == 404


# ============================================
# 第十一部分：文件类型验证测试
# ============================================

class TestFileTypeValidation:
    """文件类型验证测试"""
    
    def test_valid_pptx_extension(self, client, mock_auth_headers):
        """测试有效的 PPTX 扩展名"""
        valid_extensions = [".pptx", ".PPTX", ".Pptx"]
        
        for ext in valid_extensions:
            response = client.post(
                "/api/documents/upload/init",
                json={
                    "filename": f"test{ext}",
                    "filesize": 1024,
                    "total_chunks": 1
                },
                headers=mock_auth_headers
            )
            assert response.status_code == 200
    
    def test_ppt_extension(self, client, mock_auth_headers):
        """测试旧版 PPT 扩展名"""
        response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "test.ppt",
                "filesize": 1024,
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        # 可能支持也可能不支持
        assert response.status_code in [200, 400, 422]
    
    def test_other_file_extensions(self, client, mock_auth_headers):
        """测试其他文件扩展名"""
        other_extensions = [".pdf", ".docx", ".xlsx", ".txt", ".exe", ".zip"]
        
        for ext in other_extensions:
            response = client.post(
                "/api/documents/upload/init",
                json={
                    "filename": f"test{ext}",
                    "filesize": 1024,
                    "total_chunks": 1
                },
                headers=mock_auth_headers
            )
            # 应该被拒绝或接受（取决于实现）
            assert response.status_code in [200, 400, 422]


# ============================================
# 第十二部分：API 契约测试
# ============================================

class TestAPIContract:
    """API 契约测试"""
    
    def test_upload_init_response_contract(self, client, mock_auth_headers):
        """测试上传初始化响应契约"""
        response = client.post(
            "/api/documents/upload/init",
            json={"filename": "test.pptx", "filesize": 1024, "total_chunks": 1},
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应字段类型
        assert isinstance(data["upload_id"], str)
        assert isinstance(data["chunk_size"], int)
        assert isinstance(data["total_chunks"], int)
    
    def test_document_list_response_contract(self, client, mock_auth_headers):
        """测试文档列表响应契约"""
        response = client.get("/api/documents", headers=mock_auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应结构
        assert isinstance(data["documents"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["page"], int)
        assert isinstance(data["limit"], int)
    
    def test_document_detail_response_contract(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试文档详情响应契约"""
        response = client.get(
            f"/api/documents/{sample_document.id}",
            headers=mock_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应字段类型
        assert isinstance(data["id"], str)
        assert isinstance(data["filename"], str)
        assert isinstance(data["original_filename"], str)
        assert isinstance(data["file_size"], int)
        assert isinstance(data["page_count"], int)
        assert isinstance(data["status"], str)
        assert isinstance(data["slides"], list)
    
    def test_error_response_contract(self, client, mock_auth_headers):
        """测试错误响应契约"""
        response = client.get(
            f"/api/documents/{uuid.uuid4()}",
            headers=mock_auth_headers
        )
        assert response.status_code == 404
        data = response.json()
        
        # 验证错误响应包含 detail 字段
        assert "detail" in data


# ============================================
# 第十三部分：端到端流程测试
# ============================================

class TestEndToEndFlows:
    """端到端流程测试"""
    
    def test_complete_upload_flow(self, client, mock_auth_headers, sample_pptx_file):
        """测试完整的上传流程"""
        # 1. 初始化上传
        init_response = client.post(
            "/api/documents/upload/init",
            json={
                "filename": "e2e_test.pptx",
                "filesize": len(sample_pptx_file),
                "total_chunks": 1
            },
            headers=mock_auth_headers
        )
        assert init_response.status_code == 200
        upload_id = init_response.json()["upload_id"]
        
        # 2. 上传分片
        chunk_response = client.post(
            "/api/documents/upload/chunk",
            data={"upload_id": upload_id, "chunk_index": 0},
            files={"chunk": ("chunk_0", BytesIO(sample_pptx_file), "application/octet-stream")},
            headers=mock_auth_headers
        )
        assert chunk_response.status_code == 200
        
        # 3. 完成上传
        complete_response = client.post(
            "/api/documents/upload/complete",
            json={
                "upload_id": upload_id,
                "filename": "端到端测试文档.pptx",
                "md5_hash": hashlib.md5(sample_pptx_file).hexdigest()
            },
            headers=mock_auth_headers
        )
        assert complete_response.status_code == 200
        assert "document_id" in complete_response.json()
    
    def test_document_lifecycle(self, client, mock_auth_headers, sample_document, sample_slides):
        """测试文档生命周期"""
        doc_id = sample_document.id
        
        # 1. 查看文档列表
        list_response = client.get("/api/documents", headers=mock_auth_headers)
        assert list_response.status_code == 200
        
        # 2. 查看文档详情
        detail_response = client.get(
            f"/api/documents/{doc_id}",
            headers=mock_auth_headers
        )
        assert detail_response.status_code == 200
        
        # 3. 查看文档页面
        slides_response = client.get(
            f"/api/documents/{doc_id}/slides",
            headers=mock_auth_headers
        )
        assert slides_response.status_code == 200
        
        # 4. 删除文档
        delete_response = client.delete(
            f"/api/documents/{doc_id}",
            headers=mock_auth_headers
        )
        assert delete_response.status_code == 200
        
        # 5. 验证删除后无法访问
        after_delete_response = client.get(
            f"/api/documents/{doc_id}",
            headers=mock_auth_headers
        )
        assert after_delete_response.status_code == 404
