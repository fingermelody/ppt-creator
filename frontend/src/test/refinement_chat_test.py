"""
PPT 精修 - 对话功能专项测试
"""

import time
import requests
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:3000"
API_BASE_URL = "http://localhost:8000"

def get_task_id():
    """获取一个真实的精修任务 ID"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/refinement/tasks")
        data = response.json()
        if data.get("tasks") and len(data["tasks"]) > 0:
            return data["tasks"][0]["id"]
    except:
        pass
    return None

def test_chat_functionality():
    """测试对话功能"""
    task_id = get_task_id()
    if not task_id:
        print("❌ 没有可用的任务")
        return False
    
    print(f"📌 使用任务 ID: {task_id}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 捕获网络请求
        requests_made = []
        responses_received = []
        
        def handle_request(request):
            if "/api/refinement" in request.url:
                requests_made.append({
                    "method": request.method,
                    "url": request.url
                })
        
        def handle_response(response):
            if "/api/refinement" in response.url:
                responses_received.append({
                    "url": response.url,
                    "status": response.status
                })
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # 访问任务详情页
        print("\n1️⃣ 访问任务详情页...")
        page.goto(f"{BASE_URL}/#/refinement/{task_id}")
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # 查找对话输入框
        print("2️⃣ 查找对话输入框...")
        textarea = page.locator(".chat-input textarea, .t-textarea__inner, textarea")
        
        if textarea.count() == 0:
            print("❌ 找不到对话输入框")
            browser.close()
            return False
        
        print(f"   ✅ 找到 {textarea.count()} 个输入框")
        
        # 输入测试消息
        print("3️⃣ 输入测试消息...")
        test_message = "请帮我修改这个页面的标题为测试标题"
        textarea.first.fill(test_message)
        time.sleep(0.5)
        
        # 查找发送按钮
        print("4️⃣ 查找发送按钮...")
        send_btn = page.locator("button:has-text('发送'), .send-button, .chat-input button")
        
        if send_btn.count() == 0:
            print("❌ 找不到发送按钮")
            browser.close()
            return False
        
        print(f"   ✅ 找到 {send_btn.count()} 个发送按钮")
        
        # 点击发送
        print("5️⃣ 点击发送按钮...")
        send_btn.first.click()
        
        # 等待响应
        print("6️⃣ 等待服务器响应...")
        time.sleep(3)
        
        # 检查消息是否显示
        print("7️⃣ 检查消息显示...")
        messages = page.locator(".message, .chat-message, .message-item")
        print(f"   消息数量: {messages.count()}")
        
        # 检查 API 请求
        print("\n📊 API 请求统计:")
        print(f"   发送的请求数: {len(requests_made)}")
        print(f"   收到的响应数: {len(responses_received)}")
        
        chat_requests = [r for r in requests_made if "chat" in r["url"].lower() or "message" in r["url"].lower()]
        print(f"   对话相关请求: {len(chat_requests)}")
        
        if chat_requests:
            for r in chat_requests:
                print(f"      - {r['method']} {r['url']}")
        
        # 检查响应状态
        error_responses = [r for r in responses_received if r["status"] >= 400]
        if error_responses:
            print("\n⚠️ 错误响应:")
            for r in error_responses:
                print(f"   - {r['status']}: {r['url']}")
        
        # 截图
        page.screenshot(path="/tmp/refinement_chat_test.png", full_page=True)
        print(f"\n📸 截图已保存: /tmp/refinement_chat_test.png")
        
        browser.close()
        
        # 总结
        print("\n" + "="*50)
        print("测试结果:")
        if error_responses:
            print("❌ 存在 API 错误响应")
            return False
        else:
            print("✅ 对话功能测试通过")
            return True

if __name__ == "__main__":
    result = test_chat_functionality()
    exit(0 if result else 1)
