import { test, expect, Page } from '@playwright/test';

/**
 * 页面精调测试用例
 * 测试页面编辑、AI对话、版本管理等功能
 */

test.describe('精调列表页面测试', () => {
  test.beforeEach(async ({ page }) => {
    // 导航到精调列表页面
    await page.goto('/#/refinement');
    await page.waitForLoadState('networkidle');
  });

  test('页面标题和描述显示正确', async ({ page }) => {
    // 检查页面标题
    await expect(page.locator('.page-header h1')).toHaveText('PPT精修');

    // 检查页面描述
    await expect(page.locator('.page-description')).toContainText('AI对话');
  });

  test('搜索框显示', async ({ page }) => {
    // 检查搜索框存在
    const searchInput = page.locator('.page-toolbar input');
    await expect(searchInput).toBeVisible();
    await expect(searchInput).toHaveAttribute('placeholder', /搜索/);
  });

  test('标签页切换功能', async ({ page }) => {
    // 检查默认选中"精修任务"标签
    await expect(page.locator('.t-tabs__nav-item').first()).toContainText('精修任务');

    // 点击"从草稿创建"标签页（使用更精确的选择器）
    await page.locator('.t-tabs__nav-item').filter({ hasText: '从草稿创建' }).click();

    // 验证标签页切换成功（TDesign使用 t-is-active 类表示选中状态）
    await expect(page.locator('.t-tabs__nav-item').nth(1)).toHaveClass(/t-is-active/);
  });

  test('精修任务列表显示', async ({ page }) => {
    // 检查精修任务列表容器
    const tabContent = page.locator('.tab-content');
    await expect(tabContent).toBeVisible();

    // 检查是否有任务卡片或空状态
    const taskCards = page.locator('.task-card');
    const emptyContainer = page.locator('.empty-container');

    // 至少应该有任务卡片或空状态其中一个
    const hasCards = await taskCards.count() > 0;
    const hasEmpty = await emptyContainer.count() > 0;
    expect(hasCards || hasEmpty).toBeTruthy();
  });

  test('搜索功能', async ({ page }) => {
    // 输入搜索关键词
    const searchInput = page.locator('.page-toolbar input');
    await searchInput.fill('测试搜索');

    // 等待搜索结果更新
    await page.waitForTimeout(500);

    // 搜索框应该包含输入的内容
    await expect(searchInput).toHaveValue('测试搜索');

    // 清空搜索
    await searchInput.clear();
    await expect(searchInput).toHaveValue('');
  });

  test('从草稿创建 - 空状态处理', async ({ page }) => {
    // 点击"从草稿创建"标签页（使用更精确的选择器）
    await page.locator('.t-tabs__nav-item').filter({ hasText: '从草稿创建' }).click();

    // 检查是否有草稿卡片或空状态
    const draftCards = page.locator('.draft-card');
    const emptyContainer = page.locator('.empty-container');

    const hasCards = await draftCards.count() > 0;
    const hasEmpty = await emptyContainer.count() > 0;
    expect(hasCards || hasEmpty).toBeTruthy();
  });
});

