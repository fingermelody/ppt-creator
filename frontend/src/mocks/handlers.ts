/* API Mock 处理器 */

import { mockDocuments, mockSlides, mockDrafts, mockRefinementTask, mockRefinedPages, mockMessages } from './data';

// 模拟延迟
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// 模拟生成 ID
const generateId = () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

// 文档 API mock handlers
export const documentHandlers = {
  // 获取文档列表
  getDocuments: async (params?: any) => {
    await delay(300);
    return {
      documents: mockDocuments,
      total: mockDocuments.length,
    };
  },

  // 获取文档详情
  getDocument: async (id: string) => {
    await delay(200);
    const doc = mockDocuments.find((d) => d.id === id);
    if (!doc) throw new Error('Document not found');
    return doc;
  },

  // 获取文档页面
  getDocumentSlides: async (documentId: string) => {
    await delay(300);
    const slides = mockSlides[documentId] || [];
    return { slides };
  },

  // 删除文档
  deleteDocument: async (id: string) => {
    await delay(200);
    const index = mockDocuments.findIndex((d) => d.id === id);
    if (index > -1) {
      mockDocuments.splice(index, 1);
    }
    return { success: true };
  },

  // 初始化上传
  initUpload: async (data: any) => {
    await delay(100);
    return {
      upload_id: generateId(),
      chunk_size: 5 * 1024 * 1024,
    };
  },

  // 上传分片
  uploadChunk: async (uploadId: string, chunkIndex: number, chunk: any) => {
    await delay(100);
    return {
      success: true,
      received_chunks: chunkIndex + 1,
    };
  },

  // 完成上传
  completeUpload: async (data: any) => {
    await delay(500);
    const newDoc = {
      id: generateId(),
      title: data.title,
      category: data.category,
      page_count: Math.floor(Math.random() * 20) + 5,
      status: 'ready',
      thumbnail: `https://via.placeholder.com/400x300?text=${encodeURIComponent(data.title)}`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      file_size: Math.floor(Math.random() * 10000000) + 1000000,
    };
    mockDocuments.unshift(newDoc);
    return {
      document_id: newDoc.id,
      status: 'ready',
    };
  },

  // 搜索文档
  searchDocuments: async (query: string) => {
    await delay(300);
    const filtered = mockDocuments.filter((doc) =>
      doc.title.toLowerCase().includes(query.toLowerCase())
    );
    return {
      documents: filtered,
      total: filtered.length,
    };
  },
};

