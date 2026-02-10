/* 大纲设计相关类型定义 */

// PPT大纲
export interface PPTOutline {
  id: string;                     // 大纲唯一ID
  title: string;                  // PPT主标题
  objective: string;              // 制作目标
  target_audience?: string;       // 目标受众（可选）
  duration?: string;              // 预计演示时长（可选）
  style_template_id?: string;     // 关联的风格模板ID（可选）
  chapters: OutlineChapter[];     // 章节列表
  generation_type: 'smart' | 'wizard'; // 生成方式
  status: 'draft' | 'confirmed' | 'assembled'; // 大纲状态
  total_pages: number;            // 预计总页数
  created_at: string;
  updated_at: string;
  user_id: string;
}

// 大纲章节
export interface OutlineChapter {
  id: string;                     // 章节唯一ID
  order: number;                  // 章节顺序（从1开始）
  title: string;                  // 章节标题
  page_count: number;             // 预期页数（1-5页）
  summary: string;                // 章节内容摘要
  keywords: string[];             // 关键词标签
  source_documents?: string[];    // 指定的参考文档ID（可选）
  ai_suggestion?: string;         // AI内容建议（可选）
}

// 智能生成请求
export interface SmartGenerateRequest {
  description: string;            // 用户输入的描述文字（100-2000字）
  style_preference?: string;      // 风格偏好（可选）
}

// 智能生成响应
export interface SmartGenerateResponse {
  outline: PPTOutline;            // 生成的大纲
  confidence: number;             // 生成置信度（0-1）
  suggestions: string[];          // 优化建议
}

// 向导式生成 - 步骤1数据
export interface WizardStep1Data {
  title: string;                  // PPT标题（必填）
  objective: string;              // 制作目标（必填）
  target_audience?: string;       // 目标受众
  duration?: '5min' | '10min' | '15min' | '30min' | 'custom';
  custom_duration?: number;       // 自定义时长（分钟）
}

// 向导式生成 - 步骤2数据
export interface WizardStep2Data {
  chapters: {
    title: string;                // 章节标题（必填）
    page_count: number;           // 预期页数（1-5页）
  }[];
}

// 向导式生成 - 步骤3数据
export interface WizardStep3Data {
  chapters: {
    chapter_id: string;
    summary: string;              // 内容摘要（必填）
    keywords: string[];           // 关键词
    source_documents?: string[];  // 指定参考文档
  }[];
}

// 向导式生成 - 步骤4数据
export interface WizardStep4Data {
  style_template_id?: string;     // 选择的风格模板ID
  skip_style: boolean;            // 是否跳过风格选择
}

// 向导会话
export interface WizardSession {
  session_id: string;
  current_step: number;           // 1-4
  step1_completed: boolean;
  step2_completed: boolean;
  step3_completed: boolean;
  step4_completed: boolean;
  step1_data?: WizardStep1Data;
  step2_data?: WizardStep2Data;
  step3_data?: WizardStep3Data;
  step4_data?: WizardStep4Data;
  created_at: string;
}

// 大纲模板
export interface OutlineTemplate {
  id: string;
  name: string;                   // 模板名称
  description: string;            // 模板描述
  icon: string;                   // 图标
  category: string;               // 分类
  chapters: {
    title: string;
    suggested_page_count: number;
    sample_summary: string;
  }[];
}

// 大纲列表响应
export interface OutlineListResponse {
  outlines: PPTOutline[];
  total: number;
}

// 大纲模板列表响应
export interface TemplateListResponse {
  templates: OutlineTemplate[];
}

// 创建向导会话响应
export interface CreateSessionResponse {
  session_id: string;
  current_step: number;
  created_at: string;
}

// 保存步骤响应
export interface SaveStepResponse {
  success: boolean;
  next_step: number;
  message: string;
  chapter_ids?: string[];         // 步骤2返回
}

// 完成向导响应
export interface CompleteWizardResponse {
  outline: PPTOutline;
  message: string;
}

// 确认大纲响应
export interface ConfirmOutlineResponse {
  success: boolean;
  assembly_draft_id: string;      // 自动创建的组装草稿ID
  message: string;
}

// AI建议响应
export interface AISuggestionResponse {
  suggestion: string;             // AI建议内容
}

// 应用模板响应
export interface ApplyTemplateResponse {
  outline: PPTOutline;
}

// 生成方式类型
export type GenerationType = 'smart' | 'wizard';

// 大纲状态类型
export type OutlineStatus = 'draft' | 'confirmed' | 'assembled';

// 时长选项
export const DURATION_OPTIONS = [
  { value: '5min', label: '5分钟' },
  { value: '10min', label: '10分钟' },
  { value: '15min', label: '15分钟' },
  { value: '30min', label: '30分钟' },
  { value: 'custom', label: '自定义' },
] as const;

// 目标受众选项
export const TARGET_AUDIENCE_OPTIONS = [
  { value: 'internal_team', label: '内部团队' },
  { value: 'external_customer', label: '外部客户' },
  { value: 'investor', label: '投资人' },
  { value: 'partner', label: '合作伙伴' },
  { value: 'other', label: '其他' },
] as const;
