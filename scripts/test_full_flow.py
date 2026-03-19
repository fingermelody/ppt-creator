#!/usr/bin/env python3
"""
完整流程测试脚本
测试从大纲生成到PPT导出的完整流程
"""

import requests
import json
import time
import os

BASE_URL = "https://ppt-api-228212-9-1253851367.sh.run.tcloudbase.com"

def test_full_flow():
    print("=" * 60)
    print("PPT 生成完整流程测试")
    print("=" * 60)
    
    # 步骤 1: 智能生成大纲
    print("\n✨ 步骤 1: 智能生成大纲...")
    response = requests.post(
        f"{BASE_URL}/api/outlines/smart-generate",
        json={"description": "人工智能技术发展与应用案例介绍PPT"}
    )
    
    if response.status_code != 200:
        print(f"   ❌ 大纲生成失败: {response.text}")
        return False
    
    data = response.json()
    # 提取 outline 对象
    outline = data.get('outline', data)
    outline_id = outline['id']
    print(f"   ✅ 大纲生成成功")
    print(f"   大纲ID: {outline_id}")
    print(f"   标题: {outline.get('title', '无标题')}")
    
    # 章节信息在 chapters 字段中
    sections = outline.get('chapters', outline.get('sections', []))
    total_pages = sum(s.get('expected_pages', s.get('page_count', 1)) for s in sections)
    print(f"   章节数: {len(sections)}, 预计页数: {total_pages}")
    for s in sections:
        pg = s.get('expected_pages', s.get('page_count', 1))
        print(f"      - {s['title']} ({pg}页)")
    
    # 步骤 2: 确认大纲
    print("\n✨ 步骤 2: 确认大纲，创建组装草稿...")
    response = requests.post(f"{BASE_URL}/api/outlines/{outline_id}/confirm")
    
    if response.status_code != 200:
        print(f"   ❌ 确认大纲失败: {response.text}")
        return False
    
    data = response.json()
    draft_id = data['assembly_draft_id']
    print(f"   ✅ 草稿创建成功")
    print(f"   草稿ID: {draft_id}")
    
    # 步骤 3: 获取草稿详情
    print("\n✨ 步骤 3: 获取草稿详情...")
    response = requests.get(f"{BASE_URL}/api/drafts/{draft_id}")
    
    if response.status_code != 200:
        print(f"   ❌ 获取草稿详情失败: {response.text}")
        return False
    
    data = response.json()
    print(f"   草稿标题: {data['title']}")
    print(f"   页面数: {data['page_count']}")
    
    sections = data.get('sections', [])
    pages = data.get('pages', [])
    
    if sections:
        print(f"   ✅ 包含章节信息: {len(sections)} 个章节")
        for s in sections:
            print(f"      - {s['title']}")
    else:
        print("   ⚠️ 未包含章节信息")
    
    if pages:
        print(f"   ✅ 包含页面信息: {len(pages)} 个页面")
    else:
        print("   ⚠️ 未包含页面信息")
    
    # 步骤 4: 导出 PPT
    print("\n✨ 步骤 4: 导出 PPT 文件...")
    response = requests.post(
        f"{BASE_URL}/api/drafts/{draft_id}/export",
        json={"format": "pptx"}
    )
    
    if response.status_code != 200:
        print(f"   ❌ 导出失败: {response.text}")
        return False
    
    data = response.json()
    download_url = data['download_url']
    file_name = data['file_name']
    file_size = data['file_size']
    
    print(f"   ✅ 导出成功")
    print(f"   文件名: {file_name}")
    print(f"   文件大小: {file_size} 字节 ({file_size/1024:.2f} KB)")
    print(f"   下载地址: {download_url}")
    
    # 步骤 5: 下载并验证文件
    print("\n✨ 步骤 5: 下载并验证 PPT 文件...")
    full_download_url = f"{BASE_URL}{download_url}"
    response = requests.get(full_download_url)
    
    if response.status_code != 200:
        print(f"   ❌ 下载失败: {response.status_code}")
        return False
    
    # 保存文件
    output_file = "/tmp/exported_presentation.pptx"
    with open(output_file, 'wb') as f:
        f.write(response.content)
    
    actual_size = os.path.getsize(output_file)
    print(f"   ✅ 文件下载成功")
    print(f"   保存位置: {output_file}")
    print(f"   实际大小: {actual_size} 字节 ({actual_size/1024:.2f} KB)")
    
    # 验证是否为有效的 ZIP 格式（PPTX 是 ZIP 格式）
    import zipfile
    try:
        with zipfile.ZipFile(output_file, 'r') as z:
            file_list = z.namelist()
            if '[Content_Types].xml' in file_list and any('ppt/' in f for f in file_list):
                print(f"   ✅ 文件格式验证通过（有效的 PPTX 文件）")
                slide_count = len([f for f in file_list if f.startswith('ppt/slides/slide') and f.endswith('.xml')])
                print(f"   幻灯片数量: {slide_count}")
            else:
                print(f"   ❌ 文件格式验证失败")
                return False
    except zipfile.BadZipFile:
        print(f"   ❌ 文件不是有效的 ZIP/PPTX 格式")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 完整流程测试通过！")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = test_full_flow()
    exit(0 if success else 1)
