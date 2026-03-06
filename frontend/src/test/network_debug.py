"""检查精修页面的网络请求"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    
    # 捕获网络请求
    responses = []
    def capture_response(response):
        if '/api/' in response.url:
            try:
                body = response.text() if response.status < 300 else None
            except:
                body = None
            responses.append({
                'url': response.url,
                'status': response.status,
                'body': body[:200] if body else None
            })
    
    page.on('response', capture_response)
    
    # 捕获控制台
    errors = []
    page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
    
    # 访问精修页面
    page.goto('http://localhost:3000/#/refinement')
    page.wait_for_load_state('networkidle')
    time.sleep(3)
    
    print('API 请求:')
    for r in responses:
        status_icon = '✅' if r['status'] < 400 else '❌'
        print(f"  {status_icon} {r['status']} - {r['url']}")
        if r['body']:
            print(f"      响应: {r['body'][:100]}")
    
    print('\n控制台错误:')
    for e in errors[:5]:
        print(f"  ❌ {e[:200]}")
    
    browser.close()
