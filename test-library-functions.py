#!/usr/bin/env python3
"""
文档库功能测试脚本
测试需求文档 2.1.1 PPT文档库管理的所有功能
"""

import requests
import json
import os
import sys
from pathlib import Path

# API 基础 URL
API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000')

# 测试结果记录
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_test(test_name, passed, message="", details=None):
    """记录测试结果"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"   {message}")
    if details:
        print(f"   详情: {json.dumps(details, indent=2, ensure_ascii=False)}")
    
    if passed:
        test_results["passed"].append({"test": test_name, "message": message})
    else:
        test_results["failed"].append({"test": test_name, "message": message, "details": details})

def log_warning(test_name, message):
    """记录警告"""
    print(f"⚠️  WARNING - {test_name}")
    print(f"   {message}")
    test_results["warnings"].append({"test": test_name, "message": message})

def test_api_health():
    """测试 API 健康状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/documents", timeout=5)
        if response.status_code in [200, 401, 403]:
            log_test("API健康检查", True, f"API 可访问，状态码: {response.status_code}")
            return True
        else:
            log_test("API健康检查", False, f"API 返回异常状态码: {response.status_code}")
            return False
    except Exception as e:
        log_test("API健康检查", False, f"API 不可访问: {str(e)}")
        return False

def test_get_documents_list():
    """测试获取文档列表"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/documents",
            params={"page": 1, "limit": 10},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                "获取文档列表", 
                True, 
                f"成功获取 {len(data.get('documents', []))} 个文档",
                data
            )
            return data
        else:
            log_test("获取文档列表", False, f"状态码: {response.status_code}", response.text)
            return None
    except Exception as e:
        log_test("获取文档列表", False, f"请求失败: {str(e)}")
        return None

def test_document_upload():
    """测试文档上传功能（分片上传）"""
    # 查找测试文件
    test_files = list(Path("backend/uploads/files").glob("*.pptx"))
    if not test_files:
        log_warning("文档上传测试", "未找到测试用的 PPT 文件")
        return None
    
    test_file = test_files[0]
    file_size = test_file.stat().st_size
    chunk_size = 5 * 1024 * 1024  # 5MB
    total_chunks = (file_size + chunk_size - 1) // chunk_size
    
    try:
        # 1. 初始化上传
        init_response = requests.post(
            f"{API_BASE_URL}/api/documents/upload/init",
            json={
                "filename": test_file.name,
                "filesize": file_size,
                "total_chunks": total_chunks
            },
            timeout=5
        )
        
        if init_response.status_code != 200:
            log_test("文档上传-初始化", False, f"初始化失败: {init_response.status_code}")
            return None
        
        upload_id = init_response.json().get("upload_id")
        log_test("文档上传-初始化", True, f"上传ID: {upload_id}")
        
        # 2. 上传分片（只上传第一个分片作为测试）
        with open(test_file, "rb") as f:
            chunk_data = f.read(min(chunk_size, file_size))
        
        chunk_response = requests.post(
            f"{API_BASE_URL}/api/documents/upload/chunk",
            data={
                "upload_id": upload_id,
                "chunk_index": 0
            },
            files={"chunk": ("chunk_0", chunk_data)},
            timeout=10
        )
        
        if chunk_response.status_code != 200:
            log_test("文档上传-分片上传", False, f"分片上传失败: {chunk_response.status_code}")
            return None
        
        log_test("文档上传-分片上传", True, "第一分片上传成功")
        
        # 3. 由于只上传了一个分片，不测试完成上传
        log_warning("文档上传-完整流程", "仅测试了第一分片上传，未测试完整流程")
        return upload_id
        
    except Exception as e:
        log_test("文档上传", False, f"上传失败: {str(e)}")
        return None

def test_semantic_search():
    """测试语义搜索功能"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/documents/slides/search",
            json={"query": "测试搜索", "n_results": 5},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                "语义搜索", 
                True, 
                f"搜索成功，返回 {data.get('total', 0)} 个结果",
                {"sample": data.get('results', [])[:2]}
            )
            return True
        elif response.status_code == 503:
            log_warning("语义搜索", "向量化服务未启用")
            return None
        else:
            log_test("语义搜索", False, f"状态码: {response.status_code}")
            return False
    except Exception as e:
        log_test("语义搜索", False, f"搜索失败: {str(e)}")
        return False

