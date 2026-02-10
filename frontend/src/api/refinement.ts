import apiClient from './client';
import {
  TaskDetail,
  RefinedPage,
  RefinementMessage,
  RefinementSuggestion,
  QuickAction,
} from '../types/refinement';

export const refinementApi = {
  // 创建精修任务
  createTask: async (draftId: string, title?: string) => {
    return apiClient.post<{ task_id: string; total_pages: number; created_at: string }>(
      '/api/refinement/tasks',
      { draft_id: draftId, title }
    );
  },

  // 获取精修任务详情
  getTaskDetail: async (taskId: string) => {
    return apiClient.get<TaskDetail>(`/api/refinement/tasks/${taskId}`);
  },

  // 保存精修版本
  saveTask: async (taskId: string, title?: string) => {
    return apiClient.post<{ success: boolean; saved_at: string; version: string }>(
      `/api/refinement/tasks/${taskId}/save`,
      { title }
    );
  },

  // 导出精修后的PPT
  exportRefinedPPT: async (taskId: string) => {
    return apiClient.post<{ download_url: string; file_size: number; exported_at: string }>(
      `/api/refinement/tasks/${taskId}/export`
    );
  },

  // 获取页面内容
  getPageContent: async (taskId: string, pageIndex: number) => {
    return apiClient.get<RefinedPage>(`/api/refinement/tasks/${taskId}/pages/${pageIndex}/content`);
  },

  // 获取页面缩略图
  getPageThumbnail: async (taskId: string, pageIndex: number) => {
    return apiClient.get<{ image_url: string; generated_at: string }>(
      `/api/refinement/tasks/${taskId}/pages/${pageIndex}/thumbnail`
    );
  },

  // 发送对话消息
  sendMessage: async (
    taskId: string,
    pageIndex: number,
    message: string,
    selectedElement?: string,
    conversationId?: string
  ) => {
    return apiClient.post<{
      success: boolean;
      message_id: string;
      assistant_message: string;
      modification?: any;
      updated_page?: RefinedPage;
    }>(`/api/refinement/tasks/${taskId}/pages/${pageIndex}/chat`, {
      message,
      context: {
        selected_element: selectedElement,
        conversation_id: conversationId,
      },
    });
  },

  // 获取对话历史
  getChatHistory: async (taskId: string, pageIndex: number) => {
    return apiClient.get<{ conversation_id: string; messages: RefinementMessage[] }>(
      `/api/refinement/tasks/${taskId}/pages/${pageIndex}/chat/history`
    );
  },

  // 编辑文本
  editText: async (
    taskId: string,
    pageIndex: number,
    elementId: string,
    text: string,
    preserveStyle = true
  ) => {
    return apiClient.put<{ success: boolean; modification_id: string; updated_element: any }>(
      `/api/refinement/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/text`,
      { text, preserve_style: preserveStyle }
    );
  },

  // 编辑表格
  editTable: async (
    taskId: string,
    pageIndex: number,
    elementId: string,
    operation: string,
    data: any
  ) => {
    return apiClient.put<{ success: boolean; modification_id: string; updated_element: any }>(
      `/api/refinement/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/table`,
      { operation, data }
    );
  },

  // 替换图片
  replaceImage: async (
    taskId: string,
    pageIndex: number,
    elementId: string,
    imageUrl?: string,
    imageBase64?: string
  ) => {
    return apiClient.put<{ success: boolean; modification_id: string; updated_element: any }>(
      `/api/refinement/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/image`,
      { image_url: imageUrl, image_base64: imageBase64 }
    );
  },

  // 修改样式
  editStyle: async (
    taskId: string,
    pageIndex: number,
    elementId: string,
    style: Partial<{
      font_family: string;
      font_size: number;
      color: string;
      bold: boolean;
      italic: boolean;
      alignment: string;
    }>
  ) => {
    return apiClient.put<{ success: boolean; modification_id: string; updated_element: any }>(
      `/api/refinement/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/style`,
      style
    );
  },

  // 获取修改建议
  getSuggestions: async (taskId: string, pageIndex: number) => {
    return apiClient.get<{ suggestions: RefinementSuggestion[] }>(
      `/api/refinement/tasks/${taskId}/pages/${pageIndex}/suggestions`
    );
  },

  // 获取快捷操作
  getQuickActions: async (taskId: string, pageIndex: number, selectedElement?: string) => {
    return apiClient.get<{ actions: QuickAction[] }>(
      `/api/refinement/tasks/${taskId}/pages/${pageIndex}/quick-actions`,
      { params: { selected_element: selectedElement } }
    );
  },
};

export default refinementApi;
