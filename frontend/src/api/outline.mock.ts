/* 大纲设计 Mock API */

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
  OutlineTemplate,
} from '../types/outline';

// 模拟延迟
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// 生成UUID
const generateId = () => Math.random().toString(36).substring(2, 15);

// 预设大纲模板
const OUTLINE_TEMPLATES: OutlineTemplate[] = [
  {
    id: 'product_intro',
    name: '产品介绍',
    description: '适用于产品发布、功能介绍、方案推介等场景',
    icon: '🚀',
    category: '商务',
    chapters: [
      { title: '公司简介', suggested_page_count: 2, sample_summary: '公司背景、发展历程、核心团队' },
      { title: '产品概述', suggested_page_count: 3, sample_summary: '产品定位、核心功能、技术特点' },
      { title: '功能详解', suggested_page_count: 3, sample_summary: '主要功能模块、使用场景、操作演示' },
      { title: '竞争优势', suggested_page_count: 2, sample_summary: '差异化特点、性能对比、客户价值' },
      { title: '客户案例', suggested_page_count: 2, sample_summary: '典型客户、应用效果、数据对比' },
      { title: '商务合作', suggested_page_count: 1, sample_summary: '合作方式、报价方案、联系方式' },
    ],
  },
  {
    id: 'work_report',
    name: '工作汇报',
    description: '适用于周报、月报、季度总结、年度汇报等场景',
    icon: '📊',
    category: '汇报',
    chapters: [
      { title: '工作概述', suggested_page_count: 1, sample_summary: '汇报周期、主要工作内容概览' },
      { title: '完成情况', suggested_page_count: 3, sample_summary: '已完成工作、关键成果、达成目标' },
      { title: '数据分析', suggested_page_count: 2, sample_summary: '核心指标、数据对比、趋势分析' },
      { title: '问题与挑战', suggested_page_count: 2, sample_summary: '遇到的问题、解决方案、经验总结' },
      { title: '下阶段计划', suggested_page_count: 2, sample_summary: '工作目标、重点任务、时间安排' },
      { title: '资源需求', suggested_page_count: 1, sample_summary: '人力需求、资源支持、协调事项' },
    ],
  },
  {
    id: 'training_course',
    name: '培训课件',
    description: '适用于内部培训、技能培训、新员工入职培训等场景',
    icon: '📚',
    category: '培训',
    chapters: [
      { title: '课程介绍', suggested_page_count: 1, sample_summary: '培训目标、适用对象、时间安排' },
      { title: '背景知识', suggested_page_count: 2, sample_summary: '相关背景、基础概念、前置知识' },
      { title: '核心内容', suggested_page_count: 4, sample_summary: '主要知识点、详细讲解、示例说明' },
      { title: '实践演练', suggested_page_count: 2, sample_summary: '案例分析、动手练习、操作指南' },
      { title: '常见问题', suggested_page_count: 2, sample_summary: 'FAQ解答、注意事项、避坑指南' },
      { title: '总结回顾', suggested_page_count: 1, sample_summary: '知识要点、课后作业、参考资料' },
    ],
  },
  {
    id: 'project_proposal',
    name: '项目方案',
    description: '适用于项目立项、方案汇报、招投标等场景',
    icon: '📋',
    category: '方案',
    chapters: [
      { title: '项目背景', suggested_page_count: 2, sample_summary: '需求背景、问题分析、项目目标' },
      { title: '方案概述', suggested_page_count: 2, sample_summary: '整体思路、技术路线、核心优势' },
      { title: '详细设计', suggested_page_count: 4, sample_summary: '架构设计、功能规划、技术方案' },
      { title: '实施计划', suggested_page_count: 2, sample_summary: '阶段划分、时间节点、里程碑' },
      { title: '团队介绍', suggested_page_count: 1, sample_summary: '团队构成、核心成员、项目经验' },
      { title: '预算报价', suggested_page_count: 2, sample_summary: '成本估算、报价明细、付款方式' },
    ],
  },
  {
    id: 'tech_sharing',
    name: '技术分享',
    description: '适用于技术沙龙、内部分享、技术布道等场景',
    icon: '💻',
    category: '技术',
    chapters: [
      { title: '主题引入', suggested_page_count: 1, sample_summary: '分享背景、为什么关注这个话题' },
      { title: '概念介绍', suggested_page_count: 2, sample_summary: '基本概念、原理说明、发展历程' },
      { title: '技术详解', suggested_page_count: 3, sample_summary: '核心原理、实现方式、关键技术' },
      { title: '实践案例', suggested_page_count: 3, sample_summary: '应用场景、代码示例、效果展示' },
      { title: '最佳实践', suggested_page_count: 2, sample_summary: '使用建议、注意事项、常见坑点' },
      { title: '总结展望', suggested_page_count: 1, sample_summary: '核心收获、未来发展、学习资源' },
    ],
  },
];

