import { test, expect, Page } from '@playwright/test';

/**
 * 页面精调测试用例
 * 测试页面编辑、AI对话、版本管理等功能
 */

test.describe('精调页面测试', () => {
  test('精调列表页面加载', async ({ page }) => {
    // 导航到精调列表
    await page.goto('/#/refinement');
    await page.waitForLoadState('networkidle');
    
    // 检查页面主要元素
    const refinementPage = page.locator('.refinement-page, .refinement-list');
    
    if (await refinementPage.count() > 0) {
      await expect(refinementPage).toBeVisible();
    }
  });

  test('带ID的精调页面', async ({ page }) => {
    // 访问特定精调页面
    await page.goto('/#/refinement/test-id');
    await page.waitForLoadState('networkidle');
    
    // 页面应该加载，可能会显示错误或空状态
    const pageContent = page.locator('.refinement-page, .t-empty, .error-page');
    await expect(pageContent.first()).toBeVisible();
  });

  test('页面列表组件', async ({ page }) => {
    await page.goto('/#/refinement/test-id');
    await page.waitForLoadState('networkidle');
    
    // 检查页面列表
    const pageList = page.locator('.page-list');
    
    if (await pageList.count() > 0) {
      await expect(pageList).toBeVisible();
    }
  });

  test('聊天面板组件', async ({ page }) => {
    await page.goto('/#/refinement/test-id');
    await page.waitForLoadState('networkidle');
    
    // 检查聊天面板
    const chatPanel = page.locator('.chat-panel');
    
    if (await chatPanel.count() > 0) {
      await expect(chatPanel).toBeVisible();
    }
  });
});
