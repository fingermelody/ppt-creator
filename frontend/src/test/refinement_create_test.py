"""测试创建精修任务功能"""
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    
    # 捕获网络请求
    responses = []
    def capture_response(response):
        if '/api/' in response.url:
            responses.append({
                'url': response.url,
                'status': response.status,
                'method': response.request.method
            })
    
    page.on('response', capture_response)
    
    # 捕获控制台
    errors = []
    page.on('console', lambda msg: errors.append(msg.text) if msg.type == 'error' else None)
    
    # 访问精修页面
    page.goto('http://localhost:3000/#/refinement')
    page.wait_for_load_state('networkidle')
    time.sleep(2)
    
    # 点击从草稿创建标签
    tab = page.get_by_text('从草稿创建')
    if tab.count() > 0:
        tab.first.click()
        time.sleep(2)
        page.wait_for_load_state('networkidle')
    
    # 点击第一个创建精修任务按钮
    create_btn = page.get_by_text('创建精修任务')
    if create_btn.count() > 0:
        print(f'点击创建精修任务按钮...')
        create_btn.first.click()
        time.sleep(3)
        page.wait_for_load_state('networkidle')
        
        # 检查是否跳转到精修详情页
        current_url = page.url
        print(f'当前URL: {current_url}')
        
        # 截图
        page.screenshot(path='/tmp/refinement_after_create.png', full_page=True)
        print('创建后截图已保存')
        
        # 检查是否有错误
        if '/refinement/' in current_url and 'refinement' in current_url:
            print('✅ 成功跳转到精修详情页')
        else:
            print('⚠️ 可能没有成功跳转')
    else:
        print('❌ 没有找到创建按钮')
    
    print('\nAPI 请求:')
    for r in responses:
        status_icon = '✅' if r['status'] < 400 else '❌'
        print(f"  {status_icon} {r['method']} {r['status']} - {r['url']}")
    
    print('\n控制台错误:')
    for e in errors[:5]:
        print(f"  ❌ {e[:200]}")
    
    browser.close()