// 组装 API mock handlers
export const assemblyHandlers = {
  // 创建草稿
  createDraft: async (data: any) => {
    await delay(300);
    const newDraft = {
      id: generateId(),
      title: data.title || '新PPT',
      description: data.description,
      chapters: [],
      total_pages: 0,
      status: 'draft',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      version: 1,
    };
    mockDrafts.unshift(newDraft);
    return {
      draft_id: newDraft.id,
      created_at: newDraft.created_at,
    };
  },

  // 获取草稿列表
  getDrafts: async (params?: any) => {
    await delay(300);
    return {
      drafts: mockDrafts,
      total: mockDrafts.length,
    };
  },

  // 获取草稿详情
  getDraftDetail: async (id: string) => {
    await delay(200);
    const draft = mockDrafts.find((d) => d.id === id);
    if (!draft) throw new Error('Draft not found');
    return {
      draft,
      can_undo: draft.version > 1,
      can_redo: false,
      undo_description: '删除章节',
    };
  },

  // 保存草稿
  saveDraft: async (id: string, data?: any) => {
    await delay(200);
    const draft = mockDrafts.find((d) => d.id === id);
    if (draft && data?.title) {
      draft.title = data.title;
      draft.updated_at = new Date().toISOString();
    }
    return {
      success: true,
      saved_at: new Date().toISOString(),
      version: draft?.version || 1,
    };
  },

  // 删除草稿
  deleteDraft: async (id: string) => {
    await delay(200);
    const index = mockDrafts.findIndex((d) => d.id === id);
    if (index > -1) {
      mockDrafts.splice(index, 1);
    }
    return { success: true };
  },

  // 导出PPT
  exportPPT: async (id: string, data?: any) => {
    await delay(1000);
    return {
      download_url: 'https://via.placeholder.com/file.pptx',
      file_size: 10485760,
      page_count: 10,
    };
  },

  // 添加章节
  addChapter: async (draftId: string, data: any) => {
    await delay(500);
    const draft = mockDrafts.find((d) => d.id === draftId);
    if (!draft) throw new Error('Draft not found');

    const chapter = {
      id: generateId(),
      title: data.title,
      description: data.description,
      required_pages: data.required_pages,
      page_count: data.required_pages,
      pages: Array.from({ length: data.required_pages }, (_, i) => ({
        slide_id: generateId(),
        document_id: mockDocuments[Math.floor(Math.random() * mockDocuments.length)].id,
        document_title: mockDocuments[Math.floor(Math.random() * mockDocuments.length)].title,
        page_number: i + 1,
        thumbnail: `https://via.placeholder.com/280x200?text=${encodeURIComponent(data.title)}-${i + 1}`,
        similarity: Math.floor(Math.random() * 20) + 80,
        content_summary: `${data.description} - 第${i + 1}页`,
        order: i,
      })),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    draft.chapters.push(chapter);
    draft.total_pages += chapter.page_count;

    return {
      chapter_id: chapter.id,
      generated_pages: chapter.pages,
      total_pages: chapter.page_count,
    };
  },

  // 更新章节
  updateChapter: async (draftId: string, chapterId: string, data: any) => {
    await delay(500);
    const draft = mockDrafts.find((d) => d.id === draftId);
    if (!draft) throw new Error('Draft not found');

    const chapter = draft.chapters.find((c) => c.id === chapterId);
    if (!chapter) throw new Error('Chapter not found');

    if (data.title) chapter.title = data.title;
    if (data.description) chapter.description = data.description;
    if (data.required_pages) {
      const diff = data.required_pages - chapter.page_count;
      chapter.required_pages = data.required_pages;
      chapter.page_count = data.required_pages;
      draft.total_pages += diff;
    }

    return {
      chapter_id: chapter.id,
      generated_pages: chapter.pages,
    };
  },

  // 删除章节
  deleteChapter: async (draftId: string, chapterId: string) => {
    await delay(200);
    const draft = mockDrafts.find((d) => d.id === draftId);
    if (!draft) throw new Error('Draft not found');

    const index = draft.chapters.findIndex((c) => c.id === chapterId);
    if (index > -1) {
      draft.total_pages -= draft.chapters[index].page_count;
      draft.chapters.splice(index, 1);
    }

    return { success: true };
  },

  // 重新生成章节
  regenerateChapter: async (draftId: string, chapterId: string) => {
    await delay(500);
    const draft = mockDrafts.find((d) => d.id === draftId);
    if (!draft) throw new Error('Draft not found');

    const chapter = draft.chapters.find((c) => c.id === chapterId);
    if (!chapter) throw new Error('Chapter not found');

    return {
      chapter_id: chapter.id,
      generated_pages: chapter.pages,
    };
  },

  // 获取备选页面
  getAlternatives: async (draftId: string, chapterId: string, slideId: string, limit: number) => {
    await delay(300);
    const alternatives = Array.from({ length: limit }, (_, i) => ({
      slide_id: generateId(),
      document_id: mockDocuments[Math.floor(Math.random() * mockDocuments.length)].id,
      document_title: mockDocuments[Math.floor(Math.random() * mockDocuments.length)].title,
      page_number: Math.floor(Math.random() * 20) + 1,
      thumbnail: `https://via.placeholder.com/280x200?text=Alt-${i + 1}`,
      similarity: Math.floor(Math.random() * 30) + 60,
      content_summary: `备选页面 ${i + 1}`,
    }));

    return {
      current_page: {
        slide_id,
        document_id: 'doc-001',
        document_title: '文档示例',
        page_number: 1,
        thumbnail: 'https://via.placeholder.com/280x200?text=Current',
        similarity: 85.5,
        content_summary: '当前页面内容',
      },
      alternatives,
    };
  },

  // 替换页面
  replacePage: async (draftId: string, chapterId: string, oldSlideId: string, data: any) => {
    await delay(300);
    const draft = mockDrafts.find((d) => d.id === draftId);
    if (!draft) throw new Error('Draft not found');

    const chapter = draft.chapters.find((c) => c.id === chapterId);
    if (!chapter) throw new Error('Chapter not found');

    const pageIndex = chapter.pages.findIndex((p) => p.slide_id === oldSlideId);
    if (pageIndex === -1) throw new Error('Slide not found');

    const oldPage = chapter.pages[pageIndex];
    const newPages = data.new_slide_ids.map((id: string) => ({
      slide_id: id,
      document_id: mockDocuments[Math.floor(Math.random() * mockDocuments.length)].id,
      document_title: mockDocuments[Math.floor(Math.random() * mockDocuments.length)].title,
      page_number: Math.floor(Math.random() * 20) + 1,
      thumbnail: `https://via.placeholder.com/280x200?text=New`,
      similarity: Math.floor(Math.random() * 20) + 80,
      content_summary: '新页面',
      order: 0,
    }));

    chapter.pages.splice(pageIndex, 1, ...newPages);
    chapter.page_count = chapter.page_count - 1 + newPages.length;
    draft.total_pages = draft.total_pages - 1 + newPages.length;

    return {
      success: true,
      replaced_pages: [oldPage],
      new_pages: newPages,
    };
  },

  // 删除页面
  deletePage: async (draftId: string, chapterId: string, slideId: string) => {
    await delay(200);
    const draft = mockDrafts.find((d) => d.id === draftId);
    if (!draft) throw new Error('Draft not found');

    const chapter = draft.chapters.find((c) => c.id === chapterId);
    if (!chapter) throw new Error('Chapter not found');

    const index = chapter.pages.findIndex((p) => p.slide_id === slideId);
    if (index > -1) {
      chapter.pages.splice(index, 1);
      chapter.page_count--;
      draft.total_pages--;
    }

    return { success: true };
  },

  // 添加页面
  addPage: async (draftId: string, chapterId: string, slideId: string, order: number) => {
    await delay(200);
    const draft = mockDrafts.find((d) => d.id === draftId);
    if (!draft) throw new Error('Draft not found');

    const chapter = draft.chapters.find((c) => c.id === chapterId);
    if (!chapter) throw new Error('Chapter not found');

    const newPage = {
      slide_id: slideId,
      document_id: mockDocuments[0]?.id || 'doc-001',
      document_title: mockDocuments[0]?.title || '文档',
      page_number: 1,
      thumbnail: `https://via.placeholder.com/280x200?text=New-Page`,
      similarity: 85,
      content_summary: '新添加的页面',
      order,
    };

    chapter.pages.splice(order, 0, newPage);
    chapter.page_count++;
    draft.total_pages++;

    return { success: true, page: newPage };
  },

  // 撤销
  undo: async (id: string) => {
    await delay(200);
    const draft = mockDrafts.find((d) => d.id === id);
    if (!draft) throw new Error('Draft not found');
    if (draft.version > 1) {
      draft.version--;
    }
    return {
      success: true,
      draft,
      operation: '撤销操作',
    };
  },

  // 重做
  redo: async (id: string) => {
    await delay(200);
    const draft = mockDrafts.find((d) => d.id === id);
    if (!draft) throw new Error('Draft not found');
    draft.version++;
    return {
      success: true,
      draft,
      operation: '重做操作',
    };
  },
};

// 精修 API mock handlers
export const refinementHandlers = {
  // 创建精修任务
  createTask: async (data: any) => {
    await delay(300);
    return {
      task_id: mockRefinementTask.id,
      total_pages: mockRefinedPages.length,
      created_at: new Date().toISOString(),
    };
  },

  // 获取精修任务详情
  getTaskDetail: async (id: string) => {
    await delay(200);
    return {
      task: mockRefinementTask,
      pages: mockRefinedPages,
      total_pages: mockRefinedPages.length,
      total_modifications: 3,
    };
  },

  // 保存精修版本
  saveTask: async (id: string, data?: any) => {
    await delay(200);
    if (data?.title) {
      mockRefinementTask.title = data.title;
    }
    return {
      success: true,
      saved_at: new Date().toISOString(),
      version: 2,
    };
  },

  // 导出精修PPT
  exportRefinedPPT: async (id: string) => {
    await delay(1000);
    return {
      download_url: 'https://via.placeholder.com/file.pptx',
      file_size: 10485760,
      exported_at: new Date().toISOString(),
    };
  },

  // 获取页面内容
  getPageContent: async (taskId: string, pageIndex: number) => {
    await delay(200);
    const page = mockRefinedPages[pageIndex];
    if (!page) throw new Error('Page not found');
    return page;
  },

  // 获取页面缩略图
  getPageThumbnail: async (taskId: string, pageIndex: number) => {
    await delay(100);
    return {
      image_url: `https://via.placeholder.com/400x300?text=Page-${pageIndex + 1}`,
      generated_at: new Date().toISOString(),
    };
  },

  // 发送消息
  sendMessage: async (taskId: string, pageIndex: number, message: string, data?: any) => {
    await delay(500);
    const userMsg: any = {
      id: generateId(),
      role: 'user',
      content: message,
      type: 'chat',
      timestamp: new Date().toISOString(),
    };

    const assistantMsg: any = {
      id: generateId(),
      role: 'assistant',
      content: `已执行您的操作：${message}`,
      type: 'modification',
      timestamp: new Date().toISOString(),
    };

    if (!mockMessages[pageIndex]) {
      mockMessages[pageIndex] = [];
    }
    mockMessages[pageIndex].push(userMsg, assistantMsg);

    return {
      success: true,
      message_id: userMsg.id,
      assistant_message: assistantMsg.content,
    };
  },

  // 获取对话历史
  getChatHistory: async (taskId: string, pageIndex: number) => {
    await delay(200);
    return {
      conversation_id: `conv-${taskId}-${pageIndex}`,
      messages: mockMessages[pageIndex] || [],
    };
  },
};

// PPT 模板 mock 数据
const mockTemplates: any[] = [
  {
    id: 'tpl-001',
    name: '商务简约',
    description: '简洁大气的商务演示模板，适合汇报和提案',
    category: 'business',
    preview_url: 'https://via.placeholder.com/800x600?text=商务简约',
    thumbnail_url: 'https://via.placeholder.com/400x300?text=商务简约',
    color_scheme: { primary: '#1890ff', secondary: '#f5f5f5', accent: '#52c41a', background: '#ffffff', text: '#333333' },
    font_family: '微软雅黑',
    is_premium: false,
    usage_count: 1520,
    created_at: '2025-01-15T08:00:00Z',
  },
  {
    id: 'tpl-002',
    name: '科技感',
    description: '深蓝色科技风格，适合科技产品和技术分享',
    category: 'technology',
    preview_url: 'https://via.placeholder.com/800x600?text=科技感',
    thumbnail_url: 'https://via.placeholder.com/400x300?text=科技感',
    color_scheme: { primary: '#0d47a1', secondary: '#1a237e', accent: '#00bcd4', background: '#0a1929', text: '#ffffff' },
    font_family: 'Roboto',
    is_premium: false,
    usage_count: 980,
    created_at: '2025-01-10T08:00:00Z',
  },
  {
    id: 'tpl-003',
    name: '教育培训',
    description: '温馨明亮的教育风格，适合教学和培训',
    category: 'education',
    preview_url: 'https://via.placeholder.com/800x600?text=教育培训',
    thumbnail_url: 'https://via.placeholder.com/400x300?text=教育培训',
    color_scheme: { primary: '#ff9800', secondary: '#fff3e0', accent: '#4caf50', background: '#ffffff', text: '#333333' },
    font_family: '思源黑体',
    is_premium: false,
    usage_count: 756,
    created_at: '2025-01-08T08:00:00Z',
  },
  {
    id: 'tpl-004',
    name: '创意设计',
    description: '多彩创意风格，适合创意提案和作品展示',
    category: 'creative',
    preview_url: 'https://via.placeholder.com/800x600?text=创意设计',
    thumbnail_url: 'https://via.placeholder.com/400x300?text=创意设计',
    color_scheme: { primary: '#e91e63', secondary: '#fce4ec', accent: '#9c27b0', background: '#ffffff', text: '#333333' },
    font_family: 'Poppins',
    is_premium: true,
    usage_count: 432,
    created_at: '2025-01-05T08:00:00Z',
  },
  {
    id: 'tpl-005',
    name: '极简白',
    description: '极简主义设计，大量留白，专注内容',
    category: 'minimalist',
    preview_url: 'https://via.placeholder.com/800x600?text=极简白',
    thumbnail_url: 'https://via.placeholder.com/400x300?text=极简白',
    color_scheme: { primary: '#333333', secondary: '#f5f5f5', accent: '#1890ff', background: '#ffffff', text: '#333333' },
    font_family: 'Helvetica Neue',
    is_premium: false,
    usage_count: 1200,
    created_at: '2025-01-01T08:00:00Z',
  },
  {
    id: 'tpl-006',
    name: '暗黑风格',
    description: '深色背景高端风格，适合正式场合',
    category: 'dark',
    preview_url: 'https://via.placeholder.com/800x600?text=暗黑风格',
    thumbnail_url: 'https://via.placeholder.com/400x300?text=暗黑风格',
    color_scheme: { primary: '#bb86fc', secondary: '#1f1f1f', accent: '#03dac6', background: '#121212', text: '#e1e1e1' },
    font_family: 'Inter',
    is_premium: true,
    usage_count: 567,
    created_at: '2024-12-28T08:00:00Z',
  },
  {
    id: 'tpl-007',
    name: '多彩渐变',
    description: '活力四射的渐变色彩，适合年轻化场景',
    category: 'colorful',
    preview_url: 'https://via.placeholder.com/800x600?text=多彩渐变',
    thumbnail_url: 'https://via.placeholder.com/400x300?text=多彩渐变',
    color_scheme: { primary: '#ff6b6b', secondary: '#4ecdc4', accent: '#ffe66d', background: '#ffffff', text: '#333333' },
    font_family: 'Nunito',
    is_premium: false,
    usage_count: 890,
    created_at: '2024-12-25T08:00:00Z',
  },
  {
    id: 'tpl-008',
    name: '商务深蓝',
    description: '专业稳重的深蓝色商务风格',
    category: 'business',
    preview_url: 'https://via.placeholder.com/800x600?text=商务深蓝',
    thumbnail_url: 'https://via.placeholder.com/400x300?text=商务深蓝',
    color_scheme: { primary: '#1a365d', secondary: '#e2e8f0', accent: '#3182ce', background: '#ffffff', text: '#1a202c' },
    font_family: 'Source Sans Pro',
    is_premium: false,
    usage_count: 1100,
    created_at: '2024-12-20T08:00:00Z',
  },
];

// PPT 生成任务 mock 数据
const mockGenerationTasks: any[] = [
  {
    id: 'gen-001',
    title: '人工智能发展趋势分析',
    topic: '分析2024-2025年人工智能领域的最新发展趋势，包括大语言模型、AI Agent、多模态等方向的技术突破和应用场景',
    status: 'completed',
    progress: 100,
    template_id: 'tpl-002',
    style_reference: { type: 'template', template_id: 'tpl-002', preview_url: 'https://via.placeholder.com/800x600?text=科技感' },
    generated_pages: Array.from({ length: 10 }, (_, i) => ({
      id: `page-001-${i + 1}`,
      index: i,
      title: i === 0 ? '人工智能发展趋势分析' : `第${i}章节`,
      content: {
        title: i === 0 ? '人工智能发展趋势分析' : `章节${i}标题`,
        bullet_points: ['要点1：技术突破', '要点2：应用场景', '要点3：未来展望'],
      },
      thumbnail: `https://via.placeholder.com/400x300?text=AI-Page-${i + 1}`,
      sources: ['source-1', 'source-2'],
      generated_at: '2025-02-01T10:30:00Z',
    })),
    web_sources: [
      { id: 'src-001', title: 'OpenAI发布GPT-5', url: 'https://example.com/gpt5', snippet: 'OpenAI宣布推出新一代大语言模型...', relevance: 95, fetched_at: '2025-02-01T10:00:00Z' },
      { id: 'src-002', title: 'AI Agent技术白皮书', url: 'https://example.com/ai-agent', snippet: 'AI Agent正在改变软件开发方式...', relevance: 88, fetched_at: '2025-02-01T10:01:00Z' },
      { id: 'src-003', title: '多模态AI最新进展', url: 'https://example.com/multimodal', snippet: '融合文本、图像、视频的多模态AI...', relevance: 82, fetched_at: '2025-02-01T10:02:00Z' },
    ],
    total_pages: 10,
    created_at: '2025-02-01T10:00:00Z',
    updated_at: '2025-02-01T10:30:00Z',
    completed_at: '2025-02-01T10:30:00Z',
  },
  {
    id: 'gen-002',
    title: '新能源汽车市场报告',
    topic: '深入分析新能源汽车市场现状、主要厂商竞争格局、技术发展路线和未来市场预测',
    status: 'completed',
    progress: 100,
    template_id: 'tpl-001',
    style_reference: { type: 'template', template_id: 'tpl-001', preview_url: 'https://via.placeholder.com/800x600?text=商务简约' },
    generated_pages: Array.from({ length: 15 }, (_, i) => ({
      id: `page-002-${i + 1}`,
      index: i,
      title: `新能源汽车报告-第${i + 1}页`,
      content: {
        title: `页面${i + 1}`,
        bullet_points: ['市场分析', '技术趋势', '竞争格局'],
      },
      thumbnail: `https://via.placeholder.com/400x300?text=EV-Page-${i + 1}`,
      sources: ['source-3'],
      generated_at: '2025-01-28T15:00:00Z',
    })),
    web_sources: [
      { id: 'src-004', title: '2025新能源汽车销量报告', url: 'https://example.com/ev-sales', snippet: '新能源汽车销量持续增长...', relevance: 92, fetched_at: '2025-01-28T14:30:00Z' },
    ],
    total_pages: 15,
    created_at: '2025-01-28T14:30:00Z',
    updated_at: '2025-01-28T15:00:00Z',
    completed_at: '2025-01-28T15:00:00Z',
  },
];

// PPT 生成 API mock handlers
export const generationHandlers = {
  // 获取模板列表
  getTemplates: async (category?: string) => {
    await delay(300);
    let templates = mockTemplates;
    if (category && category !== 'all') {
      templates = mockTemplates.filter((t) => t.category === category);
    }
    const categories = [...new Set(mockTemplates.map((t) => t.category))];
    return {
      templates,
      total: templates.length,
      categories,
    };
  },

  // 获取任务列表
  getTasks: async () => {
    await delay(300);
    return {
      tasks: mockGenerationTasks,
      total: mockGenerationTasks.length,
    };
  },

  // 获取任务详情
  getTaskDetail: async (taskId: string) => {
    await delay(200);
    const task = mockGenerationTasks.find((t) => t.id === taskId);
    if (!task) {
      // 如果没找到，返回一个新生成的任务
      return {
        id: taskId,
        title: '新生成的PPT',
        topic: '用户输入的主题',
        status: 'completed',
        progress: 100,
        template_id: 'tpl-001',
        generated_pages: Array.from({ length: 10 }, (_, i) => ({
          id: `page-new-${i + 1}`,
          index: i,
          title: `第${i + 1}页`,
          content: {
            title: `页面${i + 1}`,
            bullet_points: ['要点1', '要点2', '要点3'],
          },
          thumbnail: `https://via.placeholder.com/400x300?text=Page-${i + 1}`,
          sources: [],
          generated_at: new Date().toISOString(),
        })),
        web_sources: [],
        total_pages: 10,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        completed_at: new Date().toISOString(),
      };
    }
    return task;
  },

  // 开始生成
  startGeneration: async (request: any) => {
    await delay(500);
    const taskId = `gen-${Date.now()}`;
    const newTask = {
      id: taskId,
      title: request.title || `关于"${request.topic.slice(0, 20)}..."的PPT`,
      topic: request.topic,
      status: 'pending',
      progress: 0,
      template_id: request.template_id,
      style_reference: request.template_id 
        ? { type: 'template', template_id: request.template_id }
        : null,
      generated_pages: [],
      web_sources: [],
      total_pages: request.page_count || 10,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    mockGenerationTasks.unshift(newTask);
    return {
      task_id: taskId,
      status: 'pending',
      message: '任务已创建，开始生成...',
      estimated_time: 60,
    };
  },

  // 获取生成进度
  getProgress: async (taskId: string) => {
    await delay(100);
    const task = mockGenerationTasks.find((t) => t.id === taskId);
    return {
      task_id: taskId,
      status: task?.status || 'generating',
      progress: task?.progress || 50,
      current_step: 'generating',
      message: '正在生成PPT内容...',
      sources_found: 5,
      pages_generated: Math.floor((task?.progress || 50) / 10),
    };
  },

  // 取消生成
  cancelGeneration: async (taskId: string) => {
    await delay(200);
    const task = mockGenerationTasks.find((t) => t.id === taskId);
    if (task) {
      task.status = 'failed';
    }
    return { success: true };
  },

  // 导出PPT
  exportPPT: async (taskId: string) => {
    await delay(1000);
    const task = mockGenerationTasks.find((t) => t.id === taskId);
    return {
      download_url: 'https://via.placeholder.com/file.pptx',
      file_size: 10485760,
      file_name: `${task?.title || 'PPT'}.pptx`,
      exported_at: new Date().toISOString(),
    };
  },

  // 删除任务
  deleteTask: async (taskId: string) => {
    await delay(200);
    const index = mockGenerationTasks.findIndex((t) => t.id === taskId);
    if (index > -1) {
      mockGenerationTasks.splice(index, 1);
    }
    return { success: true };
  },

  // 重新生成指定页面
  regeneratePage: async (taskId: string, pageIndex: number) => {
    await delay(500);
    return {
      success: true,
      page: {
        id: `page-regen-${Date.now()}`,
        index: pageIndex,
        title: `重新生成的第${pageIndex + 1}页`,
        content: {
          title: `页面${pageIndex + 1}`,
          bullet_points: ['新要点1', '新要点2', '新要点3'],
        },
        thumbnail: `https://via.placeholder.com/400x300?text=Regen-${pageIndex + 1}`,
        sources: [],
        generated_at: new Date().toISOString(),
      },
    };
  },

  // 上传自定义模板
  uploadCustomTemplate: async (file: File) => {
    await delay(1000);
    return {
      template_id: `custom-${Date.now()}`,
      preview_url: `https://via.placeholder.com/800x600?text=${encodeURIComponent(file.name)}`,
    };
  },
};