// 模拟存储
let mockOutlines: PPTOutline[] = [];
let mockWizardSessions: Map<string, WizardSession> = new Map();

// ============================================
// 智能生成
// ============================================

/**
 * 智能生成大纲
 */
export const smartGenerate = async (
  data: SmartGenerateRequest
): Promise<SmartGenerateResponse> => {
  await delay(2000); // 模拟AI生成延迟

  // 根据描述生成大纲
  const chapters: OutlineChapter[] = [
    {
      id: generateId(),
      order: 1,
      title: '项目概述',
      page_count: 2,
      summary: '介绍项目背景、目标和整体规划',
      keywords: ['概述', '背景', '目标'],
    },
    {
      id: generateId(),
      order: 2,
      title: '核心内容',
      page_count: 3,
      summary: '详细说明核心功能和关键特性',
      keywords: ['核心', '功能', '特性'],
    },
    {
      id: generateId(),
      order: 3,
      title: '技术方案',
      page_count: 2,
      summary: '技术架构和实现方案说明',
      keywords: ['技术', '架构', '方案'],
    },
    {
      id: generateId(),
      order: 4,
      title: '实施计划',
      page_count: 2,
      summary: '项目实施时间表和里程碑',
      keywords: ['计划', '时间', '里程碑'],
    },
    {
      id: generateId(),
      order: 5,
      title: '总结展望',
      page_count: 1,
      summary: '项目总结和未来规划',
      keywords: ['总结', '展望', '规划'],
    },
  ];

  const outline: PPTOutline = {
    id: generateId(),
    title: '智能生成的PPT',
    objective: data.description.substring(0, 100),
    target_audience: '外部客户',
    duration: '15分钟',
    chapters,
    generation_type: 'smart',
    status: 'draft',
    total_pages: chapters.reduce((sum, ch) => sum + ch.page_count, 0),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 'mock-user-id',
  };

  mockOutlines.push(outline);

  return {
    outline,
    confidence: 0.92,
    suggestions: [
      '建议为"技术方案"章节补充更多关键词以提高检索准确性',
      '整体页数分配合理，结构清晰',
    ],
  };
};

// ============================================
// 向导式生成
// ============================================

/**
 * 创建向导会话
 */
export const createWizardSession = async (): Promise<CreateSessionResponse> => {
  await delay(300);

  const sessionId = generateId();
  const session: WizardSession = {
    session_id: sessionId,
    current_step: 1,
    step1_completed: false,
    step2_completed: false,
    step3_completed: false,
    step4_completed: false,
    created_at: new Date().toISOString(),
  };

  mockWizardSessions.set(sessionId, session);

  return {
    session_id: sessionId,
    current_step: 1,
    created_at: session.created_at,
  };
};

/**
 * 获取向导会话状态
 */
export const getWizardSession = async (
  sessionId: string
): Promise<WizardSession> => {
  await delay(200);

  const session = mockWizardSessions.get(sessionId);
  if (!session) {
    throw new Error('会话不存在');
  }
  return session;
};

/**
 * 保存步骤1
 */
export const saveWizardStep1 = async (
  sessionId: string,
  data: WizardStep1Data
): Promise<SaveStepResponse> => {
  await delay(300);

  const session = mockWizardSessions.get(sessionId);
  if (!session) {
    throw new Error('会话不存在');
  }

  session.step1_data = data;
  session.step1_completed = true;
  session.current_step = 2;

  return {
    success: true,
    next_step: 2,
    message: '主题设定已保存，请进行章节规划',
  };
};

/**
 * 保存步骤2
 */
export const saveWizardStep2 = async (
  sessionId: string,
  data: WizardStep2Data
): Promise<SaveStepResponse> => {
  await delay(300);

  const session = mockWizardSessions.get(sessionId);
  if (!session) {
    throw new Error('会话不存在');
  }

  session.step2_data = data;
  session.step2_completed = true;
  session.current_step = 3;

  const chapterIds = data.chapters.map(() => generateId());

  return {
    success: true,
    next_step: 3,
    message: '章节规划已保存，请填写章节内容摘要',
    chapter_ids: chapterIds,
  };
};

/**
 * 保存步骤3
 */
export const saveWizardStep3 = async (
  sessionId: string,
  data: WizardStep3Data
): Promise<SaveStepResponse> => {
  await delay(300);

  const session = mockWizardSessions.get(sessionId);
  if (!session) {
    throw new Error('会话不存在');
  }

  session.step3_data = data;
  session.step3_completed = true;
  session.current_step = 4;

  return {
    success: true,
    next_step: 4,
    message: '内容摘要已保存，可选择PPT风格或直接完成',
  };
};

