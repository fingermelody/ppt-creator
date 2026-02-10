/* PPT 生成模块状态管理 */

import { create } from 'zustand';
import type {
  GenerationTask,
  GenerationStatus,
  GeneratedPage,
  PPTTemplate,
  WebSource,
  StyleReference,
  TemplateCategory,
} from '../types/generation';

// 生成Store状态
interface GenerationState {
  // 当前生成任务
  currentTask: GenerationTask | null;
  setCurrentTask: (task: GenerationTask | null) => void;
  updateCurrentTask: (updates: Partial<GenerationTask>) => void;
  
  // 任务列表
  tasks: GenerationTask[];
  setTasks: (tasks: GenerationTask[]) => void;
  addTask: (task: GenerationTask) => void;
  removeTask: (taskId: string) => void;
  
  // 模板列表
  templates: PPTTemplate[];
  setTemplates: (templates: PPTTemplate[]) => void;
  
  // 筛选的模板分类
  selectedCategory: TemplateCategory | 'all';
  setSelectedCategory: (category: TemplateCategory | 'all') => void;
  
  // 选中的模板
  selectedTemplate: PPTTemplate | null;
  setSelectedTemplate: (template: PPTTemplate | null) => void;
  
  // 风格参考
  styleReference: StyleReference | null;
  setStyleReference: (ref: StyleReference | null) => void;
  
  // 自定义风格文件
  customStyleFile: File | null;
  setCustomStyleFile: (file: File | null) => void;
  
  // 输入内容
  topicInput: string;
  setTopicInput: (topic: string) => void;
  
  titleInput: string;
  setTitleInput: (title: string) => void;
  
  // 生成选项
  pageCount: number;
  setPageCount: (count: number) => void;
  
  includeImages: boolean;
  setIncludeImages: (include: boolean) => void;
  
  includeCharts: boolean;
  setIncludeCharts: (include: boolean) => void;
  
  searchDepth: 'quick' | 'normal' | 'deep';
  setSearchDepth: (depth: 'quick' | 'normal' | 'deep') => void;
  
  language: 'zh' | 'en';
  setLanguage: (lang: 'zh' | 'en') => void;
  
  // 生成进度
  generationProgress: number;
  setGenerationProgress: (progress: number) => void;
  
  generationStatus: GenerationStatus;
  setGenerationStatus: (status: GenerationStatus) => void;
  
  progressMessage: string;
  setProgressMessage: (message: string) => void;
  
  // 网络搜索来源
  webSources: WebSource[];
  setWebSources: (sources: WebSource[]) => void;
  addWebSource: (source: WebSource) => void;
  
  // 生成的页面
  generatedPages: GeneratedPage[];
  setGeneratedPages: (pages: GeneratedPage[]) => void;
  addGeneratedPage: (page: GeneratedPage) => void;
  updateGeneratedPage: (pageId: string, updates: Partial<GeneratedPage>) => void;
  
  // 当前预览的页面索引
  currentPreviewIndex: number;
  setCurrentPreviewIndex: (index: number) => void;
  
  // 加载状态
  loading: boolean;
  setLoading: (loading: boolean) => void;
  
  // 生成中状态
  generating: boolean;
  setGenerating: (generating: boolean) => void;
  
  // 错误信息
  error: string | null;
  setError: (error: string | null) => void;
  
  // 显示模板选择弹窗
  showTemplateModal: boolean;
  setShowTemplateModal: (show: boolean) => void;
  
  // 显示生成进度弹窗
  showProgressModal: boolean;
  setShowProgressModal: (show: boolean) => void;
  
  // 重置生成表单
  resetForm: () => void;
  
  // 重置所有状态
  reset: () => void;
}

const initialState = {
  currentTask: null,
  tasks: [],
  templates: [],
  selectedCategory: 'all' as const,
  selectedTemplate: null,
  styleReference: null,
  customStyleFile: null,
  topicInput: '',
  titleInput: '',
  pageCount: 10,
  includeImages: true,
  includeCharts: true,
  searchDepth: 'normal' as const,
  language: 'zh' as const,
  generationProgress: 0,
  generationStatus: 'pending' as GenerationStatus,
  progressMessage: '',
  webSources: [],
  generatedPages: [],
  currentPreviewIndex: 0,
  loading: false,
  generating: false,
  error: null,
  showTemplateModal: false,
  showProgressModal: false,
};

