import apiClient from './client';
import {
  UploadInitResponse,
  UploadCompleteRequest,
  DocumentListParams,
  DocumentListResponse,
  Document,
  Slide,
  PreviewResponse,
} from '../types/document';

// 获取 API 基础 URL
const getBaseUrl = () => {
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
};

export const documentsApi = {
  // 初始化上传
  initUpload: async (filename: string, filesize: number, totalChunks: number) => {
    return apiClient.post<UploadInitResponse>('/api/documents/upload/init', {
      filename,
      filesize,
      total_chunks: totalChunks,
    });
  },

  // 上传分片
  uploadChunk: async (uploadId: string, chunkIndex: number, chunk: Blob) => {
    const formData = new FormData();
    formData.append('upload_id', uploadId);
    formData.append('chunk_index', chunkIndex.toString());
    formData.append('chunk', chunk);

    return apiClient.post<{ success: boolean; received_chunks: number }>(
      '/api/documents/upload/chunk',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
  },

  // 完成上传
  completeUpload: async (data: UploadCompleteRequest) => {
    return apiClient.post<{ document_id: string; status: string }>(
      '/api/documents/upload/complete',
      data
    );
  },

  // 获取文档列表
  getDocuments: async (params: DocumentListParams) => {
    return apiClient.get<DocumentListResponse>('/api/documents', { params });
  },

  // 获取文档详情
  getDocument: async (documentId: string) => {
    return apiClient.get<Document>(`/api/documents/${documentId}`);
  },

  // 获取文档页面列表
  getDocumentSlides: async (documentId: string) => {
    return apiClient.get<{ slides: Slide[] }>(`/api/documents/${documentId}/slides`);
  },

  // 获取文档文件 URL
  getDocumentFileUrl: (documentId: string) => {
    return `${getBaseUrl()}/api/documents/${documentId}/file`;
  },

  // 获取文档预览链接
  previewDocument: async (documentId: string) => {
    return apiClient.post<PreviewResponse>(`/api/documents/${documentId}/preview`);
  },

  // 删除文档
  deleteDocument: async (documentId: string) => {
    return apiClient.delete<{ success: boolean }>(`/api/documents/${documentId}`);
  },

  // 搜索文档
  searchDocuments: async (query: string, page = 1, limit = 20) => {
    return apiClient.get<DocumentListResponse>('/api/documents/search', {
      params: { query, page, limit },
    });
  },
};

export default documentsApi;
