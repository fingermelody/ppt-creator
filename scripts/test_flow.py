#!/usr/bin/env python3
"""
测试完整流程：写大纲 -> 保存大纲 -> 组装 PPT
"""

import requests
import json
import time

API_BASE = "https://ppt-api-228212-9-1253851367.sh.run.tcloudbase.com"

def test_api():
    print("=" * 60)
    print("PPT 智能生成系统 - 完整流程测试")
    print("=" * 60)
    
    # 1. 测试大纲列表
    print("\n📋 步骤 1: 获取大纲列表...")
    try:
        resp = requests.get(f"{API_BASE}/api/outlines?page=1&limit=20", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        print(f"   ✅ 成功获取大纲列表，共 {data.get('total', 0)} 条")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False
    
    # 2. 测试智能生成大纲
    print("\n🤖 步骤 2: 智能生成大纲...")
    try:
        payload = {
            "description": "这是一个关于人工智能技术在现代企业管理中应用的演示文稿，包括机器学习、深度学习、自然语言处理等核心技术，以及这些技术如何帮助企业提升效率和竞争力。主要内容涵盖：1. AI技术概述及发展趋势；2. 企业智能化转型的必要性；3. AI在客户服务中的应用；4. AI在数据分析和决策中的作用；5. 实施AI战略的最佳实践。",
            "page_count": 10
        }
        resp = requests.post(
            f"{API_BASE}/api/outlines/smart-generate",
            json=payload,
            timeout=60
        )
        resp.raise_for_status()
        data = resp.json()
        outline_id = data.get('outline', {}).get('id')
        print(f"   ✅ 大纲生成成功，ID: {outline_id}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False
    
    # 3. 获取大纲详情
    print("\n📖 步骤 3: 获取大纲详情...")
    try:
        resp = requests.get(f"{API_BASE}/api/outlines/{outline_id}", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        print(f"   ✅ 大纲标题: {data.get('title', 'N/A')}")
        print(f"   ✅ 章节数: {len(data.get('sections', []))}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False
    
    # 4. 更新大纲
    print("\n✏️ 步骤 4: 更新大纲...")
    try:
        payload = {
            "title": "人工智能在企业管理中的应用 - 更新版"
        }
        resp = requests.put(
            f"{API_BASE}/api/outlines/{outline_id}",
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        print(f"   ✅ 大纲更新成功")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False
    
    # 5. 确认大纲（创建组装草稿）
    print("\n✨ 步骤 5: 确认大纲，创建组装草稿...")
    try:
        resp = requests.post(
            f"{API_BASE}/api/outlines/{outline_id}/confirm",
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        draft_id = data.get('assembly_draft_id') or data.get('draft_id')
        print(f"   ✅ 草稿创建成功，ID: {draft_id}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False
    
    # 6. 获取草稿详情
    print("\n📄 步骤 6: 获取草稿详情...")
    try:
        resp = requests.get(f"{API_BASE}/api/drafts/{draft_id}", timeout=30)
        resp.raise_for_status()
        data = resp.json()
        print(f"   ✅ 草稿标题: {data.get('title', 'N/A')}")
        print(f"   ✅ 章节数: {len(data.get('chapters', []))}")
        print(f"   ✅ 状态: {data.get('status', 'N/A')}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 所有测试通过！完整流程验证成功！")
    print("=" * 60)
    print(f"\n前端访问地址: https://ppt.bottlepeace.com/#/outline")
    print(f"新建的大纲 ID: {outline_id}")
    print(f"组装草稿 ID: {draft_id}")
    
    return True

if __name__ == "__main__":
    test_api()
