#!/usr/bin/env python3
"""
PPT 组装功能高级测试脚本
测试范围：预览PPT、导出PPT、页面编辑、章节操作
"""

from playwright.sync_api import sync_playwright
import time
import requests
import json

FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"
SCREENSHOT_DIR = "/tmp"

def get_existing_draft():
    """获取已有的草稿 ID"""
    try:
        resp = requests.get(f"{BACKEND_URL}/api/drafts", timeout=10)
        data = resp.json()
        if data.get("drafts") and len(data["drafts"]) > 0:
            return data["drafts"][0]
        return None
    except Exception as e:
        print(f"获取草稿失败: {e}")
        return None

def test_assembly_advanced():
    """组装功能高级测试"""
    
    # 获取已有草稿
    draft = get_existing_draft()
    if not draft:
        print("❌ 没有可用的草稿，请先创建一个草稿")
        return False
    
    draft_id = draft["id"]
    outline_id = draft.get("outline_id", "")
    print(f"使用草稿: {draft['title']} (ID: {draft_id})")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # 监听
        console_logs = []
        errors = []
        downloads = []
        
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on('pageerror', lambda err: errors.append(str(err)))
        page.on('download', lambda download: downloads.append(download))
        
        results = {}
        
        # ========== 准备：进入组装页面 ==========
        print("\n" + "="*60)
        print("准备阶段：直接进入组装页面")
        print("="*60)
        
        try:
            url = f'{FRONTEND_URL}/#/assembly/{draft_id}'
            if outline_id:
                url += f'?outline={outline_id}'
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(3)
            page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_00_ready.png', full_page=True)
            
            if '/assembly/' in page.url:
                print(f"✅ 已进入组装页面: {page.url}")
            else:
                print(f"⚠️ URL: {page.url}")
                
        except Exception as e:
            print(f"❌ 准备阶段失败: {e}")
            page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_00_error.png', full_page=True)
            browser.close()
            return False
        
        # ========== 测试 1: 页面结构验证 ==========
        print("\n" + "="*60)
        print("测试 1: 页面结构验证")
        print("="*60)
        
        try:
            # 检查章节侧边栏
            sidebar = page.locator('.chapters-sidebar')
            chapters = page.locator('.chapter-panel')
            slides_grid = page.locator('.slides-grid')
            
            print(f"   章节侧边栏: {'存在' if sidebar.count() > 0 else '不存在'}")
            print(f"   章节数量: {chapters.count()}")
            print(f"   幻灯片区域: {'存在' if slides_grid.count() > 0 else '不存在'}")
            
            if sidebar.count() > 0 and chapters.count() > 0:
                results['test_1'] = 'PASS'
            else:
                results['test_1'] = 'WARN'
                
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_1'] = 'FAIL'
        
        # ========== 测试 2: 章节选择和展示 ==========
        print("\n" + "="*60)
        print("测试 2: 章节选择和展示")
        print("="*60)
        
        try:
            chapters = page.locator('.chapter-panel')
            chapter_count = chapters.count()
            
            if chapter_count > 0:
                # 点击每个章节
                for i in range(min(3, chapter_count)):
                    chapters.nth(i).click()
                    time.sleep(0.5)
                    print(f"   选择章节 {i+1}")
                
                page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_02_chapters.png', full_page=True)
                
                # 检查幻灯片预览更新
                slides = page.locator('.slide-preview, .slide-item')
                print(f"   当前幻灯片数: {slides.count()}")
                
                results['test_2'] = 'PASS'
            else:
                print("⚠️ 没有章节")
                results['test_2'] = 'WARN'
                
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_2'] = 'FAIL'
        
        # ========== 测试 3: 幻灯片预览交互 ==========
        print("\n" + "="*60)
        print("测试 3: 幻灯片预览交互")
        print("="*60)
        
        try:
            slides = page.locator('.slide-preview, .slide-item, .slide-card')
            slide_count = slides.count()
            
            if slide_count > 0:
                print(f"   幻灯片总数: {slide_count}")
                
                # 点击第一个幻灯片
                slides.first.click()
                time.sleep(0.5)
                page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_03_slide.png', full_page=True)
                
                # 检查 hover 效果区域的按钮
                hover_btns = page.locator('.slide-hover-buttons button, .slide-actions button')
                print(f"   操作按钮数: {hover_btns.count()}")
                
                results['test_3'] = 'PASS'
            else:
                print("⚠️ 没有幻灯片")
                results['test_3'] = 'WARN'
                
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_3'] = 'FAIL'
        
        # ========== 测试 4: 预览PPT按钮 ==========
        print("\n" + "="*60)
        print("测试 4: 预览PPT按钮")
        print("="*60)
        
        try:
            preview_btn = page.locator('button:has-text("预览")')
            if preview_btn.count() > 0:
                is_disabled = preview_btn.first.get_attribute('disabled')
                print(f"   预览按钮: {'禁用' if is_disabled else '可用'}")
                
                if not is_disabled:
                    preview_btn.first.click()
                    print("   已点击预览按钮")
                    time.sleep(3)
                    
                    page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_04_preview.png', full_page=True)
                    
                    # 检查预览对话框
                    dialog = page.locator('.t-dialog')
                    if dialog.count() > 0 and dialog.first.is_visible():
                        print("✅ 预览对话框已显示")
                        
                        # 检查内容
                        iframe = page.locator('iframe')
                        print(f"   iframe: {iframe.count() > 0}")
                        
                        # 关闭
                        close_btn = page.locator('.t-dialog__close')
                        if close_btn.count() > 0:
                            close_btn.first.click()
                            time.sleep(0.5)
                        
                        results['test_4'] = 'PASS'
                    else:
                        print("⚠️ 对话框未显示")
                        results['test_4'] = 'WARN'
                else:
                    print("   按钮被禁用，跳过点击")
                    results['test_4'] = 'SKIP'
            else:
                print("⚠️ 未找到预览按钮")
                results['test_4'] = 'WARN'
                
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_4'] = 'FAIL'
            page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_04_error.png')
        
        # 确保预览对话框关闭
        print("   确保对话框关闭...")
        
        # 使用 JavaScript 强制关闭所有对话框
        page.evaluate('''() => {
            // 移除所有 dialog portal
            document.querySelectorAll('.t-portal-wrapper').forEach(el => el.remove());
            // 移除 overlay
            document.querySelectorAll('.t-dialog__wrap, .t-dialog__mask').forEach(el => el.remove());
        }''')
        time.sleep(1)
        
        # ESC 兜底
        for _ in range(3):
            try:
                page.keyboard.press('Escape')
                time.sleep(0.3)
            except:
                pass
        time.sleep(1)
        
        # ========== 测试 5: 导出PPT按钮 ==========
        print("\n" + "="*60)
        print("测试 5: 导出PPT按钮")
        print("="*60)
        
        try:
            export_btn = page.locator('button:has-text("导出")')
            if export_btn.count() > 0:
                is_disabled = export_btn.first.get_attribute('disabled')
                print(f"   导出按钮: {'禁用' if is_disabled else '可用'}")
                
                if not is_disabled:
                    export_btn.first.click()
                    print("   已点击导出按钮")
                    time.sleep(1)
                    
                    # 检查确认对话框
                    confirm_dialog = page.locator('.t-dialog')
                    if confirm_dialog.count() > 0 and confirm_dialog.first.is_visible():
                        print("   确认对话框已显示")
                        page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_05_confirm.png', full_page=True)
                        
                        # 点击取消按钮（避免真正导出影响后续测试）
                        cancel_btn = page.locator('.t-dialog button:has-text("取消")')
                        if cancel_btn.count() > 0:
                            cancel_btn.first.click()
                            print("   已点击取消")
                            time.sleep(0.5)
                        else:
                            # 关闭对话框
                            close_btn = page.locator('.t-dialog__close')
                            if close_btn.count() > 0:
                                close_btn.first.click()
                                time.sleep(0.5)
                        
                        results['test_5'] = 'PASS'
                    else:
                        print("   未显示确认对话框")
                        results['test_5'] = 'WARN'
                    
                    page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_05_export.png', full_page=True)
                else:
                    print("   按钮被禁用")
                    results['test_5'] = 'SKIP'
            else:
                print("⚠️ 未找到导出按钮")
                results['test_5'] = 'WARN'
                
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_5'] = 'FAIL'
            results['test_5'] = 'FAIL'
        
        # 确保关闭所有对话框
        print("\n   清理：关闭所有对话框...")
        try:
            # 使用 JavaScript 强制移除所有对话框
            page.evaluate('''() => {
                document.querySelectorAll('.t-portal-wrapper').forEach(el => el.remove());
                document.querySelectorAll('.t-dialog__wrap, .t-dialog__mask').forEach(el => el.remove());
            }''')
            time.sleep(0.5)
            
            # ESC 兜底
            for _ in range(3):
                page.keyboard.press('Escape')
                time.sleep(0.2)
            time.sleep(0.5)
            print("   清理完成")
        except Exception as clean_err:
            print(f"   清理时出错: {clean_err}")
        
        # ========== 测试 6: 添加章节对话框 ==========
        print("\n" + "="*60)
        print("测试 6: 添加章节对话框")
        print("="*60)
        
        try:
            add_btn = page.locator('button:has-text("添加章节")')
            if add_btn.count() > 0:
                add_btn.first.click()
                time.sleep(1)
                
                dialog = page.locator('.t-dialog')
                if dialog.count() > 0 and dialog.first.is_visible():
                    print("✅ 添加章节对话框已显示")
                    page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_06_add.png', full_page=True)
                    
                    # 检查表单字段
                    title_input = page.locator('input')
                    textarea = page.locator('textarea')
                    print(f"   输入框: {title_input.count()}, 文本框: {textarea.count()}")
                    
                    # 关闭
                    close_btn = page.locator('.t-dialog__close')
                    if close_btn.count() > 0:
                        close_btn.first.click()
                    
                    results['test_6'] = 'PASS'
                else:
                    print("⚠️ 对话框未显示")
                    results['test_6'] = 'WARN'
            else:
                print("⚠️ 未找到添加章节按钮")
                results['test_6'] = 'WARN'
                
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_6'] = 'FAIL'
        
        # ========== 测试 7: 查看备选功能 ==========
        print("\n" + "="*60)
        print("测试 7: 查看备选功能")
        print("="*60)
        
        try:
            # 先选择一个幻灯片
            slides = page.locator('.slide-preview, .slide-item')
            if slides.count() > 0:
                slides.first.hover()
                time.sleep(0.5)
                
                alt_btn = page.locator('button:has-text("查看备选"), .view-alternatives-btn')
                if alt_btn.count() > 0 and alt_btn.first.is_visible():
                    alt_btn.first.click()
                    time.sleep(1)
                    page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_07_alt.png', full_page=True)
                    print("✅ 已点击查看备选")
                    
                    # 检查对话框
                    dialog = page.locator('.t-dialog, .alternatives-dialog')
                    if dialog.count() > 0:
                        print("✅ 备选对话框已显示")
                        
                        # 使用 JavaScript 关闭对话框
                        page.evaluate('''() => {
                            document.querySelectorAll('.t-portal-wrapper').forEach(el => el.remove());
                        }''')
                        time.sleep(0.5)
                        
                        results['test_7'] = 'PASS'
                    else:
                        results['test_7'] = 'WARN'
                else:
                    print("⚠️ 未找到查看备选按钮")
                    results['test_7'] = 'SKIP'
            else:
                results['test_7'] = 'SKIP'
                
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_7'] = 'FAIL'
        
        # ========== 测试 8: 页面样式和布局 ==========
        print("\n" + "="*60)
        print("测试 8: 页面样式和布局")
        print("="*60)
        
        try:
            # 检查整体布局
            assembly_page = page.locator('.assembly-page')
            header = page.locator('.assembly-header, header')
            
            print(f"   主容器: {'存在' if assembly_page.count() > 0 else '不存在'}")
            print(f"   头部区域: {'存在' if header.count() > 0 else '不存在'}")
            
            # 检查响应式
            page.set_viewport_size({"width": 1024, "height": 768})
            time.sleep(1)
            page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_adv_08_responsive.png', full_page=True)
            
            # 恢复视口
            page.set_viewport_size({"width": 1920, "height": 1080})
            
            results['test_8'] = 'PASS'
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_8'] = 'FAIL'
        
        # ========== 汇总 ==========
        print("\n" + "="*60)
        print("高级测试汇总")
        print("="*60)
        
        for name, result in results.items():
            icon = '✅' if result == 'PASS' else '⚠️' if result in ['WARN', 'SKIP'] else '❌'
            print(f"  {icon} {name}: {result}")
        
        if errors:
            print(f"\n页面错误 ({len(errors)}):")
            for e in errors[:3]:
                print(f"  ❌ {e[:100]}")
        
        error_logs = [l for l in console_logs if '[error]' in l.lower()]
        if error_logs:
            print(f"\n控制台错误 ({len(error_logs)}):")
            for l in error_logs[:3]:
                print(f"  ❌ {l[:100]}")
        
        browser.close()
        
        passed = sum(1 for r in results.values() if r == 'PASS')
        skipped = sum(1 for r in results.values() if r == 'SKIP')
        total = len(results)
        print(f"\n通过: {passed}/{total}, 跳过: {skipped}")
        print(f"通过率: {100*(passed+skipped)/total:.0f}%")
        print(f"截图: {SCREENSHOT_DIR}/assembly_adv_*.png")
        
        return passed >= 5

if __name__ == '__main__':
    success = test_assembly_advanced()
    exit(0 if success else 1)