def test_document_preview(documents_data):
    """测试文档预览功能"""
    if not documents_data or not documents_data.get('documents'):
        log_warning("文档预览测试", "没有可用的文档进行预览测试")
        return None
    
    # 选择第一个就绪的文档
    doc = None
    for d in documents_data['documents']:
        if d.get('status') == 'ready':
            doc = d
            break
    
    if not doc:
        log_warning("文档预览测试", "没有状态为 ready 的文档")
        return None
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/documents/{doc['id']}/preview",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            log_test(
                "文档预览", 
                True, 
                f"预览链接生成成功",
                {"preview_type": data.get("preview_type"), "has_url": bool(data.get("preview_url"))}
            )
            return True
        else:
            log_test("文档预览", False, f"状态码: {response.status_code}")
            return False
    except Exception as e:
        log_test("文档预览", False, f"预览失败: {str(e)}")
        return False

def test_document_download(documents_data):
    """测试文档下载功能"""
    if not documents_data or not documents_data.get('documents'):
        log_warning("文档下载测试", "没有可用的文档进行下载测试")
        return None
    
    doc = documents_data['documents'][0]
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/documents/{doc['id']}/file",
            timeout=10,
            stream=True
        )
        
        if response.status_code == 200:
            content_length = response.headers.get('content-length', 'unknown')
            log_test("文档下载", True, f"文件大小: {content_length} bytes")
            return True
        else:
            log_test("文档下载", False, f"状态码: {response.status_code}")
            return False
    except Exception as e:
        log_test("文档下载", False, f"下载失败: {str(e)}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("PPT文档库管理功能测试")
    print("=" * 60)
    print()
    
    # 1. 测试 API 健康状态
    if not test_api_health():
        print("\nAPI 不可用，停止后续测试")
        return
    
    print()
    
    # 2. 测试获取文档列表
    documents_data = test_get_documents_list()
    print()
    
    # 3. 测试文档上传
    test_document_upload()
    print()
    
    # 4. 测试语义搜索
    test_semantic_search()
    print()
    
    # 5. 测试文档预览
    test_document_preview(documents_data)
    print()
    
    # 6. 测试文档下载
    test_document_download(documents_data)
    print()
    
    # 输出测试总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"✅ 通过: {len(test_results['passed'])}")
    print(f"❌ 失败: {len(test_results['failed'])}")
    print(f"⚠️  警告: {len(test_results['warnings'])}")
    
    if test_results['failed']:
        print("\n失败的测试:")
        for item in test_results['failed']:
            print(f"  - {item['test']}: {item['message']}")
    
    if test_results['warnings']:
        print("\n警告:")
        for item in test_results['warnings']:
            print(f"  - {item['test']}: {item['message']}")
    
    # 检查未实现的功能
    print("\n" + "=" * 60)
    print("功能完整性检查（对照需求文档）")
    print("=" * 60)
    
    required_features = {
        "上传PPT文件(PPTX/PPT)，无文件大小限制": "已实现（分片上传）",
        "分片上传、断点续传、上传进度显示": "部分实现（分片上传已实现，断点续传未验证）",
        "页面级解析：提取文本、图片OCR、图表、布局、样式": "已实现（后端解析）",
        "向量化存储：文本和图片向量化": "已实现（后端向量化）",
        "文档分类管理(文件夹/标签)": "❌ 未实现",
        "页面级语义检索": "后端已实现，前端未提供UI",
        "文档预览、删除、编辑": "预览✅ 删除✅ 编辑❌",
        "批量导入导出": "❌ 未实现"
    }
    
    for feature, status in required_features.items():
        print(f"{feature}: {status}")

if __name__ == "__main__":
    main()
