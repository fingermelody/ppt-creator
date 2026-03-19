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
import type { PPTOutline } from '../types/outline';

// 后端草稿页面响应类型
interface BackendDraftPage {
  id: string;
  draft_id: string;
  title?: string;
  order_index: number;
  source_slide_id?: string;
  section_id?: string;
  thumbnail_path?: string;
  is_modified: number;
  created_at: string;
}

// 后端章节信息（来自大纲）
interface BackendSectionInfo {
  id: string;
  title: string;
  description?: string;
  expected_pages?: number;
  order_index: number;
}

// 后端草稿详情响应类型
interface BackendDraftDetail {
  id: string;
  title: string;
  description?: string;
  outline_id?: string;
  status: string;
  page_count: number;
  pages?: BackendDraftPage[];  // 列表查询时可能不包含 pages
  sections?: BackendSectionInfo[];  // 关联大纲的章节信息
  created_at: string;
  updated_at: string;
}

// 转换后端数据为前端格式
function convertBackendDraftToFrontend(backendDraft: BackendDraftDetail): DraftDetail {
  // 构建章节ID到章节信息的映射
  const sectionInfoMap = new Map<string, BackendSectionInfo>();
  if (backendDraft.sections) {
    backendDraft.sections.forEach(section => {
      sectionInfoMap.set(section.id, section);
    });
  }

  // 按 section_id 分组页面
  const sectionMap = new Map<string, BackendDraftPage[]>();
  const unassignedPages: BackendDraftPage[] = [];

  // 处理 pages 可能为 undefined 的情况
  const pages = backendDraft.pages || [];
  pages.forEach(page => {
    if (page.section_id) {
      const existing = sectionMap.get(page.section_id) || [];
      existing.push(page);
      sectionMap.set(page.section_id, existing);
    } else {
      unassignedPages.push(page);
    }
  });

  // 构建章节列表
  const chapters: Chapter[] = [];
  
  if (sectionMap.size === 0 && unassignedPages.length > 0) {
    // 所有页面放在一个默认章节
    chapters.push({
      id: 'default-chapter',
      title: backendDraft.title || '默认章节',
      description: backendDraft.description || '',
      required_pages: unassignedPages.length,
      page_count: unassignedPages.length,
      pages: unassignedPages.map((page, index) => ({
        slide_id: page.id,
        document_id: page.source_slide_id || '',
        document_title: page.title || `页面 ${index + 1}`,
        page_number: page.order_index + 1,
        thumbnail: page.thumbnail_path || '',
        similarity: 1,
        content_summary: page.title || '',
        order: page.order_index,
      })),
      created_at: backendDraft.created_at,
      updated_at: backendDraft.updated_at,
    });
  } else if (sectionMap.size > 0) {
    // 按章节信息的 order_index 排序
    const sortedSectionIds = Array.from(sectionMap.keys()).sort((a, b) => {
      const sectionA = sectionInfoMap.get(a);
      const sectionB = sectionInfoMap.get(b);
      return (sectionA?.order_index || 0) - (sectionB?.order_index || 0);
    });

    sortedSectionIds.forEach((sectionId) => {
      const pages = sectionMap.get(sectionId) || [];
      const sectionInfo = sectionInfoMap.get(sectionId);
      
      chapters.push({
        id: sectionId,
        title: sectionInfo?.title || `章节`,
        description: sectionInfo?.description || '',
        required_pages: sectionInfo?.expected_pages || pages.length,
        page_count: pages.length,
        pages: pages.map((page, index) => ({
          slide_id: page.id,
          document_id: page.source_slide_id || '',
          document_title: page.title || `页面 ${index + 1}`,
          page_number: page.order_index + 1,
          thumbnail: page.thumbnail_path || '',
          similarity: 1,
          content_summary: page.title || '',
          order: page.order_index,
        })),
        created_at: backendDraft.created_at,
        updated_at: backendDraft.updated_at,
      });
    });

    // 未分配的页面放入"其他"章节
    if (unassignedPages.length > 0) {
      chapters.push({
        id: 'other-chapter',
        title: '其他页面',
        description: '',
        required_pages: unassignedPages.length,
        page_count: unassignedPages.length,
        pages: unassignedPages.map((page, index) => ({
          slide_id: page.id,
          document_id: page.source_slide_id || '',
          document_title: page.title || `页面 ${index + 1}`,
          page_number: page.order_index + 1,
          thumbnail: page.thumbnail_path || '',
          similarity: 1,
          content_summary: page.title || '',
          order: page.order_index,
        })),
        created_at: backendDraft.created_at,
        updated_at: backendDraft.updated_at,
      });
    }
  } else if (backendDraft.sections && backendDraft.sections.length > 0) {
    // 有章节信息但没有页面，创建空章节
    backendDraft.sections
      .sort((a, b) => a.order_index - b.order_index)
      .forEach(section => {
        chapters.push({
          id: section.id,
          title: section.title,
          description: section.description || '',
          required_pages: section.expected_pages || 1,
          page_count: 0,
          pages: [],
          created_at: backendDraft.created_at,
          updated_at: backendDraft.updated_at,
        });
      });
  }

  const draft: AssemblyDraft = {
    id: backendDraft.id,
    title: backendDraft.title,
    description: backendDraft.description,
    chapters,
    total_pages: backendDraft.page_count,
    status: backendDraft.status === 'assembling' ? 'draft' : 
            backendDraft.status === 'generating' ? 'generating' : 'completed',
    created_at: backendDraft.created_at,
    updated_at: backendDraft.updated_at,
    version: 1,
  };

  return {
    draft,
    can_undo: false,
    can_redo: false,
  };
}

