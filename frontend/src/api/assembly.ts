import apiClient from './client';
import {
  AssemblyDraft,
  DraftListResponse,
  DraftDetail,
  Chapter,
  ChapterPage,
  AlternativeResponse,
  ReplacePageRequest,
  ReplacePageResponse,
  OperationHistory,
} from '../types/assembly';

export const assemblyApi = {
  // 创建组装任务
  createDraft: async (title: string, description?: string) => {
    return apiClient.post<{ draft_id: string; created_at: string }>('/api/assembly/drafts', {
      title,
      description,
    });
  },

  // 获取草稿列表
  getDrafts: async (page = 1, limit = 20, status?: string) => {
    return apiClient.get<DraftListResponse>('/api/assembly/drafts', {
      params: { page, limit, status },
    });
  },

  // 获取草稿详情
  getDraftDetail: async (draftId: string) => {
    return apiClient.get<DraftDetail>(`/api/assembly/drafts/${draftId}`);
  },

  // 保存草稿
  saveDraft: async (draftId: string, title?: string) => {
    return apiClient.post<{ success: boolean; saved_at: string }>(
      `/api/assembly/drafts/${draftId}/save`,
      { title }
    );
  },

  // 删除草稿
  deleteDraft: async (draftId: string) => {
    return apiClient.delete<{ success: boolean }>(`/api/assembly/drafts/${draftId}`);
  },

  // 导出PPT
  exportPPT: async (draftId: string, filename?: string) => {
    return apiClient.post<{ download_url: string; file_size: number; page_count: number }>(
      `/api/assembly/drafts/${draftId}/export`,
      { filename }
    );
  },

  // 添加章节
  addChapter: async (draftId: string, chapter: Omit<Chapter, 'id' | 'page_count' | 'pages' | 'created_at' | 'updated_at'>) => {
    return apiClient.post<{ chapter_id: string; generated_pages: ChapterPage[]; total_pages: number }>(
      `/api/assembly/drafts/${draftId}/chapters`,
      chapter
    );
  },

  // 更新章节
  updateChapter: async (
    draftId: string,
    chapterId: string,
    chapter: Partial<Omit<Chapter, 'id' | 'page_count' | 'pages' | 'created_at' | 'updated_at'>>
  ) => {
    return apiClient.put<{ chapter_id: string; generated_pages: ChapterPage[] }>(
      `/api/assembly/drafts/${draftId}/chapters/${chapterId}`,
      chapter
    );
  },

  // 删除章节
  deleteChapter: async (draftId: string, chapterId: string) => {
    return apiClient.delete<{ success: boolean }>(
      `/api/assembly/drafts/${draftId}/chapters/${chapterId}`
    );
  },

  // 重新生成章节
  regenerateChapter: async (draftId: string, chapterId: string) => {
    return apiClient.post<{ chapter_id: string; generated_pages: ChapterPage[] }>(
      `/api/assembly/drafts/${draftId}/chapters/${chapterId}/regenerate`
    );
  },

  // 获取备选页面
  getAlternatives: async (draftId: string, chapterId: string, slideId: string, limit = 5) => {
    return apiClient.get<AlternativeResponse>(
      `/api/assembly/drafts/${draftId}/chapters/${chapterId}/pages/${slideId}/alternatives`,
      { params: { limit } }
    );
  },

  // 替换页面
  replacePage: async (draftId: string, chapterId: string, oldSlideId: string, request: ReplacePageRequest) => {
    return apiClient.put<ReplacePageResponse>(
      `/api/assembly/drafts/${draftId}/chapters/${chapterId}/pages/${oldSlideId}/replace`,
      request
    );
  },

  // 删除页面
  deletePage: async (draftId: string, chapterId: string, slideId: string) => {
    return apiClient.delete<{ success: boolean }>(
      `/api/assembly/drafts/${draftId}/chapters/${chapterId}/pages/${slideId}`
    );
  },

  // 添加页面
  addPage: async (draftId: string, chapterId: string, slideId: string, order: number) => {
    return apiClient.post<{ success: boolean; page: ChapterPage }>(
      `/api/assembly/drafts/${draftId}/chapters/${chapterId}/pages`,
      { slide_id: slideId, order }
    );
  },

  // 调整页面顺序
  reorderPages: async (draftId: string, chapterId: string, pageOrders: { slide_id: string; order: number }[]) => {
    return apiClient.put<{ success: boolean }>(
      `/api/assembly/drafts/${draftId}/chapters/${chapterId}/pages/reorder`,
      { page_orders: pageOrders }
    );
  },

  // 跨章节移动页面
  movePage: async (
    draftId: string,
    slideId: string,
    targetChapterId: string,
    targetOrder: number
  ) => {
    return apiClient.put<{ success: boolean }>(`/api/assembly/drafts/${draftId}/pages/${slideId}/move`, {
      target_chapter_id: targetChapterId,
      target_order: targetOrder,
    });
  },

  // 撤销操作
  undo: async (draftId: string) => {
    return apiClient.post<{ success: boolean; draft: AssemblyDraft; operation: string }>(
      `/api/assembly/drafts/${draftId}/undo`
    );
  },

  // 重做操作
  redo: async (draftId: string) => {
    return apiClient.post<{ success: boolean; draft: AssemblyDraft; operation: string }>(
      `/api/assembly/drafts/${draftId}/redo`
    );
  },

  // 获取操作历史
  getHistory: async (draftId: string) => {
    return apiClient.get<OperationHistory>(`/api/assembly/drafts/${draftId}/history`);
  },
};

export default assemblyApi;