/**
 * 保存步骤4
 */
export const saveWizardStep4 = async (
  sessionId: string,
  data: WizardStep4Data
): Promise<SaveStepResponse> => {
  await delay(300);

  const session = mockWizardSessions.get(sessionId);
  if (!session) {
    throw new Error('会话不存在');
  }

  session.step4_data = data;
  session.step4_completed = true;

  return {
    success: true,
    next_step: 4,
    message: '风格选择已保存',
  };
};

/**
 * 完成向导
 */
export const completeWizard = async (
  sessionId: string
): Promise<CompleteWizardResponse> => {
  await delay(500);

  const session = mockWizardSessions.get(sessionId);
  if (!session) {
    throw new Error('会话不存在');
  }

  if (!session.step1_data || !session.step2_data || !session.step3_data) {
    throw new Error('请先完成步骤1-3');
  }

  const chapters: OutlineChapter[] = session.step2_data.chapters.map((ch, index) => {
    const step3Chapter = session.step3_data!.chapters[index];
    return {
      id: step3Chapter?.chapter_id || generateId(),
      order: index + 1,
      title: ch.title,
      page_count: ch.page_count,
      summary: step3Chapter?.summary || '',
      keywords: step3Chapter?.keywords || [],
      source_documents: step3Chapter?.source_documents,
    };
  });

  const outline: PPTOutline = {
    id: generateId(),
    title: session.step1_data.title,
    objective: session.step1_data.objective,
    target_audience: session.step1_data.target_audience,
    duration: session.step1_data.duration,
    style_template_id: session.step4_data?.style_template_id,
    chapters,
    generation_type: 'wizard',
    status: 'draft',
    total_pages: chapters.reduce((sum, ch) => sum + ch.page_count, 0),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 'mock-user-id',
  };

  mockOutlines.push(outline);
  mockWizardSessions.delete(sessionId);

  return {
    outline,
    message: '大纲创建成功',
  };
};

/**
 * 获取AI内容建议
 */
export const getAISuggestion = async (
  chapterTitle: string,
  pptObjective: string
): Promise<AISuggestionResponse> => {
  await delay(1000);

  const suggestions: Record<string, string> = {
    '公司简介': '可包含公司成立时间、员工规模、融资情况、主要客户、获得荣誉等信息，建议配合时间轴展示发展历程。',
    '产品概述': '建议突出产品的差异化特点和用户价值，可以使用对比图表展示与竞品的区别。',
    '技术架构': '推荐使用架构图配合文字说明，清晰展示系统各模块间的关系和数据流向。',
    '客户案例': '建议使用具体数据和客户反馈，增加说服力。可以包含应用前后的对比数据。',
    '总结展望': '总结核心要点，展望未来发展方向，可以提出下一步的行动建议。',
  };

  return {
    suggestion: suggestions[chapterTitle] || `基于"${pptObjective}"的目标，建议本章节聚焦于"${chapterTitle}"的核心内容，突出重点，配合图表说明。`,
  };
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
  await delay(300);

  let templates = OUTLINE_TEMPLATES;
  if (category) {
    templates = templates.filter((t) => t.category === category);
  }

  return { templates };
};

/**
 * 应用模板创建大纲
 */
export const applyTemplate = async (
  templateId: string,
  data?: { title?: string; objective?: string }
): Promise<ApplyTemplateResponse> => {
  await delay(500);

  const template = OUTLINE_TEMPLATES.find((t) => t.id === templateId);
  if (!template) {
    throw new Error('模板不存在');
  }

  const chapters: OutlineChapter[] = template.chapters.map((ch, index) => ({
    id: generateId(),
    order: index + 1,
    title: ch.title,
    page_count: ch.suggested_page_count,
    summary: ch.sample_summary,
    keywords: [],
  }));

  const outline: PPTOutline = {
    id: generateId(),
    title: data?.title || `未命名${template.name}`,
    objective: data?.objective || '',
    chapters,
    generation_type: 'wizard',
    status: 'draft',
    total_pages: chapters.reduce((sum, ch) => sum + ch.page_count, 0),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    user_id: 'mock-user-id',
  };

  mockOutlines.push(outline);

  return { outline };
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
  await delay(300);

  let outlines = [...mockOutlines];
  
  if (params?.status) {
    outlines = outlines.filter((o) => o.status === params.status);
  }

  // 按更新时间倒序
  outlines.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

  const page = params?.page || 1;
  const limit = params?.limit || 20;
  const start = (page - 1) * limit;
  const end = start + limit;

  return {
    outlines: outlines.slice(start, end),
    total: outlines.length,
  };
};

/**
 * 获取大纲详情
 */
