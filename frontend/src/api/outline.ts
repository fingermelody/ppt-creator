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
// 智能生成
// ============================================

/**
 * 智能生成大纲
 */
export const smartGenerate = async (
  data: SmartGenerateRequest
): Promise<SmartGenerateResponse> => {
  const response = await client.post('/api/outlines/smart-generate', data);
  return response.data;
};

// ============================================
// 向导式生成
// ============================================

/**
 * 创建向导会话
 */
export const createWizardSession = async (): Promise<CreateSessionResponse> => {
  const response = await client.post('/api/outlines/wizard/sessions');
  return response.data;
};

/**
 * 获取向导会话状态
 */
export const getWizardSession = async (
  sessionId: string
): Promise<WizardSession> => {
  const response = await client.get(`/api/outlines/wizard/sessions/${sessionId}`);
  return response.data;
};

/**
 * 保存步骤1（PPT主题设定）
 */
export const saveWizardStep1 = async (
  sessionId: string,
  data: WizardStep1Data
): Promise<SaveStepResponse> => {
  const response = await client.put(
    `/api/outlines/wizard/sessions/${sessionId}/step1`,
    data
  );
  return response.data;
};

/**
 * 保存步骤2（章节规划）
 */
export const saveWizardStep2 = async (
  sessionId: string,
  data: WizardStep2Data
): Promise<SaveStepResponse> => {
  const response = await client.put(
    `/api/outlines/wizard/sessions/${sessionId}/step2`,
    data
  );
  return response.data;
};

/**
 * 保存步骤3（章节内容摘要）
 */
export const saveWizardStep3 = async (
  sessionId: string,
  data: WizardStep3Data
): Promise<SaveStepResponse> => {
  const response = await client.put(
    `/api/outlines/wizard/sessions/${sessionId}/step3`,
    data
  );
  return response.data;
};

/**
 * 保存步骤4（风格选择）
 */
export const saveWizardStep4 = async (
  sessionId: string,
  data: WizardStep4Data
): Promise<SaveStepResponse> => {
  const response = await client.put(
    `/api/outlines/wizard/sessions/${sessionId}/step4`,
    data
  );
  return response.data;
};

/**
 * 完成向导，生成大纲
 */
export const completeWizard = async (
  sessionId: string
): Promise<CompleteWizardResponse> => {
  const response = await client.post(
    `/api/outlines/wizard/sessions/${sessionId}/complete`
  );
  return response.data;
};

/**
 * 获取AI内容建议
 */
export const getAISuggestion = async (
  chapterTitle: string,
  pptObjective: string
): Promise<AISuggestionResponse> => {
  const response = await client.post('/api/outlines/wizard/ai-suggestion', {
    chapter_title: chapterTitle,
    ppt_objective: pptObjective,
  });
  return response.data;
};

// ============================================
// 大纲模板
// ============================================

/**
 * 获取大纲模板列表
 */
export const getTemplates = async (
  category?: string
): Promise<TemplateListResponse> => {
  const params = category ? { category } : {};
  const response = await client.get('/api/outlines/templates', { params });
  return response.data;
};

/**
 * 应用模板创建大纲
 */
export const applyTemplate = async (
  templateId: string,
  data?: { title?: string; objective?: string }
): Promise<ApplyTemplateResponse> => {
  const response = await client.post(
    `/api/outlines/templates/${templateId}/apply`,
    data || {}
  );
  return response.data;
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
  const response = await client.get('/api/outlines', { params });
  return response.data;
};

/**
 * 获取大纲详情
 */
export const getOutlineDetail = async (outlineId: string): Promise<PPTOutline> => {
  const response = await client.get(`/api/outlines/${outlineId}`);
  return response.data;
};

/**
 * 更新大纲
 */
export const updateOutline = async (
  outlineId: string,
  data: Partial<PPTOutline>
): Promise<{ success: boolean; updated_at: string }> => {
  const response = await client.put(`/api/outlines/${outlineId}`, data);
  return response.data;
};

/**
 * 更新单个章节
 */
export const updateChapter = async (
  outlineId: string,
  chapterId: string,
  data: Partial<OutlineChapter>
): Promise<{ success: boolean; chapter: OutlineChapter }> => {
  const response = await client.put(
    `/api/outlines/${outlineId}/chapters/${chapterId}`,
    data
  );
  return response.data;
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
  const response = await client.post(
    `/api/outlines/${outlineId}/chapters`,
    data
  );
  return response.data;
};

/**
 * 删除章节
 */
export const deleteChapter = async (
  outlineId: string,
  chapterId: string
): Promise<{ success: boolean }> => {
  const response = await client.delete(
    `/api/outlines/${outlineId}/chapters/${chapterId}`
  );
  return response.data;
};

/**
 * 调整章节顺序
 */
export const reorderChapters = async (
  outlineId: string,
  chapterOrders: { chapter_id: string; order: number }[]
): Promise<{ success: boolean }> => {
  const response = await client.put(
    `/api/outlines/${outlineId}/chapters/reorder`,
    { chapter_orders: chapterOrders }
  );
  return response.data;
};

/**
 * 确认大纲（进入组装阶段）
 */
export const confirmOutline = async (
  outlineId: string
): Promise<ConfirmOutlineResponse> => {
  const response = await client.post(`/api/outlines/${outlineId}/confirm`);
  return response.data;
};

/**
 * 删除大纲
 */
export const deleteOutline = async (
  outlineId: string
): Promise<{ success: boolean }> => {
  const response = await client.delete(`/api/outlines/${outlineId}`);
  return response.data;
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
  const response = await client.post(
    `/api/outlines/${outlineId}/auto-save`,
    data
  );
  return response.data;
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
