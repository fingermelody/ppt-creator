/* PPT 生成模块类型定义 */

// PPT 生成任务
export interface GenerationTask {
  id: string;                       // 任务ID
  title: string;                    // PPT标题
  topic: string;                    // 主题描述
  status: GenerationStatus;         // 任务状态
  progress: number;                 // 生成进度 0-100
  template_id?: string;             // 使用的模板ID
  style_reference?: StyleReference; // 风格参考
  generated_pages: GeneratedPage[]; // 生成的页面
  web_sources: WebSource[];         // 网络来源
  total_pages: number;              // 总页数
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

// 生成状态
export type GenerationStatus = 
  | 'pending'       // 等待开始
  | 'searching'     // 正在搜索信息
  | 'analyzing'     // 分析内容
  | 'generating'    // 生成PPT
  | 'applying_style'// 应用风格
  | 'completed'     // 完成
  | 'failed';       // 失败

// 生成的页面
export interface GeneratedPage {
  id: string;
  index: number;
  title: string;
  content: PageContent;
  thumbnail?: string;
  sources: string[];                // 内容来源引用
  generated_at: string;
}

// 页面内容
export interface PageContent {
  title?: string;
  subtitle?: string;
  bullet_points?: string[];
  paragraphs?: string[];
  images?: PageImage[];
  charts?: PageChart[];
  tables?: PageTable[];
}

// 页面图片
export interface PageImage {
  id: string;
  url: string;
  alt: string;
  source?: string;
}

// 页面图表
export interface PageChart {
  id: string;
  type: 'bar' | 'line' | 'pie' | 'donut';
  title: string;
  data: any;
}

// 页面表格
export interface PageTable {
  id: string;
  headers: string[];
  rows: string[][];
}

// 网络搜索来源
export interface WebSource {
  id: string;
  title: string;
  url: string;
  snippet: string;
  relevance: number;                // 相关度 0-100
  fetched_at: string;
}

// 风格参考
export interface StyleReference {
  type: 'template' | 'custom';
  template_id?: string;             // 预设模板ID
  custom_file_path?: string;        // 自定义上传的PPT路径
  preview_url?: string;             // 预览图
}

// PPT 模板
export interface PPTTemplate {
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  preview_url: string;
  thumbnail_url: string;
  color_scheme: ColorScheme;
  font_family: string;
  is_premium: boolean;
  usage_count: number;
  created_at: string;
}

// 模板分类
export type TemplateCategory = 
  | 'business'      // 商务
  | 'education'     // 教育
  | 'technology'    // 科技
  | 'creative'      // 创意
  | 'minimalist'    // 简约
  | 'dark'          // 暗色
  | 'colorful';     // 多彩

// 配色方案
export interface ColorScheme {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  text: string;
}

// 生成请求
export interface GenerationRequest {
  topic: string;                    // 主题描述（必填，100-2000字）
  title?: string;                   // PPT标题（可选，不填则自动生成）
  page_count?: number;              // 期望页数（默认10页）
  template_id?: string;             // 模板ID
  custom_style_file?: File;         // 自定义风格文件
  include_images: boolean;          // 是否包含图片
  include_charts: boolean;          // 是否包含图表
  language: 'zh' | 'en';            // 语言
  search_depth: 'quick' | 'normal' | 'deep'; // 搜索深度
}

// 生成响应
export interface GenerationResponse {
  task_id: string;
  status: GenerationStatus;
  message: string;
  estimated_time?: number;          // 预估时间（秒）
}

// 生成进度
export interface GenerationProgress {
  task_id: string;
  status: GenerationStatus;
  progress: number;
  current_step: string;
  message: string;
  sources_found?: number;
  pages_generated?: number;
}

// 模板列表响应
export interface TemplateListResponse {
  templates: PPTTemplate[];
  total: number;
  categories: TemplateCategory[];
}

// 任务列表响应
export interface TaskListResponse {
  tasks: GenerationTask[];
  total: number;
}

// 导出响应
export interface ExportResponse {
  download_url: string;
  file_size: number;
  file_name: string;
  exported_at: string;
}

// 搜索深度选项
export const SEARCH_DEPTH_OPTIONS = [
  { value: 'quick', label: '快速搜索', description: '搜索3-5个来源，速度快' },
  { value: 'normal', label: '标准搜索', description: '搜索5-10个来源，平衡速度和质量' },
  { value: 'deep', label: '深度搜索', description: '搜索10-20个来源，内容更丰富' },
] as const;

// 页数选项
export const PAGE_COUNT_OPTIONS = [
  { value: 5, label: '5页', description: '简短介绍' },
  { value: 10, label: '10页', description: '标准演示' },
  { value: 15, label: '15页', description: '详细内容' },
  { value: 20, label: '20页', description: '完整报告' },
] as const;

// 模板分类名称映射
export const TEMPLATE_CATEGORY_NAMES: Record<TemplateCategory, string> = {
  business: '商务',
  education: '教育',
  technology: '科技',
  creative: '创意',
  minimalist: '简约',
  dark: '暗色',
  colorful: '多彩',
};
