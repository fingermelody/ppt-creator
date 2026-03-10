#!/usr/bin/env python3
"""
PPT-RSD 综合功能测试脚本
测试所有核心功能模块和API端点
"""

import requests
import json
import time
from typing import Dict, List, Any
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8001"
TEST_RESULTS = []

class TestResult:
    """测试结果类"""
    def __init__(self, module: str, test_name: str, status: str, details: str = ""):
        self.module = module
        self.test_name = test_name
        self.status = status  # "passed", "failed", "warning"
        self.details = details
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self):
        return {
            "module": self.module,
            "test_name": self.test_name,
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp
        }

def test_api(endpoint: str, method: str = "GET", data: Dict = None, params: Dict = None) -> tuple:
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            return None, f"不支持的HTTP方法: {method}"
        
        return response.status_code, response.json() if response.content else {}
    except requests.exceptions.Timeout:
        return None, "请求超时"
    except requests.exceptions.ConnectionError:
        return None, "连接失败"
    except Exception as e:
        return None, f"异常: {str(e)}"

def add_result(module: str, test_name: str, status: str, details: str = ""):
    """添加测试结果"""
    result = TestResult(module, test_name, status, details)
    TEST_RESULTS.append(result)
    status_emoji = {"passed": "✅", "failed": "❌", "warning": "⚠️"}[status]
    print(f"{status_emoji} [{module}] {test_name}: {details}")

# ============== 1. 健康检查测试 ==============
print("\n" + "="*60)
print("1. 健康检查测试")
print("="*60)

status_code, response = test_api("/health")
if status_code == 200 and response.get("status") == "healthy":
    add_result("系统健康", "后端服务状态", "passed", "服务运行正常")
else:
    add_result("系统健康", "后端服务状态", "failed", f"服务异常: {response}")

# ============== 2. 文档库管理测试 ==============
print("\n" + "="*60)
print("2. PPT文档库管理测试")
print("="*60)

# 2.1 文档列表
status_code, response = test_api("/api/documents", params={"page": 1, "limit": 10})
if status_code == 200 and "documents" in response:
    doc_count = len(response.get("documents", []))
    add_result("文档库", "获取文档列表", "passed", f"成功获取{doc_count}个文档")
    
    # 保存第一个文档ID用于后续测试
    if doc_count > 0:
        TEST_DOC_ID = response["documents"][0]["id"]
    else:
        TEST_DOC_ID = None
else:
    add_result("文档库", "获取文档列表", "failed", f"失败: {response}")
    TEST_DOC_ID = None

# 2.2 文档详情
if TEST_DOC_ID:
    status_code, response = test_api(f"/api/documents/{TEST_DOC_ID}")
    if status_code == 200 and "id" in response:
        add_result("文档库", "获取文档详情", "passed", f"文档: {response.get('title', 'N/A')}")
    else:
        add_result("文档库", "获取文档详情", "failed", f"失败: {response}")
else:
    add_result("文档库", "获取文档详情", "warning", "无可用的测试文档")

# 2.3 文档搜索
status_code, response = test_api("/api/documents/search", params={"query": "腾讯云"})
if status_code == 200:
    results = response.get("results", [])
    add_result("文档库", "语义检索功能", "passed" if results else "warning", 
               f"找到{len(results)}个相关结果")
else:
    add_result("文档库", "语义检索功能", "failed", f"失败: {response}")

# ============== 3. 大纲设计测试 ==============
print("\n" + "="*60)
print("3. PPT大纲设计测试")
print("="*60)

# 3.1 智能生成大纲
outline_data = {
    "topic": "人工智能在教育领域的应用",
    "description": "探讨AI技术如何改变传统教育方式",  # 添加description字段
    "page_count": 10,
    "mode": "smart"
}
status_code, response = test_api("/api/outlines/smart-generate", method="POST", data=outline_data)
if status_code == 200 and ("id" in response or "outline" in response):
    outline = response.get("outline", response)
    section_count = len(outline.get("chapters", []))
    add_result("大纲设计", "智能生成大纲", "passed", f"成功生成{section_count}个章节")
    TEST_OUTLINE_ID = outline.get("id")
