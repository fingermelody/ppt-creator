import { test, expect, Page } from '@playwright/test';

/**
 * 文档库页面测试用例
 * 测试文档上传、预览、下载等功能
 */

test.describe('文档库页面测试', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到文档库页面
    await page.goto('/#/library');
    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
  });

  test('页面标题显示正确', async ({ page }) => {
    // 检查页面标题
    await expect(page.locator('.page-title')).toHaveText('文档库');
  });

  test('上传PPT按钮存在', async ({ page }) => {
    // 检查上传按钮
    const uploadButton = page.locator('button:has-text("上传PPT")');
    await expect(uploadButton).toBeVisible();
  });

  test('开始组装PPT按钮存在', async ({ page }) => {
    // 检查组装按钮
    const assemblyButton = page.locator('button:has-text("开始组装PPT")');
    await expect(assemblyButton).toBeVisible();
  });

  test('文档表格显示', async ({ page }) => {
    // 等待表格加载
    await page.waitForSelector('.document-table-container, .t-empty', { timeout: 10000 });
    
    // 检查是否有文档或显示空状态
    const tableContainer = page.locator('.document-table-container');
    const emptyState = page.locator('.t-empty');
    
    // 至少应该有表格或空状态其中一个
    const hasTable = await tableContainer.count() > 0;
    const hasEmpty = await emptyState.count() > 0;
    
    expect(hasTable || hasEmpty).toBeTruthy();
  });

  test('表格列标题正确', async ({ page }) => {
    // 等待表格加载
    const tableExists = await page.locator('.t-table').count() > 0;
    
    if (tableExists) {
      // 检查表格列标题
      const expectedHeaders = ['文档名称', '页数', '大小', '状态', '上传时间', '操作'];
      
      for (const header of expectedHeaders) {
        await expect(page.locator(`.t-table th:has-text("${header}")`)).toBeVisible();
      }
    }
  });

  test('上传功能点击', async ({ page }) => {
    // 点击上传按钮
    const uploadButton = page.locator('button:has-text("上传PPT")');
    await uploadButton.click();
    
    // 应该触发文件选择器（通过 input[type="file"]）
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeAttached();
  });

  test('空状态显示', async ({ page }) => {
    // 如果没有文档，检查空状态
    const emptyState = page.locator('.t-empty');
    
    if (await emptyState.count() > 0) {
      await expect(emptyState).toContainText('暂无文档');
    }
  });
});
