/* 大纲设计状态管理 */

import { create } from 'zustand';
import type {
  PPTOutline,
  OutlineChapter,
  WizardSession,
  WizardStep1Data,
  WizardStep2Data,
  WizardStep3Data,
  WizardStep4Data,
  OutlineTemplate,
  GenerationType,
} from '../types/outline';

// 向导步骤信息
export interface WizardStepInfo {
  step: number;
  title: string;
  description: string;
  completed: boolean;
}

// 大纲Store状态
interface OutlineState {
  // 当前大纲
  currentOutline: PPTOutline | null;
  setCurrentOutline: (outline: PPTOutline | null) => void;
  updateCurrentOutline: (updates: Partial<PPTOutline>) => void;
  
  // 大纲列表
  outlines: PPTOutline[];
  setOutlines: (outlines: PPTOutline[]) => void;
  addOutline: (outline: PPTOutline) => void;
  removeOutline: (outlineId: string) => void;
  
  // 章节操作
  updateChapter: (chapterId: string, updates: Partial<OutlineChapter>) => void;
  addChapter: (chapter: OutlineChapter) => void;
  removeChapter: (chapterId: string) => void;
  reorderChapters: (startIndex: number, endIndex: number) => void;
  
  // 生成模式
  generationType: GenerationType;
  setGenerationType: (type: GenerationType) => void;
  
  // 向导会话
  wizardSession: WizardSession | null;
  setWizardSession: (session: WizardSession | null) => void;
  
  // 向导步骤数据
  step1Data: WizardStep1Data | null;
  setStep1Data: (data: WizardStep1Data | null) => void;
  
  step2Data: WizardStep2Data | null;
  setStep2Data: (data: WizardStep2Data | null) => void;
  
  step3Data: WizardStep3Data | null;
  setStep3Data: (data: WizardStep3Data | null) => void;
  
  step4Data: WizardStep4Data | null;
  setStep4Data: (data: WizardStep4Data | null) => void;
  
  // 当前步骤
  currentStep: number;
  setCurrentStep: (step: number) => void;
  nextStep: () => void;
  prevStep: () => void;
  
  // 获取步骤信息
  getStepsInfo: () => WizardStepInfo[];
  
  // 模板
  templates: OutlineTemplate[];
  setTemplates: (templates: OutlineTemplate[]) => void;
  
  // 智能生成描述
  smartDescription: string;
  setSmartDescription: (description: string) => void;
  
  // 加载状态
  loading: boolean;
  setLoading: (loading: boolean) => void;
  
  // 生成中状态
  generating: boolean;
  setGenerating: (generating: boolean) => void;
  
  // 错误信息
  error: string | null;
  setError: (error: string | null) => void;
  
  // 自动保存定时器ID
  autoSaveTimerId: ReturnType<typeof setTimeout> | null;
  setAutoSaveTimerId: (timerId: ReturnType<typeof setTimeout> | null) => void;
  
  // 是否有未保存的更改
  hasUnsavedChanges: boolean;
  setHasUnsavedChanges: (hasChanges: boolean) => void;
  
  // 重置向导状态
  resetWizard: () => void;
  
  // 重置所有状态
  reset: () => void;
}

const initialState = {
  currentOutline: null,
  outlines: [],
  generationType: 'smart' as GenerationType,
  wizardSession: null,
  step1Data: null,
  step2Data: null,
  step3Data: null,
  step4Data: null,
  currentStep: 1,
  templates: [],
  smartDescription: '',
  loading: false,
  generating: false,
  error: null,
  autoSaveTimerId: null,
  hasUnsavedChanges: false,
};