else:
    add_result("大纲设计", "智能生成大纲", "failed", f"失败: {response}")
    TEST_OUTLINE_ID = None

# 3.2 向导式生成大纲
wizard_data = {
    "topic": "企业数字化转型实践",
    "page_count": 12
}
status_code, response = test_api("/api/outlines/generate/wizard/step1", method="POST", data=wizard_data)
if status_code == 200 and "session_id" in response:
    add_result("大纲设计", "向导式生成大纲", "passed", f"成功创建向导会话")
else:
    add_result("大纲设计", "向导式生成大纲", "failed", f"失败: {response}")

# 3.3 大纲保存
if TEST_OUTLINE_ID:
    update_data = {
        "sections": [
            {"title": "引言", "description": "介绍背景和意义", "order": 1},
            {"title": "现状分析", "description": "当前问题分析", "order": 2}
        ]
    }
    status_code, response = test_api(f"/api/outlines/{TEST_OUTLINE_ID}", 
                                    method="PUT", data=update_data)
    if status_code == 200:
        add_result("大纲设计", "大纲编辑保存", "passed", "保存成功")
    else:
        add_result("大纲设计", "大纲编辑保存", "failed", f"失败: {response}")
else:
    add_result("大纲设计", "大纲编辑保存", "warning", "无可用的大纲ID")

# ============== 4. 页面组装测试 ==============
print("\n" + "="*60)
print("4. PPT页面组装测试")
print("="*60)

# 4.1 智能检索页面
if TEST_DOC_ID:
    search_data = {"query": "产品介绍", "n_results": 5}
    status_code, response = test_api(f"/api/documents/{TEST_DOC_ID}/slides/search",
                                    method="POST", data=search_data)
    if status_code == 200:
        results = response.get("results", [])
        add_result("页面组装", "智能检索页面", "passed" if results else "warning",
                   f"找到{len(results)}个相关页面")
    else:
        add_result("页面组装", "智能检索页面", "failed", f"失败: {response}")
else:
    add_result("页面组装", "智能检索页面", "warning", "无可用的测试文档")

# 4.2 获取所有幻灯片
if TEST_DOC_ID:
    status_code, response = test_api(f"/api/documents/{TEST_DOC_ID}/slides")
    if status_code == 200:
        slides = response.get("slides", [])
        add_result("页面组装", "获取幻灯片列表", "passed", f"获取到{len(slides)}张幻灯片")
    else:
        add_result("页面组装", "获取幻灯片列表", "failed", f"失败: {response}")

# ============== 5. 草稿管理测试 ==============
print("\n" + "="*60)
print("5. 草稿管理测试")
print("="*60)

# 5.1 创建草稿
draft_data = {
    "title": "测试草稿PPT",
    "description": "这是一个测试草稿"
}
status_code, response = test_api("/api/drafts", method="POST", data=draft_data)
if status_code == 200 and "id" in response:
    TEST_DRAFT_ID = response["id"]
    add_result("草稿管理", "创建草稿", "passed", f"草稿ID: {TEST_DRAFT_ID}")
else:
    add_result("草稿管理", "创建草稿", "failed", f"失败: {response}")
    TEST_DRAFT_ID = None

# 5.2 获取草稿列表
status_code, response = test_api("/api/drafts")
if status_code == 200 and "drafts" in response:
    draft_count = len(response.get("drafts", []))
    add_result("草稿管理", "获取草稿列表", "passed", f"找到{draft_count}个草稿")
else:
    add_result("草稿管理", "获取草稿列表", "failed", f"失败: {response}")

