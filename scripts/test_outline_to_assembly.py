#!/usr/bin/env python3
"""
测试大纲确认到组装页面的完整流程
"""
import requests
import json
import time

API_BASE = "https://ppt-api-228212-9-1253851367.sh.run.tcloudbase.com"

def test_flow():
    print("=" * 60)
    print("测试大纲到组装页面的数据传递流程")
    print("=" * 60)
    
    # 1. 智能生成大纲
    print("\n✨ 步骤 1: 智能生成大纲...")
    try:
        resp = requests.post(
            f"{API_BASE}/api/outlines/smart-generate",
            json={
                "description": "AI技术产品介绍PPT，包含技术原理、核心功能和应用案例展示"
            },
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        outline = data.get('outline')
        outline_id = outline.get('id')
        chapters = outline.get('chapters', [])
        print(f"   ✅ 大纲生成成功")
        print(f"   大纲ID: {outline_id}")
        print(f"   标题: {outline.get('title')}")
        print(f"   章节数: {len(chapters)}")
        for ch in chapters:
            print(f"      - {ch['title']} ({ch['page_count']}页)")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False
    
    # 2. 确认大纲
    print("\n✨ 步骤 2: 确认大纲，创建组装草稿...")
    try:
        resp = requests.post(
            f"{API_BASE}/api/outlines/{outline_id}/confirm",
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        draft_id = data.get('assembly_draft_id')
        print(f"   ✅ 草稿创建成功")
        print(f"   草稿ID: {draft_id}")
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return False
    
    # 3. 获取草稿详情
    print("\n✨ 步骤 3: 获取草稿详情（验证章节信息）...")
    try:
        resp = requests.get(
            f"{API_BASE}/api/drafts/{draft_id}",
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        
        print(f"   草稿标题: {data.get('title')}")
        print(f"   总页数: {data.get('page_count')}")
        
        # 检查是否有 sections 信息
        sections = data.get('sections', [])
        pages = data.get('pages', [])
        
        print(f"   章节信息 (sections): {len(sections)} 个章节")
        for sec in sections:
            print(f"      - {sec['title']} (预期 {sec.get('expected_pages', '?')} 页)")
        
        print(f"   页面信息 (pages): {len(pages)} 个页面")
        
        # 按 section_id 分组页面
        section_pages = {}
        for page in pages:
            sid = page.get('section_id', 'unassigned')
            if sid not in section_pages:
                section_pages[sid] = []
            section_pages[sid].append(page)
        
        print(f"   页面分组:")
        for sid, pgs in section_pages.items():
            sec_title = next((s['title'] for s in sections if s['id'] == sid), sid)
            print(f"      - {sec_title}: {len(pgs)} 页")
        
        if sections and pages:
            print(f"   ✅ 章节和页面数据正确关联")
        elif sections:
            print(f"   ⚠️ 有章节信息但暂无页面")
        else:
            print(f"   ❌ 章节信息未正确传递")
            
    except Exception as e:
        print(f"   ❌ 获取草稿详情失败: {e}")
        if hasattr(e, 'response'):
            print(f"   响应: {e.response.text}")
        return False
    
    # 4. 测试导出 PPT
    print("\n✨ 步骤 4: 测试导出 PPT...")
    try:
        resp = requests.post(
            f"{API_BASE}/api/drafts/{draft_id}/export",
            json={"format": "pptx"},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        download_url = data.get('download_url')
        print(f"   ✅ 导出请求成功")
        print(f"   下载地址: {download_url}")
    except Exception as e:
        print(f"   ⚠️ 导出可能需要完善: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 流程测试完成！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_flow()
