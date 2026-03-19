/* 大纲设计API接口 */

import client from './client';
import type {
  PPTOutline,
  SmartGenerateRequest,
  SmartGenerateResponse,
  WizardSession,
  WizardStep1Data,
  WizardStep2Data,
  WizardStep3Data,
  WizardStep4Data,
  OutlineListResponse,
  TemplateListResponse,
  CreateSessionResponse,
  SaveStepResponse,
  CompleteWizardResponse,
  ConfirmOutlineResponse,
  AISuggestionResponse,
  ApplyTemplateResponse,
  OutlineChapter,
} from '../types/outline';

// ============================================
// 数据转换工具函数
// ============================================

interface BackendSection {
  id: string;
  title: string;
  description?: string;
  expected_pages?: number;
  order_index?: number;
  content_hint?: string;
}

interface BackendOutline {
  id: string;
  title: string;
  description?: string;
  generation_mode?: string;
  status?: string;
  section_count?: number;
  sections?: BackendSection[];
  created_at?: string;
  updated_at?: string;
}

// 转换后端 section 为前端 chapter
function convertSectionToChapter(section: BackendSection, index: number): OutlineChapter {
  return {
    id: section.id,
    title: section.title,
    summary: section.description || '',
    page_count: section.expected_pages || 1,
    order: section.order_index !== undefined ? section.order_index + 1 : index + 1,
    keywords: [],
  };
}

// 转换后端大纲为前端格式
function convertBackendOutline(backend: BackendOutline): PPTOutline {
  const chapters = (backend.sections || []).map((s, i) => convertSectionToChapter(s, i));
  const totalPages = chapters.reduce((sum, ch) => sum + ch.page_count, 0);
  
  return {
    id: backend.id,
    title: backend.title || '未命名大纲',
    objective: backend.description || '',
    chapters,
    generation_type: backend.generation_mode === 'wizard' ? 'wizard' : 'smart',
    status: backend.status === 'completed' ? 'confirmed' : 
            backend.status === 'draft' ? 'draft' : 'draft',
    total_pages: totalPages || backend.section_count || 0,
    created_at: backend.created_at || new Date().toISOString(),
    updated_at: backend.updated_at || new Date().toISOString(),
    user_id: '',
  };
}

// 转换后端大纲列表项为前端格式（简化版，没有完整 sections）
function convertBackendOutlineListItem(backend: BackendOutline): PPTOutline {
  // 列表项没有 sections，创建空数组
  return {
    id: backend.id,
    title: backend.title || '未命名大纲',
    objective: backend.description || '',
    chapters: [],
    generation_type: backend.generation_mode === 'wizard' ? 'wizard' : 'smart',
    status: backend.status === 'completed' ? 'confirmed' : 
            backend.status === 'draft' ? 'draft' : 'draft',
    total_pages: backend.section_count || 0,
    created_at: backend.created_at || new Date().toISOString(),
    updated_at: backend.updated_at || new Date().toISOString(),
    user_id: '',
  };
}

// ============================================
// 智能生成
// ============================================

/**
 * 智能生成大纲
 */
export const smartGenerate = async (
  data: SmartGenerateRequest
): Promise<SmartGenerateResponse> => {
  // client.post 已经返回 response.data，所以直接使用返回值
  const backendResponse = await client.post('/api/outlines/smart-generate', data);
  return {
    outline: convertBackendOutline(backendResponse.outline),
    confidence: backendResponse.confidence || 0.85,
    suggestions: backendResponse.suggestions || [],
  };
};

// ============================================
// 向导式生成
// ============================================

/**
 * 创建向导会话
 */
export const createWizardSession = async (): Promise<CreateSessionResponse> => {
  return await client.post('/api/outlines/wizard/sessions');
};

/**
 * 获取向导会话状态
 */
export const getWizardSession = async (
  sessionId: string
): Promise<WizardSession> => {
  return await client.get(`/api/outlines/wizard/sessions/${sessionId}`);
};

/**
 * 保存步骤1（PPT主题设定）
 */
export const saveWizardStep1 = async (
  sessionId: string,
  data: WizardStep1Data
): Promise<SaveStepResponse> => {
  return await client.put(
    `/api/outlines/wizard/sessions/${sessionId}/step1`,
    data
  );
};

/**
 * 保存步骤2（章节规划）
 */
export const saveWizardStep2 = async (
  sessionId: string,
  data: WizardStep2Data
): Promise<SaveStepResponse> => {
  return await client.put(
    `/api/outlines/wizard/sessions/${sessionId}/step2`,
    data
  );
};

/**
 * 保存步骤3（章节内容摘要）
 */
export const saveWizardStep3 = async (
  sessionId: string,
  data: WizardStep3Data
): Promise<SaveStepResponse> => {
  return await client.put(
    `/api/outlines/wizard/sessions/${sessionId}/step3`,
    data
  );
};

/**
 * 保存步骤4（风格选择）
 */
export const saveWizardStep4 = async (
  sessionId: string,
  data: WizardStep4Data
): Promise<SaveStepResponse> => {
  return await client.put(
    `/api/outlines/wizard/sessions/${sessionId}/step4`,
    data
  );
};

