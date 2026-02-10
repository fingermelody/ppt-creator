/* PPT 生成模块 Mock API */

import { mockApi } from '../mocks/api';
import type {
  GenerationRequest,
  GenerationResponse,
  GenerationProgress,
  TemplateListResponse,
  TaskListResponse,
  ExportResponse,
  GenerationTask,
  GenerationStatus,
} from '../types/generation';

// 模拟延迟
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// PPT 生成 API
export const generationApi = {
  // 获取模板列表
  getTemplates: async (category?: string): Promise<TemplateListResponse> => {
    await delay(300);
    return mockApi.generation.getTemplates(category);
  },

  // 获取任务列表
  getTasks: async (): Promise<TaskListResponse> => {
    await delay(300);
    return mockApi.generation.getTasks();
  },

  // 获取任务详情
  getTaskDetail: async (taskId: string): Promise<GenerationTask> => {
    await delay(200);
    return mockApi.generation.getTaskDetail(taskId);
  },

  // 开始生成
  startGeneration: async (request: GenerationRequest): Promise<GenerationResponse> => {
    await delay(500);
    const result = await mockApi.generation.startGeneration(request);
    return {
      ...result,
      status: result.status as GenerationStatus,
    };
  },

  // 获取生成进度
  getProgress: async (taskId: string): Promise<GenerationProgress> => {
    await delay(100);
    return mockApi.generation.getProgress(taskId);
  },

  // 取消生成
  cancelGeneration: async (taskId: string): Promise<{ success: boolean }> => {
    await delay(200);
    return mockApi.generation.cancelGeneration(taskId);
  },

  // 导出生成的PPT
  exportPPT: async (taskId: string): Promise<ExportResponse> => {
    await delay(1000);
    return mockApi.generation.exportPPT(taskId);
  },

  // 删除任务
  deleteTask: async (taskId: string): Promise<{ success: boolean }> => {
    await delay(200);
    return mockApi.generation.deleteTask(taskId);
  },

  // 重新生成指定页面
  regeneratePage: async (taskId: string, pageIndex: number): Promise<any> => {
    await delay(500);
    return mockApi.generation.regeneratePage(taskId, pageIndex);
  },

  // 上传自定义模板
  uploadCustomTemplate: async (file: File): Promise<{ template_id: string; preview_url: string }> => {
    await delay(1000);
    return {
      template_id: `custom-${Date.now()}`,
      preview_url: `https://via.placeholder.com/400x300?text=${encodeURIComponent(file.name)}`,
    };
  },

  // 模拟生成过程（轮询进度）
  pollProgress: async (
    taskId: string,
    onProgress: (progress: GenerationProgress) => void,
    onComplete: (task: GenerationTask) => void,
    _onError: (error: string) => void
  ) => {
    const steps = [
      { status: 'searching', progress: 10, message: '正在搜索相关信息...' },
      { status: 'searching', progress: 25, message: '已找到 5 个相关来源' },
      { status: 'analyzing', progress: 40, message: '正在分析内容结构...' },
      { status: 'generating', progress: 55, message: '正在生成PPT内容...' },
      { status: 'generating', progress: 70, message: '已生成 5/10 页' },
      { status: 'generating', progress: 85, message: '已生成 8/10 页' },
      { status: 'applying_style', progress: 95, message: '正在应用风格模板...' },
      { status: 'completed', progress: 100, message: '生成完成！' },
    ] as const;

    for (const step of steps) {
      await delay(800 + Math.random() * 400);
      
      onProgress({
        task_id: taskId,
        status: step.status as GenerationStatus,
        progress: step.progress,
        current_step: step.status,
        message: step.message,
        sources_found: step.progress > 20 ? 5 + Math.floor(Math.random() * 5) : undefined,
        pages_generated: step.progress > 50 ? Math.floor((step.progress - 50) / 5) : undefined,
      });

      if (step.status === 'completed') {
        const task = await mockApi.generation.getTaskDetail(taskId);
        onComplete(task);
        return;
      }
    }
  },
};

export default generationApi;
