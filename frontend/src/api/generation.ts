/**
 * PPT 智能生成模块 API
 * 基于联网搜索和大模型的 PPT 自动生成
 */

import apiClient from './client';
import type {
  GenerationRequest,
  GenerationResponse,
  GenerationProgress,
  TemplateListResponse,
  TaskListResponse,
  ExportResponse,
  GenerationTask,
  PPTTemplate,
} from '../types/generation';

// API 路径前缀
const API_PREFIX = '/api/v1/generation';

export const generationApi = {
  // ============== 模板管理 ==============

  /**
   * 获取模板列表
   * @param category 可选的模板分类筛选
   */
  getTemplates: async (category?: string): Promise<TemplateListResponse> => {
    return apiClient.get<TemplateListResponse>(`${API_PREFIX}/templates`, {
      params: category ? { category } : undefined,
    });
  },

  /**
   * 获取模板详情
   * @param templateId 模板ID
   */
  getTemplateDetail: async (templateId: string): Promise<PPTTemplate> => {
    return apiClient.get<PPTTemplate>(`${API_PREFIX}/templates/${templateId}`);
  },

  /**
   * 上传自定义模板
   * @param file 模板文件（.pptx）
   * @param onProgress 上传进度回调
   */
  uploadCustomTemplate: async (
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<{ template_id: string; preview_url: string; name: string }> => {
    return apiClient.upload(`${API_PREFIX}/templates/upload`, file, onProgress);
  },

  /**
   * 删除自定义模板
   * @param templateId 模板ID
   */
  deleteTemplate: async (templateId: string): Promise<{ success: boolean }> => {
    return apiClient.delete(`${API_PREFIX}/templates/${templateId}`);
  },

  // ============== 生成任务管理 ==============

  /**
   * 获取任务列表
   * @param page 页码
   * @param limit 每页数量
   * @param status 可选的状态筛选
   */
  getTasks: async (
    page = 1,
    limit = 20,
    status?: string
  ): Promise<TaskListResponse> => {
    return apiClient.get<TaskListResponse>(`${API_PREFIX}/tasks`, {
      params: { page, limit, status },
    });
  },

  /**
   * 获取任务详情
   * @param taskId 任务ID
   */
  getTaskDetail: async (taskId: string): Promise<GenerationTask> => {
    return apiClient.get<GenerationTask>(`${API_PREFIX}/tasks/${taskId}`);
  },

  /**
   * 开始生成 PPT
   * @param request 生成请求参数
   */
  startGeneration: async (request: GenerationRequest): Promise<GenerationResponse> => {
    // 如果有自定义风格文件，使用 FormData
    if (request.custom_style_file) {
      const formData = new FormData();
      formData.append('topic', request.topic);
      if (request.title) formData.append('title', request.title);
      if (request.page_count) formData.append('page_count', request.page_count.toString());
      if (request.template_id) formData.append('template_id', request.template_id);
      formData.append('include_images', request.include_images.toString());
      formData.append('include_charts', request.include_charts.toString());
      formData.append('language', request.language);
      formData.append('search_depth', request.search_depth);
      formData.append('custom_style_file', request.custom_style_file);

      return apiClient.post<GenerationResponse>(`${API_PREFIX}/tasks`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    }

    // 普通 JSON 请求
    const { custom_style_file, ...jsonRequest } = request;
    return apiClient.post<GenerationResponse>(`${API_PREFIX}/tasks`, jsonRequest);
  },

  /**
   * 获取生成进度
   * @param taskId 任务ID
   */
  getProgress: async (taskId: string): Promise<GenerationProgress> => {
    return apiClient.get<GenerationProgress>(`${API_PREFIX}/tasks/${taskId}/progress`);
  },

  /**
   * 取消生成任务
   * @param taskId 任务ID
   */
  cancelGeneration: async (taskId: string): Promise<{ success: boolean; message: string }> => {
    return apiClient.post(`${API_PREFIX}/tasks/${taskId}/cancel`);
  },

  /**
   * 删除任务
   * @param taskId 任务ID
   */
  deleteTask: async (taskId: string): Promise<{ success: boolean }> => {
    return apiClient.delete(`${API_PREFIX}/tasks/${taskId}`);
  },

  // ============== 页面操作 ==============

  /**
   * 重新生成指定页面
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param instructions 可选的重新生成指令
   */
  regeneratePage: async (
    taskId: string,
    pageIndex: number,
    instructions?: string
  ): Promise<{
    success: boolean;
    page: GenerationTask['generated_pages'][0];
    message: string;
  }> => {
    return apiClient.post(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/regenerate`, {
      instructions,
    });
  },

  /**
   * 获取页面的来源信息
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   */
  getPageSources: async (
    taskId: string,
    pageIndex: number
  ): Promise<{
    sources: GenerationTask['web_sources'];
    citations: Array<{ text: string; source_id: string }>;
  }> => {
    return apiClient.get(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/sources`);
  },

  // ============== 导出功能 ==============

  /**
   * 导出生成的 PPT
   * @param taskId 任务ID
   * @param format 导出格式
   */
  exportPPT: async (
    taskId: string,
    format: 'pptx' | 'pdf' = 'pptx'
  ): Promise<ExportResponse> => {
    return apiClient.post<ExportResponse>(`${API_PREFIX}/tasks/${taskId}/export`, {
      format,
    });
  },

  /**
   * 获取导出任务状态
   * @param exportId 导出任务ID
   */
  getExportStatus: async (exportId: string): Promise<{
    status: 'processing' | 'completed' | 'failed';
    progress: number;
    download_url?: string;
    error?: string;
  }> => {
    return apiClient.get(`${API_PREFIX}/exports/${exportId}`);
  },

  // ============== 网络搜索相关 ==============

  /**
   * 手动触发搜索更多来源
   * @param taskId 任务ID
   * @param query 可选的自定义搜索查询
   */
  searchMoreSources: async (
    taskId: string,
    query?: string
  ): Promise<{
    success: boolean;
    new_sources: GenerationTask['web_sources'];
    total_sources: number;
  }> => {
    return apiClient.post(`${API_PREFIX}/tasks/${taskId}/search`, { query });
  },

  /**
   * 移除某个来源
   * @param taskId 任务ID
   * @param sourceId 来源ID
   */
  removeSource: async (
    taskId: string,
    sourceId: string
  ): Promise<{ success: boolean }> => {
    return apiClient.delete(`${API_PREFIX}/tasks/${taskId}/sources/${sourceId}`);
  },

  // ============== 实时进度订阅 (SSE) ==============

  /**
   * 订阅生成进度（使用 Server-Sent Events）
   * @param taskId 任务ID
   * @param onProgress 进度回调
   * @param onComplete 完成回调
   * @param onError 错误回调
   * @returns 取消订阅函数
   */
  subscribeProgress: (
    taskId: string,
    onProgress: (progress: GenerationProgress) => void,
    onComplete: (task: GenerationTask) => void,
    onError: (error: string) => void
  ): (() => void) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('token');
    const url = `${baseUrl}${API_PREFIX}/tasks/${taskId}/stream${token ? `?token=${token}` : ''}`;

    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'progress') {
          onProgress(data.payload as GenerationProgress);
        } else if (data.type === 'complete') {
          onComplete(data.payload as GenerationTask);
          eventSource.close();
        } else if (data.type === 'error') {
          onError(data.payload.message);
          eventSource.close();
        }
      } catch (e) {
        console.error('Failed to parse SSE message:', e);
      }
    };

    eventSource.onerror = () => {
      onError('连接中断，请刷新页面重试');
      eventSource.close();
    };

    // 返回取消订阅函数
    return () => {
      eventSource.close();
    };
  },

  // ============== 轮询进度（备用方案） ==============

  /**
   * 轮询生成进度（当 SSE 不可用时的备用方案）
   * @param taskId 任务ID
   * @param onProgress 进度回调
   * @param onComplete 完成回调
   * @param onError 错误回调
   * @param interval 轮询间隔（毫秒）
   * @returns 取消轮询函数
   */
  pollProgress: (
    taskId: string,
    onProgress: (progress: GenerationProgress) => void,
    onComplete: (task: GenerationTask) => void,
    onError: (error: string) => void,
    interval = 1000
  ): (() => void) => {
    let isActive = true;
    let timeoutId: ReturnType<typeof setTimeout>;

    const poll = async () => {
      if (!isActive) return;

      try {
        const progress = await generationApi.getProgress(taskId);
        onProgress(progress);

        if (progress.status === 'completed') {
          const task = await generationApi.getTaskDetail(taskId);
          onComplete(task);
          return;
        }

        if (progress.status === 'failed') {
          onError(progress.message || '生成失败');
          return;
        }

        // 继续轮询
        timeoutId = setTimeout(poll, interval);
      } catch (error) {
        if (isActive) {
          onError(error instanceof Error ? error.message : '获取进度失败');
        }
      }
    };

    // 开始轮询
    poll();

    // 返回取消函数
    return () => {
      isActive = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  },
};

export default generationApi;
