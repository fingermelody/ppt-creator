/* 组装 API - Mock 版本 */

import { mockApi, useMock } from '../mocks/api';
import type { PPTOutline } from '../types/outline';

const assemblyApi = {
  createDraft: async (title: string, description?: string) => {
    if (useMock()) {
      return mockApi.assembly.createDraft({ title, description });
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.createDraft(title, description);
  },

  // 基于大纲创建草稿
  createDraftFromOutline: async (outline: PPTOutline) => {
    if (useMock()) {
      // Mock 实现：基于大纲结构创建草稿
      await new Promise((resolve) => setTimeout(resolve, 800));
      
      const draftId = `draft-${Date.now()}`;
      const chapters = outline.chapters.map((ch, index) => ({
        id: `ch-${index + 1}`,
        title: ch.title,
        description: ch.summary,
        required_pages: ch.page_count,
        page_count: ch.page_count,
        pages: Array.from({ length: ch.page_count }, (_, i) => ({
          slide_id: `slide-${ch.id}-${i + 1}`,
          document_id: `doc-${i + 1}`,
          document_title: `示例文档 ${i + 1}`,
          page_number: i + 1,
          thumbnail: `https://picsum.photos/seed/${ch.id}-${i}/400/225`,
          similarity: 0.85 + Math.random() * 0.1,
          content_summary: `${ch.title} - 第${i + 1}页内容摘要`,
          order: i,
        })),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }));

      return {
        draft_id: draftId,
        message: '草稿创建成功',
        draft: {
          id: draftId,
          title: outline.title,
          description: outline.objective,
          chapters,
          total_pages: outline.total_pages,
          status: 'draft' as const,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          version: 1,
          outline_id: outline.id,
        },
      };
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.createDraftFromOutline(outline);
  },

  getDrafts: async (page = 1, limit = 20, status?: string) => {
    if (useMock()) {
      return mockApi.assembly.getDrafts({ page, limit, status });
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.getDrafts(page, limit, status);
  },

  getDraftDetail: async (draftId: string) => {
    if (useMock()) {
      return mockApi.assembly.getDraftDetail(draftId);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.getDraftDetail(draftId);
  },

  saveDraft: async (draftId: string, title?: string) => {
    if (useMock()) {
      return mockApi.assembly.saveDraft(draftId, { title });
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.saveDraft(draftId, title);
  },

  deleteDraft: async (draftId: string) => {
    if (useMock()) {
      return mockApi.assembly.deleteDraft(draftId);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.deleteDraft(draftId);
  },

  exportPPT: async (draftId: string, filename?: string) => {
    if (useMock()) {
      return mockApi.assembly.exportPPT(draftId, { filename });
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.exportPPT(draftId, filename);
  },

  addChapter: async (draftId: string, chapter: any) => {
    if (useMock()) {
      return mockApi.assembly.addChapter(draftId, chapter);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.addChapter(draftId, chapter);
  },

  updateChapter: async (draftId: string, chapterId: string, chapter: any) => {
    if (useMock()) {
      return mockApi.assembly.updateChapter(draftId, chapterId, chapter);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.updateChapter(draftId, chapterId, chapter);
  },

  deleteChapter: async (draftId: string, chapterId: string) => {
    if (useMock()) {
      return mockApi.assembly.deleteChapter(draftId, chapterId);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.deleteChapter(draftId, chapterId);
  },

  regenerateChapter: async (draftId: string, chapterId: string) => {
    if (useMock()) {
      return mockApi.assembly.regenerateChapter(draftId, chapterId);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.regenerateChapter(draftId, chapterId);
  },

  getAlternatives: async (draftId: string, chapterId: string, slideId: string, limit = 5) => {
    if (useMock()) {
      return mockApi.assembly.getAlternatives(draftId, chapterId, slideId, limit);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.getAlternatives(draftId, chapterId, slideId, limit);
  },

  replacePage: async (draftId: string, chapterId: string, oldSlideId: string, request: any) => {
    if (useMock()) {
      return mockApi.assembly.replacePage(draftId, chapterId, oldSlideId, request);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.replacePage(draftId, chapterId, oldSlideId, request);
  },

  deletePage: async (draftId: string, chapterId: string, slideId: string) => {
    if (useMock()) {
      return mockApi.assembly.deletePage(draftId, chapterId, slideId);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.deletePage(draftId, chapterId, slideId);
  },

  addPage: async (draftId: string, chapterId: string, slideId: string, order: number) => {
    if (useMock()) {
      return mockApi.assembly.addPage(draftId, chapterId, slideId, order);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.addPage(draftId, chapterId, slideId, order);
  },

  reorderPages: async (draftId: string, chapterId: string, pageOrders: any[]) => {
    if (useMock()) {
      return mockApi.assembly.reorderPages(draftId, chapterId, pageOrders);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.reorderPages(draftId, chapterId, pageOrders);
  },

  movePage: async (draftId: string, slideId: string, targetChapterId: string, targetOrder: number) => {
    if (useMock()) {
      return mockApi.assembly.movePage(draftId, slideId, targetChapterId, targetOrder);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.movePage(draftId, slideId, targetChapterId, targetOrder);
  },

  undo: async (draftId: string) => {
    if (useMock()) {
      return mockApi.assembly.undo(draftId);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.undo(draftId);
  },

  redo: async (draftId: string) => {
    if (useMock()) {
      return mockApi.assembly.redo(draftId);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.redo(draftId);
  },

  getHistory: async (draftId: string) => {
    if (useMock()) {
      return mockApi.assembly.getHistory(draftId);
    }
    const { default: assemblyApiReal } = await import('./assembly');
    return assemblyApiReal.getHistory(draftId);
  },
};

export default assemblyApi;
