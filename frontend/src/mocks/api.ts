/* Mock API 统一接口 */

import { documentHandlers } from './handlers';
import { assemblyHandlers } from './handlers';
import { refinementHandlers } from './handlers';

export const mockApi = {
  // 文档 API
  documents: {
    initUpload: documentHandlers.initUpload,
    uploadChunk: documentHandlers.uploadChunk,
    completeUpload: documentHandlers.completeUpload,
    getDocuments: documentHandlers.getDocuments,
    getDocument: documentHandlers.getDocument,
    getDocumentSlides: documentHandlers.getDocumentSlides,
    deleteDocument: documentHandlers.deleteDocument,
    searchDocuments: documentHandlers.searchDocuments,
  },

  // 组装 API
  assembly: {
    createDraft: assemblyHandlers.createDraft,
    getDrafts: assemblyHandlers.getDrafts,
    getDraftDetail: assemblyHandlers.getDraftDetail,
    saveDraft: assemblyHandlers.saveDraft,
    deleteDraft: assemblyHandlers.deleteDraft,
    exportPPT: assemblyHandlers.exportPPT,
    addChapter: assemblyHandlers.addChapter,
    updateChapter: assemblyHandlers.updateChapter,
    deleteChapter: assemblyHandlers.deleteChapter,
    regenerateChapter: assemblyHandlers.regenerateChapter,
    getAlternatives: assemblyHandlers.getAlternatives,
    replacePage: assemblyHandlers.replacePage,
    deletePage: assemblyHandlers.deletePage,
    addPage: assemblyHandlers.addPage,
    reorderPages: () => Promise.resolve({ success: true }),
    movePage: () => Promise.resolve({ success: true }),
    undo: assemblyHandlers.undo,
    redo: assemblyHandlers.redo,
    getHistory: () => Promise.resolve({ operations: [] }),
  },

  // 精修 API
  refinement: {
    createTask: refinementHandlers.createTask,
    getTaskDetail: refinementHandlers.getTaskDetail,
    saveTask: refinementHandlers.saveTask,
    exportRefinedPPT: refinementHandlers.exportRefinedPPT,
    getPageContent: refinementHandlers.getPageContent,
    getPageThumbnail: refinementHandlers.getPageThumbnail,
    sendMessage: refinementHandlers.sendMessage,
    getChatHistory: refinementHandlers.getChatHistory,
    editText: (_taskId: string, _pageIndex: number, _elementId: string, _text: string, _preserveStyle?: boolean) =>
      Promise.resolve({ success: true, modification_id: 'mock-id', updated_element: {} }),
    editTable: (_taskId: string, _pageIndex: number, _elementId: string, _operation: string, _data: any) =>
      Promise.resolve({ success: true, modification_id: 'mock-id', updated_element: {} }),
    replaceImage: (_taskId: string, _pageIndex: number, _elementId: string, _imageUrl?: string, _imageBase64?: string) =>
      Promise.resolve({ success: true, modification_id: 'mock-id', updated_element: {} }),
    editStyle: (_taskId: string, _pageIndex: number, _elementId: string, _style: any) =>
      Promise.resolve({ success: true, modification_id: 'mock-id', updated_element: {} }),
    getSuggestions: (_taskId: string, _pageIndex: number) =>
      Promise.resolve({ suggestions: [] }),
    getQuickActions: (_taskId: string, _pageIndex: number, _selectedElement?: string) =>
      Promise.resolve({ actions: [] }),
  },

  // 导出 API
  export: {
    exportDocument: () => Promise.resolve({ download_url: 'https://via.placeholder.com/file.pptx', file_size: 10485760 }),
    exportDraft: assemblyHandlers.exportPPT,
    exportRefined: refinementHandlers.exportRefinedPPT,
  },
};

// 检查是否使用 mock 模式
export const useMock = () => {
  return import.meta.env.VITE_USE_MOCK === 'true';
};
