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
