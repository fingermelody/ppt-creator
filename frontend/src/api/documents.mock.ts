/* 文档 API - Mock 版本 */

import { mockApi, useMock } from '../mocks/api';

const documentsApi = {
  initUpload: async (filename: string, filesize: number, totalChunks: number) => {
    if (useMock()) {
      return mockApi.documents.initUpload({ filename, filesize, totalChunks });
    }
    // 真实 API 调用
    const { default: documentsApiReal } = await import('./documents');
    return documentsApiReal.initUpload(filename, filesize, totalChunks);
  },

  uploadChunk: async (uploadId: string, chunkIndex: number, chunk: Blob) => {
    if (useMock()) {
      return mockApi.documents.uploadChunk(uploadId, chunkIndex, chunk);
    }
    const { default: documentsApiReal } = await import('./documents');
    return documentsApiReal.uploadChunk(uploadId, chunkIndex, chunk);
  },

  completeUpload: async (data: any) => {
    if (useMock()) {
      return mockApi.documents.completeUpload(data);
    }
    const { default: documentsApiReal } = await import('./documents');
    return documentsApiReal.completeUpload(data);
  },

  getDocuments: async (params?: any) => {
    if (useMock()) {
      return mockApi.documents.getDocuments(params);
    }
    const { default: documentsApiReal } = await import('./documents');
    return documentsApiReal.getDocuments(params);
  },

  getDocument: async (documentId: string) => {
    if (useMock()) {
      return mockApi.documents.getDocument(documentId);
    }
    const { default: documentsApiReal } = await import('./documents');
    return documentsApiReal.getDocument(documentId);
  },

  getDocumentSlides: async (documentId: string) => {
    if (useMock()) {
      return mockApi.documents.getDocumentSlides(documentId);
    }
    const { default: documentsApiReal } = await import('./documents');
    return documentsApiReal.getDocumentSlides(documentId);
  },

  deleteDocument: async (documentId: string) => {
    if (useMock()) {
      return mockApi.documents.deleteDocument(documentId);
    }
    const { default: documentsApiReal } = await import('./documents');
    return documentsApiReal.deleteDocument(documentId);
  },

  searchDocuments: async (query: string, page = 1, limit = 20) => {
    if (useMock()) {
      return mockApi.documents.searchDocuments(query, page, limit);
    }
    const { default: documentsApiReal } = await import('./documents');
    return documentsApiReal.searchDocuments(query, page, limit);
  },
};

export default documentsApi;
