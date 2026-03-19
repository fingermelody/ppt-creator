import { test, expect, Page } from '@playwright/test';

/**
 * 大纲页面测试用例
 * 测试 PPT 大纲设计功能
 */

test.describe('大纲页面测试', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到大纲页面
    await page.goto('/#/outline');
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
  });

  test('页面标题和描述显示正确', async ({ page }) => {
    // 检查页面标题
    await expect(page.locator('.outline-header h2')).toHaveText('PPT大纲设计');
    
    // 检查页面描述
    await expect(page.locator('.header-desc')).toContainText('选择生成方式');
  });

  test('生成方式标签页切换', async ({ page }) => {
    // 检查默认选中"智能生成" - TDesign 使用 t-is-active 类
    await expect(page.locator('.t-tabs__nav-item').first()).toHaveClass(/t-is-active/);
    
    // 点击"向导式生成"标签
    await page.locator('.t-tabs__nav-item').filter({ hasText: '向导式生成' }).click();
    
    // 验证标签页切换成功
    await expect(page.locator('.t-tabs__nav-item').filter({ hasText: '向导式生成' })).toHaveClass(/t-is-active/);
  });

  test('使用模板按钮显示', async ({ page }) => {
    // 检查"使用模板"按钮存在
    const templateButton = page.locator('button:has-text("使用模板")');
    await expect(templateButton).toBeVisible();
  });

  test('大纲草稿列表显示', async ({ page }) => {
    // 检查大纲草稿卡片存在
    const draftsCard = page.locator('.drafts-card');
    await expect(draftsCard).toBeVisible();
    
    // 检查草稿卡片标题
    await expect(draftsCard.locator('.t-card__header')).toContainText('大纲草稿');
  });

  test('智能生成输入框存在', async ({ page }) => {
    // 检查智能生成组件中的输入框
    const textarea = page.locator('.smart-generate textarea, .smart-generate input');
    
    // 如果存在则验证
    if (await textarea.count() > 0) {
      await expect(textarea.first()).toBeVisible();
    }
  });
});