export const useOutlineStore = create<OutlineState>((set, get) => ({
  ...initialState,
  
  // 当前大纲
  setCurrentOutline: (outline) => set({ currentOutline: outline }),
  
  updateCurrentOutline: (updates) => {
    const { currentOutline } = get();
    if (currentOutline) {
      set({
        currentOutline: { ...currentOutline, ...updates },
        hasUnsavedChanges: true,
      });
    }
  },
  
  // 大纲列表
  setOutlines: (outlines) => set({ outlines }),
  
  addOutline: (outline) => {
    const { outlines } = get();
    set({ outlines: [outline, ...outlines] });
  },
  
  removeOutline: (outlineId) => {
    const { outlines, currentOutline } = get();
    set({
      outlines: outlines.filter((o) => o.id !== outlineId),
      currentOutline: currentOutline?.id === outlineId ? null : currentOutline,
    });
  },
  
  // 章节操作
  updateChapter: (chapterId, updates) => {
    const { currentOutline } = get();
    if (currentOutline) {
      const chapters = currentOutline.chapters.map((ch) =>
        ch.id === chapterId ? { ...ch, ...updates } : ch
      );
      const totalPages = chapters.reduce((sum, ch) => sum + ch.page_count, 0);
      set({
        currentOutline: { ...currentOutline, chapters, total_pages: totalPages },
        hasUnsavedChanges: true,
      });
    }
  },
  
  addChapter: (chapter) => {
    const { currentOutline } = get();
    if (currentOutline) {
      const chapters = [...currentOutline.chapters, chapter];
      const totalPages = chapters.reduce((sum, ch) => sum + ch.page_count, 0);
      set({
        currentOutline: { ...currentOutline, chapters, total_pages: totalPages },
        hasUnsavedChanges: true,
      });
    }
  },
  
  removeChapter: (chapterId) => {
    const { currentOutline } = get();
    if (currentOutline) {
      const chapters = currentOutline.chapters
        .filter((ch) => ch.id !== chapterId)
        .map((ch, index) => ({ ...ch, order: index + 1 }));
      const totalPages = chapters.reduce((sum, ch) => sum + ch.page_count, 0);
      set({
        currentOutline: { ...currentOutline, chapters, total_pages: totalPages },
        hasUnsavedChanges: true,
      });
    }
  },
  
  reorderChapters: (startIndex, endIndex) => {
    const { currentOutline } = get();
    if (currentOutline) {
      const chapters = [...currentOutline.chapters];
      const [removed] = chapters.splice(startIndex, 1);
      chapters.splice(endIndex, 0, removed);
      
      // 更新顺序
      const reorderedChapters = chapters.map((ch, index) => ({
        ...ch,
        order: index + 1,
      }));
      
      set({
        currentOutline: { ...currentOutline, chapters: reorderedChapters },
        hasUnsavedChanges: true,
      });
    }
  },
  
  // 生成模式
  setGenerationType: (type) => set({ generationType: type }),
  
  // 向导会话
  setWizardSession: (session) => set({ wizardSession: session }),
  
  // 向导步骤数据
  setStep1Data: (data) => set({ step1Data: data }),
  setStep2Data: (data) => set({ step2Data: data }),
  setStep3Data: (data) => set({ step3Data: data }),
  setStep4Data: (data) => set({ step4Data: data }),
  
  // 当前步骤
  setCurrentStep: (step) => set({ currentStep: step }),
  
  nextStep: () => {
    const { currentStep } = get();
    if (currentStep < 4) {
      set({ currentStep: currentStep + 1 });
    }
  },
  
  prevStep: () => {
    const { currentStep } = get();
    if (currentStep > 1) {
      set({ currentStep: currentStep - 1 });
    }
  },
  
  // 获取步骤信息
  getStepsInfo: () => {
    const { step1Data, step2Data, step3Data, step4Data } = get();
    return [
      {
        step: 1,
        title: '主题设定',
        description: 'PPT标题和目标',
        completed: !!step1Data,
      },
      {
        step: 2,
        title: '章节规划',
        description: '添加和编辑章节',
        completed: !!step2Data,
      },
      {
        step: 3,
        title: '内容摘要',
        description: '填写章节内容',
        completed: !!step3Data,
      },
      {
        step: 4,
        title: '风格选择',
        description: '选择PPT风格',
        completed: !!step4Data,
      },
    ];
  },
  
  // 模板
  setTemplates: (templates) => set({ templates }),
  
  // 智能生成描述
  setSmartDescription: (description) => set({ smartDescription: description }),
  
  // 加载状态
  setLoading: (loading) => set({ loading }),
  
  // 生成中状态
  setGenerating: (generating) => set({ generating }),
  
  // 错误信息
  setError: (error) => set({ error }),
  
  // 自动保存定时器
  setAutoSaveTimerId: (timerId) => set({ autoSaveTimerId: timerId }),
  
  // 未保存更改
  setHasUnsavedChanges: (hasChanges) => set({ hasUnsavedChanges: hasChanges }),
  
  // 重置向导状态
  resetWizard: () => {
    set({
      wizardSession: null,
      step1Data: null,
      step2Data: null,
      step3Data: null,
      step4Data: null,
      currentStep: 1,
    });
  },
  
  // 重置所有状态
  reset: () => {
    const { autoSaveTimerId } = get();
    if (autoSaveTimerId) {
      clearTimeout(autoSaveTimerId);
    }
    set(initialState);
  },
}));
