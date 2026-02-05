import apiClient from './client';

export const exportApi = {
  // 导出文档
  exportDocument: async (documentId: string, format: 'pptx' | 'pdf' = 'pptx') => {
    return apiClient.post<{ download_url: string; file_size: number }>(
      `/api/export/documents/${documentId}`,
      { format }
    );
  },

  // 导出草稿
  exportDraft: async (draftId: string, filename?: string) => {
    return apiClient.post<{ download_url: string; file_size: number; page_count: number }>(
      `/api/export/drafts/${draftId}`,
      { filename }
    );
  },

  // 导出精修版本
  exportRefined: async (taskId: string, filename?: string) => {
    return apiClient.post<{ download_url: string; file_size: number; exported_at: string }>(
      `/api/export/refined/${taskId}`,
      { filename }
    );
  },
};

export default exportApi;