export const assemblyApi = {
  // 创建组装任务
  createDraft: async (title: string, description?: string) => {
    const response = await apiClient.post<BackendDraftDetail>('/api/drafts', {
      title,
      description,
    });
    return { draft_id: response.id, created_at: response.created_at };
  },

  // 基于大纲创建草稿（注意：这个是通过确认大纲自动创建的，这里用于兼容）
  createDraftFromOutline: async (outline: PPTOutline) => {
    const response = await apiClient.post<BackendDraftDetail>(
      '/api/drafts',
      { 
        title: outline.title, 
        description: outline.objective,
        outline_id: outline.id 
      }
    );
    const converted = convertBackendDraftToFrontend(response);
    return { 
      draft_id: response.id, 
      message: '草稿创建成功', 
      draft: converted.draft 
    };
  },

  // 获取草稿列表
  getDrafts: async (page = 1, limit = 20, status?: string, outlineId?: string) => {
    const params: any = { page, limit };
    if (status) params.status = status;
    if (outlineId) params.outline_id = outlineId;
    
    const response = await apiClient.get<{ drafts: BackendDraftDetail[], total: number }>('/api/drafts', {
      params,
    });
    return {
      drafts: response.drafts.map(d => convertBackendDraftToFrontend(d).draft),
      total: response.total,
    } as DraftListResponse;
  },

  // 根据大纲ID查找草稿
  getDraftByOutlineId: async (outlineId: string) => {
    const response = await apiClient.get<{ drafts: BackendDraftDetail[], total: number }>('/api/drafts', {
      params: { outline_id: outlineId },
    });
    if (response.drafts && response.drafts.length > 0) {
      return convertBackendDraftToFrontend(response.drafts[0]);
    }
    return null;
  },

  // 获取草稿详情
  getDraftDetail: async (draftId: string) => {
    const response = await apiClient.get<BackendDraftDetail>(`/api/drafts/${draftId}`);
    return convertBackendDraftToFrontend(response);
  },

  // 保存草稿
  saveDraft: async (draftId: string, title?: string) => {
    const response = await apiClient.put<BackendDraftDetail>(
      `/api/drafts/${draftId}`,
      { title }
    );
    return { success: true, saved_at: response.updated_at };
  },

  // 删除草稿
  deleteDraft: async (draftId: string) => {
    return apiClient.delete<{ success: boolean }>(`/api/drafts/${draftId}`);
  },

  // 导出PPT
  exportPPT: async (draftId: string, filename?: string) => {
    return apiClient.post<{ download_url: string; file_size: number; file_name: string; exported_at: string }>(
      `/api/drafts/${draftId}/export`,
      { filename, format: 'pptx' }
    );
  },

  // 预览PPT（导出并上传到 COS）
  previewPPT: async (draftId: string) => {
    return apiClient.post<{ download_url: string; file_size: number; file_name: string; exported_at: string }>(
      `/api/drafts/${draftId}/preview`
    );
  },

  // 自动匹配页面
  autoMatchPages: async (draftId: string) => {
    return apiClient.post<{
      success: boolean;
      message: string;
      matched_count: number;
      recommendations: Record<string, Array<{
        slide_id: string;
        document_id: string;
        page_number: number;
        title: string;
        content_summary: string;
        thumbnail_path: string | null;
        similarity: number;
      }>>;
    }>(`/api/assembly/drafts/${draftId}/auto-match`);
  },

  // 获取章节推荐页面
  getSectionRecommendations: async (sectionId: string, limit = 10) => {
    return apiClient.get<{
      section_id: string;
      section_title: string;
      recommendations: Array<{
        slide_id: string;
        document_id: string;
        page_number: number;
        title: string;
        content_summary: string;
        thumbnail_path: string | null;
        similarity: number;
      }>;
      total: number;
    }>(`/api/assembly/sections/${sectionId}/recommendations`, {
      params: { limit }
    });
  },

  // 添加页面（使用草稿 API）
  addPage: async (draftId: string, _chapterId: string, slideId: string, order: number) => {
    return apiClient.post<{ success: boolean; page: ChapterPage }>(
      `/api/drafts/${draftId}/pages`,
      { slide_id: slideId, position: order }
    );
  },

  // 调整页面顺序
  reorderPages: async (draftId: string, _chapterId: string, pageOrders: { slide_id: string; order: number }[]) => {
    return apiClient.post<{ success: boolean }>(
      `/api/drafts/${draftId}/pages/reorder`,
      { page_orders: pageOrders.map(p => ({ page_id: p.slide_id, order_index: p.order })) }
    );
  },

  // 删除页面
  deletePage: async (draftId: string, _chapterId: string, pageId: string) => {
    return apiClient.delete<{ success: boolean }>(
      `/api/drafts/${draftId}/pages/${pageId}`
    );
  },

  // 以下 API 后端暂未实现，先保留占位
  addChapter: async (_draftId: string, _chapter: Omit<Chapter, 'id' | 'page_count' | 'pages' | 'created_at' | 'updated_at'>) => {
    console.warn('addChapter API not implemented in backend');
    return { chapter_id: '', generated_pages: [], total_pages: 0 };
  },

  updateChapter: async (_draftId: string, _chapterId: string, _chapter: Partial<Omit<Chapter, 'id' | 'page_count' | 'pages' | 'created_at' | 'updated_at'>>) => {
    console.warn('updateChapter API not implemented in backend');
    return { chapter_id: '', generated_pages: [] };
  },

  deleteChapter: async (_draftId: string, _chapterId: string) => {
    console.warn('deleteChapter API not implemented in backend');
    return { success: true };
  },

  regenerateChapter: async (_draftId: string, _chapterId: string) => {
    console.warn('regenerateChapter API not implemented in backend');
    return { chapter_id: '', generated_pages: [] };
  },

  getAlternatives: async (_draftId: string, _chapterId: string, _slideId: string, _limit = 5) => {
    console.warn('getAlternatives API not implemented in backend');
    return { alternatives: [], total: 0 };
  },

  replacePage: async (_draftId: string, _chapterId: string, _oldSlideId: string, _request: ReplacePageRequest) => {
    console.warn('replacePage API not implemented in backend');
    return { success: true, new_page: null };
  },

  movePage: async (_draftId: string, _slideId: string, _targetChapterId: string, _targetOrder: number) => {
    console.warn('movePage API not implemented in backend');
    return { success: true };
  },

  undo: async (_draftId: string) => {
    console.warn('undo API not implemented in backend');
    return { success: false, draft: null as any, operation: '' };
  },

  redo: async (_draftId: string) => {
    console.warn('redo API not implemented in backend');
    return { success: false, draft: null as any, operation: '' };
  },

  getHistory: async (_draftId: string) => {
    console.warn('getHistory API not implemented in backend');
    return { operations: [] };
  },
};

export default assemblyApi;