export const getOutlineDetail = async (outlineId: string): Promise<PPTOutline> => {
  await delay(200);

  const outline = mockOutlines.find((o) => o.id === outlineId);
  if (!outline) {
    throw new Error('大纲不存在');
  }
  return outline;
};

/**
 * 更新大纲
 */
export const updateOutline = async (
  outlineId: string,
  data: Partial<PPTOutline>
): Promise<{ success: boolean; updated_at: string }> => {
  await delay(300);

  const index = mockOutlines.findIndex((o) => o.id === outlineId);
  if (index === -1) {
    throw new Error('大纲不存在');
  }

  const updatedAt = new Date().toISOString();
  mockOutlines[index] = {
    ...mockOutlines[index],
    ...data,
    updated_at: updatedAt,
  };

  return { success: true, updated_at: updatedAt };
};

/**
 * 更新章节
 */
export const updateChapter = async (
  outlineId: string,
  chapterId: string,
  data: Partial<OutlineChapter>
): Promise<{ success: boolean; chapter: OutlineChapter }> => {
  await delay(300);

  const outline = mockOutlines.find((o) => o.id === outlineId);
  if (!outline) {
    throw new Error('大纲不存在');
  }

  const chapterIndex = outline.chapters.findIndex((c) => c.id === chapterId);
  if (chapterIndex === -1) {
    throw new Error('章节不存在');
  }

  outline.chapters[chapterIndex] = {
    ...outline.chapters[chapterIndex],
    ...data,
  };
  outline.updated_at = new Date().toISOString();

  return { success: true, chapter: outline.chapters[chapterIndex] };
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
  await delay(300);

  const outline = mockOutlines.find((o) => o.id === outlineId);
  if (!outline) {
    throw new Error('大纲不存在');
  }

  const newChapter: OutlineChapter = {
    id: generateId(),
    order: data.order || outline.chapters.length + 1,
    title: data.title,
    page_count: data.page_count,
    summary: data.summary,
    keywords: data.keywords || [],
  };

  outline.chapters.push(newChapter);
  outline.total_pages = outline.chapters.reduce((sum, ch) => sum + ch.page_count, 0);
  outline.updated_at = new Date().toISOString();

  return { chapter: newChapter };
};

/**
 * 删除章节
 */
export const deleteChapter = async (
  outlineId: string,
  chapterId: string
): Promise<{ success: boolean }> => {
  await delay(300);

  const outline = mockOutlines.find((o) => o.id === outlineId);
  if (!outline) {
    throw new Error('大纲不存在');
  }

  outline.chapters = outline.chapters.filter((c) => c.id !== chapterId);
  outline.chapters.forEach((c, i) => (c.order = i + 1));
  outline.total_pages = outline.chapters.reduce((sum, ch) => sum + ch.page_count, 0);
  outline.updated_at = new Date().toISOString();

  return { success: true };
};

/**
 * 调整章节顺序
 */
export const reorderChapters = async (
  outlineId: string,
  chapterOrders: { chapter_id: string; order: number }[]
): Promise<{ success: boolean }> => {
  await delay(300);

  const outline = mockOutlines.find((o) => o.id === outlineId);
  if (!outline) {
    throw new Error('大纲不存在');
  }

  chapterOrders.forEach(({ chapter_id, order }) => {
    const chapter = outline.chapters.find((c) => c.id === chapter_id);
    if (chapter) {
      chapter.order = order;
    }
  });

  outline.chapters.sort((a, b) => a.order - b.order);
  outline.updated_at = new Date().toISOString();

  return { success: true };
};

/**
 * 确认大纲
 */
export const confirmOutline = async (
  outlineId: string
): Promise<ConfirmOutlineResponse> => {
  await delay(500);

  const outline = mockOutlines.find((o) => o.id === outlineId);
  if (!outline) {
    throw new Error('大纲不存在');
  }

  outline.status = 'confirmed';
  outline.updated_at = new Date().toISOString();

  // 模拟创建组装草稿
  const assemblyDraftId = generateId();

  return {
    success: true,
    assembly_draft_id: assemblyDraftId,
    message: '大纲已确认，已创建组装草稿',
  };
};

/**
 * 删除大纲
 */
export const deleteOutline = async (
  outlineId: string
): Promise<{ success: boolean }> => {
  await delay(300);

  mockOutlines = mockOutlines.filter((o) => o.id !== outlineId);

  return { success: true };
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
  await delay(200);

  const outline = mockOutlines.find((o) => o.id === outlineId);
  if (!outline) {
    throw new Error('大纲不存在');
  }

  outline.title = data.title;
  outline.objective = data.objective;
  outline.chapters = data.chapters;
  outline.total_pages = data.chapters.reduce((sum, ch) => sum + ch.page_count, 0);
  outline.updated_at = new Date().toISOString();

  return { success: true, saved_at: outline.updated_at };
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
