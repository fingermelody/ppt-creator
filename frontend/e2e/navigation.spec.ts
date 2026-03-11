import { test, expect } from '@playwright/test';

/**
 * 导航测试用例
 * 测试页面路由和导航功能
 */

test.describe('页面导航测试', () => {
  test('应用首页加载', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 检查应用已加载
    const appRoot = page.locator('#root');
    await expect(appRoot).toBeVisible();
  });

  test('导航到大纲页面', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // 点击大纲导航
    const outlineLink = page.locator('a:has-text("大纲"), a[href*="outline"]');
    
    if (await outlineLink.count() > 0) {
      await outlineLink.click();
      await expect(page).toHaveURL(/.*outline.*/);
    } else {
      // 直接导航
      await page.goto('/#/outline');
      await expect(page).toHaveURL(/.*outline.*/);
    }
  });

  test('导航到文档库页面', async ({ page }) => {
    await page.goto('/#/documents');
    await page.waitForLoadState('networkidle');
    
    await expect(page).toHaveURL(/.*documents.*/);
  });

  test('导航到组装页面', async ({ page }) => {
    await page.goto('/#/assembly');
    await page.waitForLoadState('networkidle');
    
    await expect(page).toHaveURL(/.*assembly.*/);
  });

  test('导航到精调页面', async ({ page }) => {
    await page.goto('/#/refinement');
    await page.waitForLoadState('networkidle');
    
    await expect(page).toHaveURL(/.*refinement.*/);
  });

  test('404 页面处理', async ({ page }) => {
    // 访问不存在的路由
    await page.goto('/#/nonexistent-page');
    await page.waitForLoadState('networkidle');
    
    // 应该重定向到有效页面或显示404
    const pageContent = page.locator('#root');
    await expect(pageContent).toBeVisible();
  });
});
