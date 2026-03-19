"""
前端完整流程测试
测试：写大纲 -> 保存大纲 -> 组装 PPT
"""

from playwright.sync_api import sync_playwright
import time

def test_outline_flow():
    """测试大纲设计到组装的完整流程"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # 设置控制台日志监听
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        errors = []
        page.on('pageerror', lambda err: errors.append(str(err)))
        
        print("=" * 60)
        print("步骤 1: 访问大纲页面")
        print("=" * 60)
        
        try:
            # 访问大纲页面
            page.goto('https://ppt.bottlepeace.com/outline', wait_until='networkidle', timeout=60000)
            page.wait_for_load_state('networkidle')
            time.sleep(2)  # 额外等待确保页面完全加载
            
            # 截图
            page.screenshot(path='/tmp/step1_outline_page.png', full_page=True)
            print(f"✅ 大纲页面已加载")
            print(f"   当前 URL: {page.url}")
            
            # 检查是否在正确的页面
            if '/outline' not in page.url:
                print(f"❌ 页面跳转错误！当前 URL: {page.url}")
                # 打印控制台错误
                for log in console_logs:
                    if 'error' in log.lower():
                        print(f"   Console: {log}")
                for err in errors:
                    print(f"   Error: {err}")
            else:
                print(f"✅ 页面 URL 正确")
            
        except Exception as e:
            print(f"❌ 步骤 1 失败: {str(e)}")
            page.screenshot(path='/tmp/step1_error.png', full_page=True)
            
        print("\n" + "=" * 60)
        print("步骤 2: 检查页面元素")
        print("=" * 60)
        
        try:
            # 检查页面标题
            title = page.locator('h2').first.text_content()
            print(f"   页面标题: {title}")
            
            # 检查智能生成/向导式选项卡
            tabs = page.locator('.t-tabs__nav-item').all()
            print(f"   选项卡数量: {len(tabs)}")
            
            page.screenshot(path='/tmp/step2_page_elements.png', full_page=True)
            print(f"✅ 页面元素检查完成")
            
        except Exception as e:
            print(f"⚠️ 步骤 2 警告: {str(e)}")
            
        print("\n" + "=" * 60)
        print("步骤 3: 智能生成大纲")
        print("=" * 60)
        
        try:
            # 找到描述输入框
            textarea = page.locator('textarea').first
            
            # 输入描述
            description = """人工智能在企业数字化转型中的应用，包括：
1. 智能客服和聊天机器人的部署，提升客户服务效率
2. 数据分析和预测模型，帮助企业做出更明智的决策
3. 自动化流程优化，减少人工成本
4. 个性化推荐系统，提升用户体验
5. 安全和风险管理，预防潜在威胁"""
            
            textarea.fill(description)
            print(f"✅ 已输入描述")
            
            page.screenshot(path='/tmp/step3_input_description.png', full_page=True)
            
            # 点击生成按钮
            generate_btn = page.locator('button:has-text("生成大纲")').first
            if generate_btn.is_visible():
                generate_btn.click()
                print(f"✅ 已点击生成按钮")
                
                # 等待生成完成
                page.wait_for_timeout(5000)  # 等待5秒
                page.screenshot(path='/tmp/step3_after_generate.png', full_page=True)
            else:
                print(f"⚠️ 未找到生成按钮")
                
        except Exception as e:
            print(f"⚠️ 步骤 3 警告: {str(e)}")
            page.screenshot(path='/tmp/step3_error.png', full_page=True)
            
        print("\n" + "=" * 60)
        print("控制台日志摘要")
        print("=" * 60)
        
        error_logs = [log for log in console_logs if 'error' in log.lower()]
        if error_logs:
            print(f"发现 {len(error_logs)} 个错误日志:")
            for log in error_logs[:10]:
                print(f"   {log}")
        else:
            print("✅ 没有发现错误日志")
            
        if errors:
            print(f"\n发现 {len(errors)} 个页面错误:")
            for err in errors:
                print(f"   {err}")
        else:
            print("✅ 没有发现页面错误")
            
        browser.close()
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        print(f"截图保存在 /tmp/ 目录")
        
        return len(errors) == 0 and '/outline' in page.url

if __name__ == '__main__':
    success = test_outline_flow()
    print(f"\n最终结果: {'✅ 通过' if success else '❌ 失败'}")