export const useGenerationStore = create<GenerationState>((set, get) => ({
  ...initialState,
  
  // 当前任务
  setCurrentTask: (task) => set({ currentTask: task }),
  
  updateCurrentTask: (updates) => {
    const { currentTask } = get();
    if (currentTask) {
      set({ currentTask: { ...currentTask, ...updates } });
    }
  },
  
  // 任务列表
  setTasks: (tasks) => set({ tasks }),
  
  addTask: (task) => {
    const { tasks } = get();
    set({ tasks: [task, ...tasks] });
  },
  
  removeTask: (taskId) => {
    const { tasks, currentTask } = get();
    set({
      tasks: tasks.filter((t) => t.id !== taskId),
      currentTask: currentTask?.id === taskId ? null : currentTask,
    });
  },
  
  // 模板
  setTemplates: (templates) => set({ templates }),
  
  setSelectedCategory: (category) => set({ selectedCategory: category }),
  
  setSelectedTemplate: (template) => set({ 
    selectedTemplate: template,
    styleReference: template ? {
      type: 'template',
      template_id: template.id,
      preview_url: template.preview_url,
    } : null,
  }),
  
  // 风格参考
  setStyleReference: (ref) => set({ styleReference: ref }),
  
  // 自定义风格文件
  setCustomStyleFile: (file) => set({ 
    customStyleFile: file,
    styleReference: file ? {
      type: 'custom',
      custom_file_path: file.name,
    } : null,
    selectedTemplate: null,
  }),
  
  // 输入
  setTopicInput: (topic) => set({ topicInput: topic }),
  setTitleInput: (title) => set({ titleInput: title }),
  
  // 生成选项
  setPageCount: (count) => set({ pageCount: count }),
  setIncludeImages: (include) => set({ includeImages: include }),
  setIncludeCharts: (include) => set({ includeCharts: include }),
  setSearchDepth: (depth) => set({ searchDepth: depth }),
  setLanguage: (lang) => set({ language: lang }),
  
  // 进度
  setGenerationProgress: (progress) => set({ generationProgress: progress }),
  setGenerationStatus: (status) => set({ generationStatus: status }),
  setProgressMessage: (message) => set({ progressMessage: message }),
  
  // 网络来源
  setWebSources: (sources) => set({ webSources: sources }),
  addWebSource: (source) => {
    const { webSources } = get();
    set({ webSources: [...webSources, source] });
  },
  
  // 生成的页面
  setGeneratedPages: (pages) => set({ generatedPages: pages }),
  
  addGeneratedPage: (page) => {
    const { generatedPages } = get();
    set({ generatedPages: [...generatedPages, page] });
  },
  
  updateGeneratedPage: (pageId, updates) => {
    const { generatedPages } = get();
    set({
      generatedPages: generatedPages.map((p) =>
        p.id === pageId ? { ...p, ...updates } : p
      ),
    });
  },
  
  // 预览索引
  setCurrentPreviewIndex: (index) => set({ currentPreviewIndex: index }),
  
  // 加载状态
  setLoading: (loading) => set({ loading }),
  setGenerating: (generating) => set({ generating }),
  
  // 错误
  setError: (error) => set({ error }),
  
  // 弹窗
  setShowTemplateModal: (show) => set({ showTemplateModal: show }),
  setShowProgressModal: (show) => set({ showProgressModal: show }),
  
  // 重置表单
  resetForm: () => {
    set({
      topicInput: '',
      titleInput: '',
      selectedTemplate: null,
      styleReference: null,
      customStyleFile: null,
      pageCount: 10,
      includeImages: true,
      includeCharts: true,
      searchDepth: 'normal',
      error: null,
    });
  },
  
  // 重置所有
  reset: () => set(initialState),
}));