# 5.3 更新草稿
if TEST_DRAFT_ID:
    update_data = {"title": "更新后的草稿标题"}
    status_code, response = test_api(f"/api/drafts/{TEST_DRAFT_ID}",
                                    method="PUT", data=update_data)
    if status_code == 200:
        add_result("草稿管理", "更新草稿", "passed", "更新成功")
    else:
        add_result("草稿管理", "更新草稿", "failed", f"失败: {response}")

# ============== 6. PPT精修测试 ==============
print("\n" + "="*60)
print("6. PPT精修测试")
print("="*60)

# 6.1 创建精修任务
refinement_data = {
    "draft_id": TEST_DRAFT_ID,
    "pages": [1, 2, 3]
}
status_code, response = test_api("/api/refinement/tasks", method="POST", data=refinement_data)
if status_code == 200 and "id" in response:
    TEST_REFINEMENT_ID = response["id"]
    add_result("PPT精修", "创建精修任务", "passed", f"任务ID: {TEST_REFINEMENT_ID}")
else:
    add_result("PPT精修", "创建精修任务", "warning", f"需要草稿ID: {response}")
    TEST_REFINEMENT_ID = None

# 6.2 获取精修任务列表
status_code, response = test_api("/api/refinement/tasks")
if status_code == 200:
    tasks = response.get("tasks", [])
    add_result("PPT精修", "获取精修任务列表", "passed", f"找到{len(tasks)}个任务")
else:
    add_result("PPT精修", "获取精修任务列表", "failed", f"失败: {response}")

# ============== 7. 智能生成测试 ==============
print("\n" + "="*60)
print("7. PPT智能生成测试")
print("="*60)

# 7.1 创建生成任务
generation_data = {
    "topic": "云计算技术发展趋势",
    "page_count": 8,
    "search_depth": "normal"
}
status_code, response = test_api("/api/generation/tasks", method="POST", data=generation_data)
if status_code == 200 and "id" in response:
    TEST_GENERATION_ID = response["id"]
    add_result("智能生成", "创建生成任务", "passed", f"任务ID: {TEST_GENERATION_ID}")
else:
    add_result("智能生成", "创建生成任务", "failed", f"失败: {response}")
    TEST_GENERATION_ID = None

# 7.2 获取生成任务列表
status_code, response = test_api("/api/generation/tasks")
if status_code == 200:
    tasks = response.get("tasks", [])
    add_result("智能生成", "获取生成任务列表", "passed", f"找到{len(tasks)}个任务")
else:
    add_result("智能生成", "获取生成任务列表", "failed", f"失败: {response}")

# 7.3 获取模板列表
status_code, response = test_api("/api/generation/templates")
if status_code == 200:
    templates = response.get("templates", [])
    add_result("智能生成", "获取模板列表", "passed", f"找到{len(templates)}个模板")
else:
    add_result("智能生成", "获取模板列表", "failed", f"失败: {response}")

# ============== 8. 统计结果 ==============
print("\n" + "="*60)
print("测试结果统计")
print("="*60)

passed = sum(1 for r in TEST_RESULTS if r.status == "passed")
failed = sum(1 for r in TEST_RESULTS if r.status == "failed")
warning = sum(1 for r in TEST_RESULTS if r.status == "warning")
total = len(TEST_RESULTS)

print(f"总计: {total} 项测试")
print(f"✅ 通过: {passed} ({passed/total*100:.1f}%)")
print(f"❌ 失败: {failed} ({failed/total*100:.1f}%)")
print(f"⚠️  警告: {warning} ({warning/total*100:.1f}%)")

# 保存结果到文件
output_file = "/Users/ping/CodeBuddy/PPT-RSD/test_results.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump({
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "warning": warning,
            "pass_rate": f"{passed/total*100:.1f}%"
        },
        "results": [r.to_dict() for r in TEST_RESULTS],
        "test_time": datetime.now().isoformat()
    }, f, ensure_ascii=False, indent=2)

print(f"\n测试结果已保存到: {output_file}")