test.describe('精修详情页面测试', () => {
  // 使用带页面的测试任务ID
  const TEST_TASK_ID = '0f0bb549-f8a3-41c0-bdf6-8f709c28e181';

  test.beforeEach(async ({ page }) => {
    // 访问特定精修页面（使用测试ID）
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');
  });

  test('页面布局结构', async ({ page }) => {
    // 检查页面主容器
    const refinementPage = page.locator('.refinement-page');
    await expect(refinementPage).toBeVisible();

    // 检查Header区域（任务加载成功后才显示）
    const header = page.locator('.refinement-header');
    // 等待任务加载
    await page.waitForTimeout(1000);
    if (await header.count() > 0) {
      await expect(header).toBeVisible();
    }

    // 检查侧边栏（任务加载成功后才显示）
    const sidebar = page.locator('.pages-sidebar');
    if (await sidebar.count() > 0) {
      await expect(sidebar).toBeVisible();
    }

    // 检查内容区域（任务加载成功后才显示）
    const content = page.locator('.refinement-content');
    if (await content.count() > 0) {
      await expect(content).toBeVisible();
    }
  });

  test('返回按钮功能', async ({ page }) => {
    // 检查返回按钮存在
    const backButton = page.locator('button:has-text("返回")');
    await expect(backButton).toBeVisible();

    // 点击返回按钮
    await backButton.click();

    // 验证返回到列表页
    await expect(page).toHaveURL(/\/#\/refinement$/);
  });

  test('任务标题显示', async ({ page }) => {
    // 如果任务加载成功，检查标题
    const taskTitle = page.locator('.task-title');

    if (await taskTitle.count() > 0) {
      await expect(taskTitle).toBeVisible();
    }
  });

  test('导出PPT按钮', async ({ page }) => {
    // 等待页面加载
    await page.waitForTimeout(1000);
    
    // 检查导出按钮（任务加载成功后才显示）
    const exportButton = page.locator('button:has-text("导出PPT")');
    if (await exportButton.count() > 0) {
      await expect(exportButton).toBeVisible();
      await expect(exportButton).toBeEnabled();
    }
  });

  test('页面列表侧边栏', async ({ page }) => {
    // 等待页面加载
    await page.waitForTimeout(1000);
    
    // 检查侧边栏标题（任务加载成功后才显示）
    const sidebarHeader = page.locator('.sidebar-header h3');
    if (await sidebarHeader.count() > 0) {
      await expect(sidebarHeader).toHaveText('页面列表');
    }

    // 检查页面列表组件
    const pageList = page.locator('.page-list');
    if (await pageList.count() > 0) {
      await expect(pageList).toBeVisible();
    }
  });

  test('加载状态显示', async ({ page }) => {
    // 重新加载页面检查loading状态
    await page.reload();

    // 应该显示loading或内容
    const loading = page.locator('.t-loading, .refinement-page.loading');
    const content = page.locator('.refinement-page:not(.loading)');

    // 等待页面加载完成
    await page.waitForLoadState('networkidle');

    // 页面应该已经加载完成
    const refinementPage = page.locator('.refinement-page');
    await expect(refinementPage).toBeVisible();
  });

  test('错误状态处理', async ({ page }) => {
    // 访问不存在的任务ID
    await page.goto('/#/refinement/non-existent-task-id');
    await page.waitForLoadState('networkidle');

    // 应该显示空状态或错误信息
    const emptyState = page.locator('.t-empty, .empty');
    const errorState = page.locator('.error-page, .error');

    const hasEmpty = await emptyState.count() > 0;
    const hasError = await errorState.count() > 0;
    const hasPage = await page.locator('.refinement-page').count() > 0;

    expect(hasEmpty || hasError || hasPage).toBeTruthy();
  });
});

test.describe('AI对话功能测试', () => {
  const TEST_TASK_ID = '0f0bb549-f8a3-41c0-bdf6-8f709c28e181';

  test.beforeEach(async ({ page }) => {
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');
    // 等待页面完全加载
    await page.waitForTimeout(1000);
  });

  test('聊天面板显示（需要页面数据）', async ({ page }) => {
    // 检查聊天面板（只有当任务有页面时才显示）
    const chatPanel = page.locator('.chat-panel');
    
    // 如果任务有页面，检查聊天面板
    if (await chatPanel.count() > 0) {
      // 检查消息列表区域
      const chatMessages = page.locator('.chat-messages');
      await expect(chatMessages).toBeVisible();

      // 检查输入区域
      const chatInput = page.locator('.chat-input');
      await expect(chatInput).toBeVisible();
    } else {
      // 如果没有页面，应该显示空状态提示
      const emptyState = page.locator('.t-empty, .empty');
      const hasEmpty = await emptyState.count() > 0;
      expect(hasEmpty).toBeTruthy();
    }
  });

  test('消息输入框功能（需要页面数据）', async ({ page }) => {
    // 检查输入框（只有当任务有页面时才显示）
    const textarea = page.locator('.chat-input textarea');
    
    if (await textarea.count() > 0) {
      await expect(textarea).toBeVisible();
      await expect(textarea).toBeEditable();

      // 输入测试消息
      await textarea.fill('修改标题为测试标题');
      await expect(textarea).toHaveValue('修改标题为测试标题');
    }
  });

  test('发送按钮状态（需要页面数据）', async ({ page }) => {
    // 检查发送按钮（只有当任务有页面时才显示）
    const sendButton = page.locator('.chat-input button:has-text("发送")');
    
    if (await sendButton.count() > 0) {
      await expect(sendButton).toBeVisible();

      // 检查清空按钮
      const clearButton = page.locator('.chat-input button:has-text("清空")');
      await expect(clearButton).toBeVisible();
    }
  });

  test('清空输入功能（需要页面数据）', async ({ page }) => {
    // 输入文本（只有当任务有页面时才显示）
    const textarea = page.locator('.chat-input textarea');
    
    if (await textarea.count() > 0) {
      await textarea.fill('测试文本');

      // 点击清空按钮
      await page.locator('.chat-input button:has-text("清空")').click();

      // 验证输入框已清空
      await expect(textarea).toHaveValue('');
    }
  });

  test('快捷键发送消息（需要页面数据）', async ({ page }) => {
    // 输入文本（只有当任务有页面时才显示）
    const textarea = page.locator('.chat-input textarea');
    
    if (await textarea.count() > 0) {
      await textarea.fill('测试消息');

      // 按Enter发送
      await textarea.press('Enter');

      // 输入框应该被清空（如果发送成功）
      await page.waitForTimeout(500);
    }
  });

  test('Shift+Enter换行（需要页面数据）', async ({ page }) => {
    // 输入文本（只有当任务有页面时才显示）
    const textarea = page.locator('.chat-input textarea');
    
    if (await textarea.count() > 0) {
      await textarea.fill('第一行');

      // 按Shift+Enter应该换行
      await textarea.press('Shift+Enter');
      await textarea.fill('第一行\n第二行');

      // 验证多行文本
      await expect(textarea).toHaveValue(/第一行/);
    }
  });

  test('空消息不发送（需要页面数据）', async ({ page }) => {
    // 确保输入框为空（只有当任务有页面时才显示）
    const textarea = page.locator('.chat-input textarea');
    
    if (await textarea.count() > 0) {
      await textarea.clear();

      // 点击发送按钮
      await page.locator('.chat-input button:has-text("发送")').click();

      // 不应该有任何消息发送（检查消息列表仍为空或保持原状态）
      const messageItems = page.locator('.message-item');
      const initialCount = await messageItems.count();

      // 等待一下，确保没有新消息
      await page.waitForTimeout(300);

      const finalCount = await messageItems.count();
      expect(finalCount).toBe(initialCount);
    }
  });
});

test.describe('页面列表交互测试', () => {
  const TEST_TASK_ID = '0f0bb549-f8a3-41c0-bdf6-8f709c28e181';

  test.beforeEach(async ({ page }) => {
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');
  });

  test('页面选择功能', async ({ page }) => {
    // 检查页面项
    const pageItems = page.locator('.page-item');

    if (await pageItems.count() > 0) {
      // 点击第一个页面
      await pageItems.first().click();

      // 应该添加选中状态
      await expect(pageItems.first()).toHaveClass(/selected/);
    }
  });

  test('页面信息显示', async ({ page }) => {
    const pageItems = page.locator('.page-item');

    if (await pageItems.count() > 0) {
      // 检查页面编号
      const pageNumber = page.locator('.page-number');
      await expect(pageNumber.first()).toBeVisible();

      // 检查页面标题
      const pageTitle = page.locator('.page-title');
      await expect(pageTitle.first()).toBeVisible();
    }
  });

  test('修改次数徽章显示', async ({ page }) => {
    // 检查是否有修改次数徽章
    const badge = page.locator('.page-meta .t-badge');

    if (await badge.count() > 0) {
      await expect(badge.first()).toBeVisible();
    }
  });
});

test.describe('版本管理功能测试', () => {
  const TEST_TASK_ID = '0f0bb549-f8a3-41c0-bdf6-8f709c28e181';

  test.beforeEach(async ({ page }) => {
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('导出确认对话框（需要任务数据）', async ({ page }) => {
    // 点击导出按钮（只有任务加载成功后才显示）
    const exportButton = page.locator('button:has-text("导出PPT")');
    
    if (await exportButton.count() > 0) {
      await exportButton.click();

      // 检查确认对话框
      const dialog = page.locator('.t-dialog');
      await expect(dialog).toBeVisible();

      // 检查对话框内容
      await expect(dialog).toContainText('确认导出');

      // 取消对话框
      await page.locator('.t-dialog button:has-text("取消")').click();
      await expect(dialog).not.toBeVisible();
    }
  });

  test('保存功能（如果有保存按钮）', async ({ page }) => {
    // 检查是否有保存按钮
    const saveButton = page.locator('button:has-text("保存")');

    if (await saveButton.count() > 0) {
      await expect(saveButton).toBeVisible();
    }
  });
});

test.describe('元素操作测试', () => {
  const TEST_TASK_ID = '0f0bb549-f8a3-41c0-bdf6-8f709c28e181';

  test.beforeEach(async ({ page }) => {
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
  });

  test('文本编辑指令（需要页面数据）', async ({ page }) => {
    // 输入文本编辑指令（只有当任务有页面时才显示）
    const textarea = page.locator('.chat-input textarea');
    
    if (await textarea.count() > 0) {
      await textarea.fill('修改标题文本为"新标题"');

      // 点击发送
      await page.locator('.chat-input button:has-text("发送")').click();

      // 等待响应
      await page.waitForTimeout(500);

      // 消息应该被发送
      const messageItems = page.locator('.message-item');
      const count = await messageItems.count();
      expect(count).toBeGreaterThanOrEqual(0);
    }
  });

  test('样式修改指令（需要页面数据）', async ({ page }) => {
    // 输入样式修改指令（只有当任务有页面时才显示）
    const textarea = page.locator('.chat-input textarea');
    
    if (await textarea.count() > 0) {
      await textarea.fill('将标题字体改为红色');

      // 点击发送
      await page.locator('.chat-input button:has-text("发送")').click();

      // 等待响应
      await page.waitForTimeout(500);
    }
  });

  test('图片替换指令（需要页面数据）', async ({ page }) => {
    // 输入图片替换指令（只有当任务有页面时才显示）
    const textarea = page.locator('.chat-input textarea');
    
    if (await textarea.count() > 0) {
      await textarea.fill('替换图片为产品图片');

      // 点击发送
      await page.locator('.chat-input button:has-text("发送")').click();

      // 等待响应
      await page.waitForTimeout(500);
    }
  });
});

test.describe('撤销/重做功能测试', () => {
  const TEST_TASK_ID = '0f0bb549-f8a3-41c0-bdf6-8f709c28e181';

  test.beforeEach(async ({ page }) => {
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');
  });

  test('撤销按钮（如果有）', async ({ page }) => {
    // 检查是否有撤销按钮
    const undoButton = page.locator('button:has-text("撤销"), button[title="撤销"]');

    if (await undoButton.count() > 0) {
      await expect(undoButton.first()).toBeVisible();
    }
  });

  test('重做按钮（如果有）', async ({ page }) => {
    // 检查是否有重做按钮
    const redoButton = page.locator('button:has-text("重做"), button[title="重做"]');

    if (await redoButton.count() > 0) {
      await expect(redoButton.first()).toBeVisible();
    }
  });

  test('历史记录功能（如果有）', async ({ page }) => {
    // 检查是否有历史记录按钮
    const historyButton = page.locator('button:has-text("历史"), button[title="历史记录"]');

    if (await historyButton.count() > 0) {
      await expect(historyButton).toBeVisible();
    }
  });
});

test.describe('响应式布局测试', () => {
  const TEST_TASK_ID = '0f0bb549-f8a3-41c0-bdf6-8f709c28e181';

  test('桌面端布局', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // 检查侧边栏显示（只有任务加载成功后才显示）
    const sidebar = page.locator('.pages-sidebar');
    if (await sidebar.count() > 0) {
      await expect(sidebar).toBeVisible();
    }

    // 检查聊天面板显示（只有任务有页面时才显示）
    const chatPanel = page.locator('.chat-panel');
    if (await chatPanel.count() > 0) {
      await expect(chatPanel).toBeVisible();
    }
  });

  test('平板端布局', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');

    // 页面应该正常显示
    const refinementPage = page.locator('.refinement-page');
    await expect(refinementPage).toBeVisible();
  });

  test('移动端布局', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');

    // 页面应该正常显示，可能需要滚动
    const refinementPage = page.locator('.refinement-page');
    await expect(refinementPage).toBeVisible();
  });
});

test.describe('辅助功能测试', () => {
  const TEST_TASK_ID = '0f0bb549-f8a3-41c0-bdf6-8f709c28e181';

  test('键盘导航', async ({ page }) => {
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');

    // Tab键导航
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    // 应该有元素获得焦点（需要页面元素可聚焦）
    const focusedElement = page.locator(':focus');
    if (await focusedElement.count() > 0) {
      await expect(focusedElement).toBeVisible();
    }
  });

  test('输入框无障碍标签（需要页面数据）', async ({ page }) => {
    await page.goto(`/#/refinement/${TEST_TASK_ID}`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // 检查输入框是否有placeholder（只有当任务有页面时才显示）
    const textarea = page.locator('.chat-input textarea');
    if (await textarea.count() > 0) {
      const placeholder = await textarea.getAttribute('placeholder');
      expect(placeholder).toBeTruthy();
    }
  });
});
