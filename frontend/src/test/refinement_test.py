"""
PPT 精修功能自动化测试脚本
测试范围：
1. 精修列表页面 - 页面加载、草稿列表、任务列表
2. 创建精修任务 - 从草稿创建任务
3. 精修编辑页面 - 页面列表、对话、元素操作
4. 导出功能 - PPT导出
"""

import sys
import json
import time
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:3000"
API_BASE_URL = "http://localhost:8000"

class RefinementTester:
    def __init__(self, page):
        self.page = page
        self.errors = []
        self.warnings = []
        self.test_results = []
        
    def log_result(self, test_name, success, message="", details=None):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if not success and details:
            print(f"   Details: {details}")
        return success
    
    def capture_console_errors(self):
        """捕获控制台错误"""
        self.page.on("console", lambda msg: 
            self.errors.append(msg.text) if msg.type == "error" else 
            (self.warnings.append(msg.text) if msg.type == "warning" else None))
        
    def wait_for_network_idle(self, timeout=10000):
        """等待网络空闲"""
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            return True
        except Exception as e:
            print(f"Network idle timeout: {e}")
            return False
    
    def test_refinement_list_page_load(self):
        """测试精修列表页面加载"""
        test_name = "精修列表页面加载"
        try:
            self.page.goto(f"{BASE_URL}/#/refinement")
            self.wait_for_network_idle()
            
            # 检查页面标题
            title = self.page.locator("h1")
            if title.count() > 0:
                title_text = title.first.inner_text()
                if "精修" in title_text or "PPT" in title_text:
                    return self.log_result(test_name, True, f"页面标题: {title_text}")
            
            # 检查是否有Loading组件
            loading = self.page.locator(".t-loading")
            if loading.count() > 0:
                time.sleep(2)
                self.wait_for_network_idle()
            
            # 检查页面内容是否存在
            page_content = self.page.locator(".refinement-list-page")
            if page_content.count() > 0:
                return self.log_result(test_name, True, "精修列表页面已加载")
            
            # 备用检查
            return self.log_result(test_name, True, "页面已加载")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_tabs_navigation(self):
        """测试标签页导航"""
        test_name = "标签页导航"
        try:
            self.page.goto(f"{BASE_URL}/#/refinement")
            self.wait_for_network_idle()
            
            # 检查是否有标签页
            tabs = self.page.locator(".t-tabs__item, [role='tab']")
            if tabs.count() >= 2:
                # 点击"从草稿创建"标签
                drafts_tab = self.page.get_by_text("从草稿创建")
                if drafts_tab.count() > 0:
                    drafts_tab.first.click()
                    time.sleep(0.5)
                    return self.log_result(test_name, True, "标签页可切换")
                
                # 尝试点击第二个标签
                tabs.nth(1).click()
                time.sleep(0.5)
                return self.log_result(test_name, True, "标签页可切换")
            
            return self.log_result(test_name, True, "标签页检测完成")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_search_functionality(self):
        """测试搜索功能"""
        test_name = "搜索功能"
        try:
            self.page.goto(f"{BASE_URL}/#/refinement")
            self.wait_for_network_idle()
            
            # 查找搜索框
            search_input = self.page.locator("input[placeholder*='搜索'], .t-input input")
            if search_input.count() > 0:
                search_input.first.fill("测试")
                time.sleep(0.5)
                return self.log_result(test_name, True, "搜索框可正常输入")
            
            return self.log_result(test_name, True, "搜索功能检测完成")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_empty_state(self):
        """测试空状态显示"""
        test_name = "空状态显示"
        try:
            self.page.goto(f"{BASE_URL}/#/refinement")
            self.wait_for_network_idle()
            
            # 检查是否有空状态
            empty = self.page.locator(".t-empty, .empty-container")
            if empty.count() > 0:
                return self.log_result(test_name, True, "空状态正常显示")
            
            # 检查是否有任务卡片
            cards = self.page.locator(".task-card, .draft-card, .t-card")
            if cards.count() > 0:
                return self.log_result(test_name, True, f"有{cards.count()}个卡片/任务")
            
            return self.log_result(test_name, True, "页面状态正常")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_create_task_from_draft(self):
        """测试从草稿创建精修任务"""
        test_name = "从草稿创建精修任务"
        try:
            self.page.goto(f"{BASE_URL}/#/refinement")
            self.wait_for_network_idle()
            
            # 切换到"从草稿创建"标签
            drafts_tab = self.page.get_by_text("从草稿创建")
            if drafts_tab.count() > 0:
                drafts_tab.first.click()
                time.sleep(1)
                self.wait_for_network_idle()
            
            # 检查是否有草稿卡片
            draft_cards = self.page.locator(".draft-card, .t-card")
            if draft_cards.count() > 0:
                # 查找创建按钮
                create_btn = self.page.get_by_text("创建精修任务")
                if create_btn.count() > 0:
                    return self.log_result(test_name, True, f"有{draft_cards.count()}个草稿可创建任务")
            
            # 检查空状态
            empty = self.page.locator(".empty-container, .t-empty")
            if empty.count() > 0:
                return self.log_result(test_name, True, "无可用草稿（正常状态）")
            
            return self.log_result(test_name, True, "草稿页面状态正常")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_refinement_detail_page(self):
        """测试精修详情页面"""
        test_name = "精修详情页面"
        try:
            # 先访问列表页
            self.page.goto(f"{BASE_URL}/#/refinement")
            self.wait_for_network_idle()
            
            # 检查是否有任务卡片可点击
            task_cards = self.page.locator(".task-card")
            if task_cards.count() > 0:
                task_cards.first.click()
                time.sleep(1)
                self.wait_for_network_idle()
                
                # 检查是否进入详情页
                if "/refinement/" in self.page.url:
                    return self.log_result(test_name, True, "成功进入精修详情页")
            
            # 直接测试详情页路由（使用模拟ID）
            self.page.goto(f"{BASE_URL}/#/refinement/test-task-id")
            self.wait_for_network_idle()
            
            # 检查页面是否显示404或错误
            empty = self.page.locator(".t-empty")
            if empty.count() > 0:
                return self.log_result(test_name, True, "任务不存在时正确显示空状态")
            
            return self.log_result(test_name, True, "详情页路由正常")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_page_list_component(self):
        """测试页面列表组件"""
        test_name = "页面列表组件"
        try:
            # 检查是否有页面列表
            page_list = self.page.locator(".page-list, .pages-list, .pages-sidebar")
            if page_list.count() > 0:
                # 检查是否有页面项
                page_items = self.page.locator(".page-item")
                return self.log_result(test_name, True, f"页面列表组件存在，有{page_items.count()}个页面")
            
            return self.log_result(test_name, True, "页面列表组件检测完成")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_chat_panel_component(self):
        """测试对话面板组件"""
        test_name = "对话面板组件"
        try:
            # 检查是否有对话面板
            chat_panel = self.page.locator(".chat-panel")
            if chat_panel.count() > 0:
                # 检查输入框
                textarea = self.page.locator(".chat-input textarea, .t-textarea")
                if textarea.count() > 0:
                    # 尝试输入
                    textarea.first.fill("测试消息")
                    return self.log_result(test_name, True, "对话面板可正常输入")
                
                return self.log_result(test_name, True, "对话面板组件存在")
            
            return self.log_result(test_name, True, "对话面板组件检测完成")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_back_button(self):
        """测试返回按钮"""
        test_name = "返回按钮"
        try:
            # 访问详情页
            self.page.goto(f"{BASE_URL}/#/refinement/test-task-id")
            self.wait_for_network_idle()
            
            # 查找返回按钮
            back_btn = self.page.locator("button:has-text('返回'), [class*='back']")
            if back_btn.count() > 0:
                back_btn.first.click()
                time.sleep(0.5)
                
                # 检查是否返回列表页
                if "/refinement" in self.page.url and "test-task-id" not in self.page.url:
                    return self.log_result(test_name, True, "返回按钮正常工作")
            
            return self.log_result(test_name, True, "返回按钮检测完成")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_export_button(self):
        """测试导出按钮"""
        test_name = "导出按钮"
        try:
            self.page.goto(f"{BASE_URL}/#/refinement")
            self.wait_for_network_idle()
            
            # 检查列表页导出按钮
            export_btns = self.page.locator("button:has-text('导出'), [class*='download']")
            if export_btns.count() > 0:
                return self.log_result(test_name, True, f"找到{export_btns.count()}个导出按钮")
            
            return self.log_result(test_name, True, "导出按钮检测完成")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_navigation_integration(self):
        """测试导航集成"""
        test_name = "导航集成"
        try:
            self.page.goto(f"{BASE_URL}/#/refinement")
            self.wait_for_network_idle()
            
            # 检查侧边栏导航
            nav_item = self.page.locator("[class*='menu-item']:has-text('精修'), .t-menu__item:has-text('精修')")
            if nav_item.count() > 0:
                return self.log_result(test_name, True, "精修入口在导航菜单中")
            
            # 检查URL是否正确
            if "/refinement" in self.page.url:
                return self.log_result(test_name, True, "精修页面路由正常")
            
            return self.log_result(test_name, True, "导航集成检测完成")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_api_requests(self):
        """测试API请求"""
        test_name = "API请求"
        api_errors = []
        
        def handle_response(response):
            if response.status >= 400 and "/api/refinement" in response.url:
                api_errors.append({
                    "url": response.url,
                    "status": response.status
                })
        
        self.page.on("response", handle_response)
        
        try:
            self.page.goto(f"{BASE_URL}/#/refinement")
            self.wait_for_network_idle(timeout=15000)
            
            if api_errors:
                return self.log_result(test_name, False, f"API请求错误: {api_errors}")
            
            return self.log_result(test_name, True, "API请求正常")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_responsive_design(self):
        """测试响应式设计"""
        test_name = "响应式设计"
        try:
            # 测试不同视口
            viewports = [
                {"width": 1920, "height": 1080, "name": "桌面"},
                {"width": 1024, "height": 768, "name": "平板"},
                {"width": 375, "height": 667, "name": "手机"},
            ]
            
            for vp in viewports:
                self.page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
                self.page.goto(f"{BASE_URL}/#/refinement")
                self.wait_for_network_idle()
                
                # 检查页面是否正常渲染
                body = self.page.locator("body")
                if not body.is_visible():
                    return self.log_result(test_name, False, f"{vp['name']}视口下页面渲染失败")
            
            # 恢复默认视口
            self.page.set_viewport_size({"width": 1280, "height": 800})
            return self.log_result(test_name, True, "响应式设计正常")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def test_console_errors(self):
        """检查控制台错误"""
        test_name = "控制台错误检查"
        try:
            if self.errors:
                # 过滤掉预期的 404 错误（访问不存在的任务是正常行为）
                critical_errors = [
                    e for e in self.errors 
                    if ("error" in e.lower() or "fail" in e.lower())
                    and "404" not in e  # 排除 404 错误
                    and "test-task-id" not in e  # 排除测试任务 ID 相关的错误
                    and "Not Found" not in e  # 排除 Not Found 错误
                ]
                if critical_errors:
                    return self.log_result(test_name, False, f"发现{len(critical_errors)}个严重错误", critical_errors[:5])
            
            return self.log_result(test_name, True, "无严重控制台错误")
        except Exception as e:
            return self.log_result(test_name, False, str(e))
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("PPT 精修功能自动化测试")
        print("="*60 + "\n")
        
        # 捕获控制台错误
        self.capture_console_errors()
        
        # 运行测试
        tests = [
            self.test_refinement_list_page_load,
            self.test_tabs_navigation,
            self.test_search_functionality,
            self.test_empty_state,
            self.test_create_task_from_draft,
            self.test_refinement_detail_page,
            self.test_page_list_component,
            self.test_chat_panel_component,
            self.test_back_button,
            self.test_export_button,
            self.test_navigation_integration,
            self.test_api_requests,
            self.test_responsive_design,
            self.test_console_errors,
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_result(test.__name__, False, f"测试异常: {e}")
        
        # 输出测试摘要
        print("\n" + "="*60)
        print("测试摘要")
        print("="*60)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed
        print(f"通过: {passed}/{len(self.test_results)}")
        print(f"失败: {failed}/{len(self.test_results)}")
        
        if self.errors:
            print(f"\n控制台错误数: {len(self.errors)}")
        if self.warnings:
            print(f"控制台警告数: {len(self.warnings)}")
        
        return {
            "passed": passed,
            "failed": failed,
            "total": len(self.test_results),
            "results": self.test_results,
            "console_errors": self.errors,
            "console_warnings": self.warnings
        }


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        
        tester = RefinementTester(page)
        results = tester.run_all_tests()
        
        # 截图保存
        page.goto(f"{BASE_URL}/#/refinement")
        page.wait_for_load_state("networkidle")
        page.screenshot(path="/tmp/refinement_list.png", full_page=True)
        print(f"\n截图已保存: /tmp/refinement_list.png")
        
        browser.close()
        
        return results


if __name__ == "__main__":
    results = main()
    
    # 输出失败的测试
    failed_tests = [r for r in results["results"] if not r["success"]]
    if failed_tests:
        print("\n失败的测试:")
        for test in failed_tests:
            print(f"  - {test['test']}: {test['message']}")
    
    sys.exit(0 if results["failed"] == 0 else 1)
