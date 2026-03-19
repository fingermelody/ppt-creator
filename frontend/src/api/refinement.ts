import apiClient from './client';
import {
  TaskDetail,
  RefinedPage,
  RefinementMessage,
  RefinementSuggestion,
  QuickAction,
} from '../types/refinement';

// API 路径前缀
const API_PREFIX = '/api/refinement';

// 精修任务列表项类型
interface RefinementTaskListItem {
  id: string;
  title: string;
  draft_id: string;
  status: 'editing' | 'saved' | 'exported';
  page_count: number;
  modification_count: number;
  created_at: string;
  updated_at: string;
}

// 精修任务列表响应类型
interface RefinementTaskListResponse {
  tasks: RefinementTaskListItem[];
  total: number;
  page: number;
  page_size: number;
}

// 修改历史记录类型
interface ModificationHistory {
  id: string;
  page_index: number;
  element_id?: string;
  action: 'edit_text' | 'edit_style' | 'edit_table' | 'replace_image' | 'move' | 'delete' | 'add';
  before_state: any;
  after_state: any;
  created_at: string;
}

// 撤销/重做响应类型
interface UndoRedoResponse {
  success: boolean;
  current_step: number;
  total_steps: number;
  updated_page: RefinedPage;
  can_undo: boolean;
  can_redo: boolean;
}

// SSE 消息类型
interface SSEMessage {
  type: 'thinking' | 'delta' | 'modification' | 'complete' | 'error';
  payload: any;
}

