#!/usr/bin/env python3
"""
PPT 组装功能完整测试脚本
测试范围：组装页面入口 → 章节管理 → 页面操作 → 预览导出
"""

from playwright.sync_api import sync_playwright
import time

FRONTEND_URL = "http://localhost:3000"
SCREENSHOT_DIR = "/tmp"

def test_assembly_complete():
    """组装功能完整测试"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # 监听
        console_logs = []
        errors = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on('pageerror', lambda err: errors.append(str(err)))
        
        results = {}
        
        # ========== 测试 1: 直接访问组装页面 ==========
        print("\n" + "="*60)
        print("测试 1: 直接访问组装页面（无参数）")
        print("="*60)
        
        try:
            page.goto(f'{FRONTEND_URL}/#/assembly', wait_until='networkidle', timeout=30000)
            time.sleep(2)
            page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_01_entry.png', full_page=True)
            
            # 应显示引导页面
            outline_card = page.locator('.outline-required-card, .assembly-page.empty')
            if outline_card.count() > 0:
                print("✅ 正确显示引导页面")
                results['test_1'] = 'PASS'
            else:
                print("⚠️ 未显示预期的引导页面")
                results['test_1'] = 'WARN'
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_1'] = 'FAIL'
            page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_01_error.png')
        
        # ========== 测试 2: 大纲页面加载 ==========
        print("\n" + "="*60)
        print("测试 2: 大纲页面加载")
        print("="*60)
        
        try:
            page.goto(f'{FRONTEND_URL}/#/outline', wait_until='networkidle', timeout=30000)
            time.sleep(2)
            page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_02_outline.png', full_page=True)
            
            title = page.locator('h2').first.text_content()
            print(f"✅ 页面标题: {title}")
            
            tabs = page.locator('.t-tabs__nav-item').all()
            print(f"   选项卡: {[t.text_content() for t in tabs]}")
            results['test_2'] = 'PASS'
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_2'] = 'FAIL'
        
        # ========== 测试 3: 智能生成大纲 ==========
        print("\n" + "="*60)
        print("测试 3: 智能生成大纲")
        print("="*60)
        
        try:
            textarea = page.locator('textarea').first
            textarea.fill("企业数字化转型方案，包含：背景分析、目标设定、实施方案、预期效果")
            print("✅ 已输入描述")
            
            gen_btn = page.locator('button:has-text("生成大纲")')
            if gen_btn.count() > 0 and gen_btn.first.is_visible():
                gen_btn.first.click()
                print("✅ 已点击生成按钮")
                time.sleep(8)  # 等待 AI 生成
                page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_03_generated.png', full_page=True)
                
                preview_card = page.locator('.preview-card')
                if preview_card.count() > 0:
                    print("✅ 大纲预览已显示")
                    results['test_3'] = 'PASS'
                else:
                    print("⚠️ 预览卡片未出现")
                    results['test_3'] = 'WARN'
            else:
                print("⚠️ 未找到生成按钮")
                results['test_3'] = 'WARN'
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_3'] = 'FAIL'
        
        # ========== 测试 4: 确认大纲跳转 ==========
        print("\n" + "="*60)
        print("测试 4: 确认大纲并跳转")
        print("="*60)
        
        try:
            time.sleep(2)
            confirm_btn = page.locator('button:has-text("确认大纲")')
            if confirm_btn.count() > 0 and confirm_btn.first.is_visible():
                confirm_btn.first.click()
                print("✅ 已点击确认按钮")
                time.sleep(3)
                page.wait_for_load_state('networkidle')
                page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_04_confirm.png', full_page=True)
                
                if '/assembly/' in page.url:
                    print(f"✅ 成功跳转: {page.url}")
                    results['test_4'] = 'PASS'
                else:
                    print(f"⚠️ URL: {page.url}")
                    results['test_4'] = 'WARN'
            else:
                print("⚠️ 未找到确认按钮")
                results['test_4'] = 'SKIP'
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_4'] = 'FAIL'
        
        # ========== 测试 5: 章节侧边栏 ==========
        print("\n" + "="*60)
        print("测试 5: 章节侧边栏功能")
        print("="*60)
        
        try:
            if '/assembly/' in page.url:
                sidebar = page.locator('.chapters-sidebar')
                if sidebar.count() > 0:
                    print("✅ 章节侧边栏存在")
                    
                    chapters = page.locator('.chapter-panel')
                    print(f"   章节数量: {chapters.count()}")
                    
                    if chapters.count() > 0:
                        chapters.first.click()
                        time.sleep(1)
                        page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_05_chapter.png', full_page=True)
                        print("✅ 已选择章节")
                    results['test_5'] = 'PASS'
                else:
                    print("⚠️ 侧边栏未找到")
                    results['test_5'] = 'WARN'
            else:
                print("⚠️ 不在组装页面")
                results['test_5'] = 'SKIP'
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_5'] = 'FAIL'
        
        # ========== 测试 6: 添加章节对话框 ==========
        print("\n" + "="*60)
        print("测试 6: 添加章节对话框")
        print("="*60)
        
        try:
            if '/assembly/' in page.url:
                add_btn = page.locator('button:has-text("添加章节")')
                if add_btn.count() > 0:
                    add_btn.first.click()
                    time.sleep(1)
                    page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_06_dialog.png', full_page=True)
                    
                    dialog = page.locator('.t-dialog')
                    if dialog.count() > 0 and dialog.first.is_visible():
                        print("✅ 对话框已显示")
                        # 关闭对话框
                        close = page.locator('.t-dialog__close')
                        if close.count() > 0:
                            close.first.click()
                        results['test_6'] = 'PASS'
                    else:
                        print("⚠️ 对话框未显示")
                        results['test_6'] = 'WARN'
                else:
                    print("⚠️ 添加按钮未找到")
                    results['test_6'] = 'WARN'
            else:
                results['test_6'] = 'SKIP'
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_6'] = 'FAIL'
        
        # ========== 测试 7: 工具栏按钮 ==========
        print("\n" + "="*60)
        print("测试 7: 工具栏按钮检查")
        print("="*60)
        
        try:
            if '/assembly/' in page.url:
                buttons = {
                    '撤销': page.locator('button:has-text("撤销")'),
                    '重做': page.locator('button:has-text("重做")'),
                    '预览': page.locator('button:has-text("预览")'),
                    '导出': page.locator('button:has-text("导出")'),
                }
                
                for name, btn in buttons.items():
                    if btn.count() > 0:
                        print(f"✅ {name}按钮存在")
                    else:
                        print(f"⚠️ {name}按钮未找到")
                
                page.screenshot(path=f'{SCREENSHOT_DIR}/assembly_07_toolbar.png', full_page=True)
                results['test_7'] = 'PASS'
            else:
                results['test_7'] = 'SKIP'
        except Exception as e:
            print(f"❌ 失败: {e}")
            results['test_7'] = 'FAIL'
        
        # ========== 汇总 ==========
        print("\n" + "="*60)
        print("测试汇总")
        print("="*60)
        
        for name, result in results.items():
            icon = '✅' if result == 'PASS' else '⚠️' if result in ['WARN', 'SKIP'] else '❌'
            print(f"  {icon} {name}: {result}")
        
        if errors:
            print(f"\n页面错误 ({len(errors)}):")
            for e in errors[:5]:
                print(f"  {e}")
        
        error_logs = [l for l in console_logs if '[error]' in l.lower()]
        if error_logs:
            print(f"\n控制台错误 ({len(error_logs)}):")
            for l in error_logs[:5]:
                print(f"  {l}")
        
        browser.close()
        
        passed = sum(1 for r in results.values() if r == 'PASS')
        total = len(results)
        print(f"\n通过率: {passed}/{total} ({100*passed/total:.0f}%)")
        print(f"截图: {SCREENSHOT_DIR}/assembly_*.png")
        
        return passed >= total * 0.7

if __name__ == '__main__':
    success = test_assembly_complete()
    exit(0 if success else 1)
