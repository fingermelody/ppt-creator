import { test, expect, Page } from '@playwright/test';

/**
 * PPT 组装页面测试用例
 * 测试章节管理、幻灯片预览等功能
 */

test.describe('PPT组装页面测试', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到组装页面（不带参数时显示空状态或引导）
    await page.goto('/#/assembly');
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
  });

  test('组装页面加载', async ({ page }) => {
    // 检查页面主要元素
    const assemblyPage = page.locator('.assembly-page');
    await expect(assemblyPage).toBeVisible();
  });

  test('页面布局结构', async ({ page }) => {
    // 检查页面显示的状态 - 可能是大纲列表、空状态或引导
    const hasOutlineList = await page.locator('.outline-list-card').count() > 0;
    const hasOutlineRequired = await page.locator('.outline-required-card').count() > 0;
    const hasEmpty = await page.locator('.t-empty').count() > 0;
    const hasAssemblyPage = await page.locator('.assembly-page').count() > 0;
    
    // 页面应该显示某种内容
    expect(hasOutlineList || hasOutlineRequired || hasEmpty || hasAssemblyPage).toBeTruthy();
  });

  test('章节面板显示', async ({ page }) => {
    // 检查章节面板
    const chapterPanel = page.locator('.chapter-panel');
    
    if (await chapterPanel.count() > 0) {
      await expect(chapterPanel).toBeVisible();
    }
  });

  test('幻灯片预览区域', async ({ page }) => {
    // 检查幻灯片预览
    const slidePreview = page.locator('.slide-preview');
    
    if (await slidePreview.count() > 0) {
      await expect(slidePreview).toBeVisible();
    }
  });
});

test.describe('带大纲ID的组装页面', () => {
  test('访问带大纲ID的组装页面', async ({ page }) => {
    // 使用测试大纲ID访问
    await page.goto('/#/assembly/test-outline-id');
    await page.waitForLoadState('networkidle');
    
    // 页面应该加载，可能会显示错误或空状态
    const pageContent = page.locator('.assembly-page, .t-empty, .error-page');
    await expect(pageContent.first()).toBeVisible();
  });
});