export const refinementApi = {
  // 获取精修任务列表
  getTasks: async (page = 1, pageSize = 20, status?: string) => {
    return apiClient.get<RefinementTaskListResponse>(`${API_PREFIX}/tasks`, {
      params: { page, page_size: pageSize, status },
    });
  },

  // 创建精修任务
  createTask: async (draftId: string, title?: string) => {
    return apiClient.post<{ task_id: string; total_pages: number; created_at: string }>(
      `${API_PREFIX}/tasks`,
      { draft_id: draftId, title }
    );
  },

  // 获取精修任务详情
  getTaskDetail: async (taskId: string) => {
    return apiClient.get<TaskDetail>(`${API_PREFIX}/tasks/${taskId}`);
  },

  // 保存精修版本
  saveTask: async (taskId: string, title?: string) => {
    return apiClient.post<{ success: boolean; saved_at: string; version: string }>(
      `${API_PREFIX}/tasks/${taskId}/save`,
      { title }
    );
  },

  // 导出精修后的PPT
  exportRefinedPPT: async (taskId: string) => {
    return apiClient.post<{ download_url: string; file_size: number; exported_at: string }>(
      `${API_PREFIX}/tasks/${taskId}/export`
    );
  },

  // 获取页面内容
  getPageContent: async (taskId: string, pageIndex: number) => {
    return apiClient.get<RefinedPage>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/content`);
  },

  // 获取页面缩略图
  getPageThumbnail: async (taskId: string, pageIndex: number) => {
    return apiClient.get<{ image_url: string; generated_at: string }>(
      `${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/thumbnail`
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
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/chat`, {
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
      `${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/chat/history`
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
      `${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/text`,
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
      `${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/table`,
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
      `${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/image`,
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
      `${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/style`,
      style
    );
  },

  // 获取修改建议
  getSuggestions: async (taskId: string, pageIndex: number) => {
    return apiClient.get<{ suggestions: RefinementSuggestion[] }>(
      `${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/suggestions`
    );
  },

  // 获取快捷操作
  getQuickActions: async (taskId: string, pageIndex: number, selectedElement?: string) => {
    return apiClient.get<{ actions: QuickAction[] }>(
      `${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/quick-actions`,
      { params: { selected_element: selectedElement } }
    );
  },

  // ============== 新增：元素位置操作 ==============

  /**
   * 移动元素位置
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param elementId 元素ID
   * @param position 新位置 { x, y, width?, height? }
   */
  moveElement: async (
    taskId: string,
    pageIndex: number,
    elementId: string,
    position: { x: number; y: number; width?: number; height?: number }
  ) => {
    return apiClient.put<{
      success: boolean;
      modification_id: string;
      updated_element: any;
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/position`, position);
  },

  /**
   * 调整元素大小
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param elementId 元素ID
   * @param size 新尺寸 { width, height }
   */
  resizeElement: async (
    taskId: string,
    pageIndex: number,
    elementId: string,
    size: { width: number; height: number }
  ) => {
    return apiClient.put<{
      success: boolean;
      modification_id: string;
      updated_element: any;
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/size`, size);
  },

  /**
   * 删除元素
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param elementId 元素ID
   */
  deleteElement: async (taskId: string, pageIndex: number, elementId: string) => {
    return apiClient.delete<{
      success: boolean;
      modification_id: string;
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}`);
  },

  /**
   * 添加新元素
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param element 元素数据
   */
  addElement: async (
    taskId: string,
    pageIndex: number,
    element: {
      type: 'text' | 'image' | 'shape' | 'chart' | 'table';
      position: { x: number; y: number; width: number; height: number };
      content: any;
      style?: any;
    }
  ) => {
    return apiClient.post<{
      success: boolean;
      element_id: string;
      modification_id: string;
      created_element: any;
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements`, element);
  },

  /**
   * 复制元素
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param elementId 要复制的元素ID
   * @param offset 偏移位置
   */
  duplicateElement: async (
    taskId: string,
    pageIndex: number,
    elementId: string,
    offset?: { x: number; y: number }
  ) => {
    return apiClient.post<{
      success: boolean;
      new_element_id: string;
      modification_id: string;
      created_element: any;
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/duplicate`, {
      offset: offset || { x: 20, y: 20 },
    });
  },

  /**
   * 调整元素层级
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param elementId 元素ID
   * @param action 层级操作
   */
  changeElementOrder: async (
    taskId: string,
    pageIndex: number,
    elementId: string,
    action: 'bring_to_front' | 'send_to_back' | 'bring_forward' | 'send_backward'
  ) => {
    return apiClient.put<{
      success: boolean;
      modification_id: string;
      new_z_index: number;
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/${elementId}/order`, { action });
  },

  // ============== 新增：撤销/重做功能 ==============

  /**
   * 获取修改历史
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   */
  getModificationHistory: async (taskId: string, pageIndex: number) => {
    return apiClient.get<{
      history: ModificationHistory[];
      current_step: number;
      total_steps: number;
      can_undo: boolean;
      can_redo: boolean;
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/history`);
  },

  /**
   * 撤销上一步操作
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   */
  undo: async (taskId: string, pageIndex: number): Promise<UndoRedoResponse> => {
    return apiClient.post(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/undo`);
  },

  /**
   * 重做上一步撤销的操作
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   */
  redo: async (taskId: string, pageIndex: number): Promise<UndoRedoResponse> => {
    return apiClient.post(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/redo`);
  },

  /**
   * 跳转到指定历史步骤
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param step 目标步骤索引
   */
  goToHistoryStep: async (
    taskId: string,
    pageIndex: number,
    step: number
  ): Promise<UndoRedoResponse> => {
    return apiClient.post(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/history/goto`, {
      step,
    });
  },

  /**
   * 清除修改历史（保留当前状态）
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   */
  clearHistory: async (taskId: string, pageIndex: number) => {
    return apiClient.delete<{ success: boolean }>(
      `${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/history`
    );
  },

  // ============== 新增：SSE 流式对话 ==============

  /**
   * 流式发送对话消息（使用 Server-Sent Events）
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param message 用户消息
   * @param selectedElement 选中的元素ID
   * @param callbacks 回调函数
   * @returns 取消订阅函数
   */
  streamChat: (
    taskId: string,
    pageIndex: number,
    message: string,
    selectedElement: string | undefined,
    callbacks: {
      onThinking?: () => void;
      onDelta?: (text: string) => void;
      onModification?: (modification: any) => void;
      onComplete?: (response: {
        message_id: string;
        assistant_message: string;
        modification?: any;
        updated_page?: RefinedPage;
      }) => void;
      onError?: (error: string) => void;
    }
  ): (() => void) => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('token');

    // 构建 URL 参数
    const params = new URLSearchParams({
      message,
      ...(selectedElement && { selected_element: selectedElement }),
      ...(token && { token }),
    });

    const url = `${baseUrl}${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/chat/stream?${params}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      try {
        const data: SSEMessage = JSON.parse(event.data);

        switch (data.type) {
          case 'thinking':
            callbacks.onThinking?.();
            break;
          case 'delta':
            callbacks.onDelta?.(data.payload.text);
            break;
          case 'modification':
            callbacks.onModification?.(data.payload);
            break;
          case 'complete':
            callbacks.onComplete?.(data.payload);
            eventSource.close();
            break;
          case 'error':
            callbacks.onError?.(data.payload.message);
            eventSource.close();
            break;
        }
      } catch (e) {
        console.error('Failed to parse SSE message:', e);
      }
    };

    eventSource.onerror = () => {
      callbacks.onError?.('连接中断，请重试');
      eventSource.close();
    };

    // 返回取消函数
    return () => {
      eventSource.close();
    };
  },

  /**
   * 使用 fetch API 进行流式对话（支持 POST 请求）
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param message 用户消息
   * @param selectedElement 选中的元素ID
   * @param callbacks 回调函数
   * @returns 取消控制器
   */
  streamChatPost: async (
    taskId: string,
    pageIndex: number,
    message: string,
    selectedElement: string | undefined,
    callbacks: {
      onThinking?: () => void;
      onDelta?: (text: string) => void;
      onModification?: (modification: any) => void;
      onComplete?: (response: any) => void;
      onError?: (error: string) => void;
    }
  ): Promise<AbortController> => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('token');
    const controller = new AbortController();

    try {
      const response = await fetch(
        `${baseUrl}${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/chat/stream`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify({
            message,
            context: { selected_element: selectedElement },
          }),
          signal: controller.signal,
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data: SSEMessage = JSON.parse(line.slice(6));

              switch (data.type) {
                case 'thinking':
                  callbacks.onThinking?.();
                  break;
                case 'delta':
                  callbacks.onDelta?.(data.payload.text);
                  break;
                case 'modification':
                  callbacks.onModification?.(data.payload);
                  break;
                case 'complete':
                  callbacks.onComplete?.(data.payload);
                  break;
                case 'error':
                  callbacks.onError?.(data.payload.message);
                  break;
              }
            } catch (e) {
              console.error('Failed to parse SSE line:', e);
            }
          }
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        callbacks.onError?.(error instanceof Error ? error.message : '请求失败');
      }
    }

    return controller;
  },

  // ============== 新增：批量操作 ==============

  /**
   * 批量删除元素
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param elementIds 元素ID列表
   */
  batchDeleteElements: async (taskId: string, pageIndex: number, elementIds: string[]) => {
    return apiClient.post<{
      success: boolean;
      modification_id: string;
      deleted_count: number;
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/batch-delete`, {
      element_ids: elementIds,
    });
  },

  /**
   * 批量修改样式
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param elementIds 元素ID列表
   * @param style 样式
   */
  batchEditStyle: async (
    taskId: string,
    pageIndex: number,
    elementIds: string[],
    style: Partial<{
      font_family: string;
      font_size: number;
      color: string;
      bold: boolean;
      italic: boolean;
      alignment: string;
    }>
  ) => {
    return apiClient.put<{
      success: boolean;
      modification_id: string;
      updated_count: number;
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/batch-style`, {
      element_ids: elementIds,
      style,
    });
  },

  /**
   * 对齐多个元素
   * @param taskId 任务ID
   * @param pageIndex 页面索引
   * @param elementIds 元素ID列表
   * @param alignment 对齐方式
   */
  alignElements: async (
    taskId: string,
    pageIndex: number,
    elementIds: string[],
    alignment: 'left' | 'center' | 'right' | 'top' | 'middle' | 'bottom' | 'distribute_h' | 'distribute_v'
  ) => {
    return apiClient.post<{
      success: boolean;
      modification_id: string;
      updated_elements: any[];
    }>(`${API_PREFIX}/tasks/${taskId}/pages/${pageIndex}/elements/align`, {
      element_ids: elementIds,
      alignment,
    });
  },
};

export default refinementApi;

// 导出类型供外部使用
export type { ModificationHistory, UndoRedoResponse, SSEMessage, RefinementTaskListItem, RefinementTaskListResponse };