/**
 * 完成向导，生成大纲
 */
export const completeWizard = async (
  sessionId: string
): Promise<CompleteWizardResponse> => {
  return await client.post(
    `/api/outlines/wizard/sessions/${sessionId}/complete`
  );
};

/**
 * 获取AI内容建议
 */
export const getAISuggestion = async (
  chapterTitle: string,
  pptObjective: string
): Promise<AISuggestionResponse> => {
  return await client.post('/api/outlines/wizard/ai-suggestion', {
    chapter_title: chapterTitle,
    ppt_objective: pptObjective,
  });
};

// ============================================
// 大纲模板
// ============================================

/**
 * 获取大纲模板列表
 * 注意：模板API在 /api/v1/generation/templates
 */
export const getTemplates = async (
  category?: string
): Promise<TemplateListResponse> => {
  const params = category ? { category } : {};
  try {
    const data = await client.get('/api/v1/generation/templates', { params });
    return data || { templates: [], total: 0, categories: [] };
  } catch (error) {
    // 模板加载失败时返回空数组，不影响主流程
    console.warn('Failed to load templates:', error);
    return { templates: [], total: 0, categories: [] };
  }
};

/**
 * 应用模板创建大纲
 */
export const applyTemplate = async (
  templateId: string,
  data?: { title?: string; objective?: string }
): Promise<ApplyTemplateResponse> => {
  return await client.post(
    `/api/outlines/templates/${templateId}/apply`,
    data || {}
  );
};

// ============================================
// 大纲管理
// ============================================

/**
 * 获取大纲列表
 */
export const getOutlines = async (params?: {
  status?: string;
  page?: number;
  limit?: number;
}): Promise<OutlineListResponse> => {
  const data = await client.get<{ outlines: BackendOutline[]; total: number }>('/api/outlines', { params });
  return {
    outlines: (data.outlines || []).map(convertBackendOutlineListItem),
    total: data.total || 0,
  };
};

/**
 * 获取大纲详情
 */
export const getOutlineDetail = async (outlineId: string): Promise<PPTOutline> => {
  const data = await client.get<BackendOutline>(`/api/outlines/${outlineId}`);
  return convertBackendOutline(data);
};

/**
 * 更新大纲
 */
export const updateOutline = async (
  outlineId: string,
  data: Partial<PPTOutline>
): Promise<{ success: boolean; updated_at: string }> => {
  return await client.put(`/api/outlines/${outlineId}`, data);
};

/**
 * 更新单个章节
 */
export const updateChapter = async (
  outlineId: string,
  chapterId: string,
  data: Partial<OutlineChapter>
): Promise<{ success: boolean; chapter: OutlineChapter }> => {
  return await client.put(
    `/api/outlines/${outlineId}/chapters/${chapterId}`,
    data
  );
};

/**
 * 添加章节
 */
export const addChapter = async (
  outlineId: string,
  data: {
    title: string;
    page_count: number;
    summary: string;
    keywords?: string[];
    order?: number;
  }
): Promise<{ chapter: OutlineChapter }> => {
  return await client.post(
    `/api/outlines/${outlineId}/chapters`,
    data
  );
};

/**
 * 删除章节
 */
export const deleteChapter = async (
  outlineId: string,
  chapterId: string
): Promise<{ success: boolean }> => {
  return await client.delete(
    `/api/outlines/${outlineId}/chapters/${chapterId}`
  );
};

/**
 * 调整章节顺序
 */
export const reorderChapters = async (
  outlineId: string,
  chapterOrders: { chapter_id: string; order: number }[]
): Promise<{ success: boolean }> => {
  return await client.put(
    `/api/outlines/${outlineId}/chapters/reorder`,
    { chapter_orders: chapterOrders }
  );
};

/**
 * 确认大纲（进入组装阶段）
 */
export const confirmOutline = async (
  outlineId: string
): Promise<ConfirmOutlineResponse> => {
  return await client.post(`/api/outlines/${outlineId}/confirm`);
};

/**
 * 删除大纲
 */
export const deleteOutline = async (
  outlineId: string
): Promise<{ success: boolean }> => {
  return await client.delete(`/api/outlines/${outlineId}`);
};

/**
 * 自动保存大纲
 */
export const autoSaveOutline = async (
  outlineId: string,
  data: {
    title: string;
    objective: string;
    chapters: OutlineChapter[];
  }
): Promise<{ success: boolean; saved_at: string }> => {
  return await client.post(
    `/api/outlines/${outlineId}/auto-save`,
    data
  );
};

export default {
  // 智能生成
  smartGenerate,
  // 向导式生成
  createWizardSession,
  getWizardSession,
  saveWizardStep1,
  saveWizardStep2,
  saveWizardStep3,
  saveWizardStep4,
  completeWizard,
  getAISuggestion,
  // 模板
  getTemplates,
  applyTemplate,
  // 大纲管理
  getOutlines,
  getOutlineDetail,
  updateOutline,
  updateChapter,
  addChapter,
  deleteChapter,
  reorderChapters,
  confirmOutline,
  deleteOutline,
  autoSaveOutline,
};
