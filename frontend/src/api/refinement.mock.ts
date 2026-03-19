/* 精修 API - Mock 版本 */

import { mockApi, useMock } from '../mocks/api';

const refinementApi = {
  createTask: async (draftId: string, title?: string) => {
    if (useMock()) {
      return mockApi.refinement.createTask({ draft_id: draftId, title });
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.createTask(draftId, title);
  },

  getTaskDetail: async (taskId: string) => {
    if (useMock()) {
      return mockApi.refinement.getTaskDetail(taskId);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.getTaskDetail(taskId);
  },

  saveTask: async (taskId: string, title?: string) => {
    if (useMock()) {
      return mockApi.refinement.saveTask(taskId, { title });
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.saveTask(taskId, title);
  },

  exportRefinedPPT: async (taskId: string) => {
    if (useMock()) {
      return mockApi.refinement.exportRefinedPPT(taskId);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.exportRefinedPPT(taskId);
  },

  getPageContent: async (taskId: string, pageIndex: number) => {
    if (useMock()) {
      return mockApi.refinement.getPageContent(taskId, pageIndex);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.getPageContent(taskId, pageIndex);
  },

  getPageThumbnail: async (taskId: string, pageIndex: number) => {
    if (useMock()) {
      return mockApi.refinement.getPageThumbnail(taskId, pageIndex);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.getPageThumbnail(taskId, pageIndex);
  },

  sendMessage: async (taskId: string, pageIndex: number, message: string, selectedElement?: string, conversationId?: string) => {
    if (useMock()) {
      return mockApi.refinement.sendMessage(taskId, pageIndex, message, { selectedElement, conversationId });
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.sendMessage(taskId, pageIndex, message, selectedElement, conversationId);
  },

  getChatHistory: async (taskId: string, pageIndex: number) => {
    if (useMock()) {
      return mockApi.refinement.getChatHistory(taskId, pageIndex);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.getChatHistory(taskId, pageIndex);
  },

  editText: async (taskId: string, pageIndex: number, elementId: string, text: string, preserveStyle = true) => {
    if (useMock()) {
      return mockApi.refinement.editText(taskId, pageIndex, elementId, text, preserveStyle);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.editText(taskId, pageIndex, elementId, text, preserveStyle);
  },

  editTable: async (taskId: string, pageIndex: number, elementId: string, operation: string, data: any) => {
    if (useMock()) {
      return mockApi.refinement.editTable(taskId, pageIndex, elementId, operation, data);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.editTable(taskId, pageIndex, elementId, operation, data);
  },

  replaceImage: async (taskId: string, pageIndex: number, elementId: string, imageUrl?: string, imageBase64?: string) => {
    if (useMock()) {
      return mockApi.refinement.replaceImage(taskId, pageIndex, elementId, imageUrl, imageBase64);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.replaceImage(taskId, pageIndex, elementId, imageUrl, imageBase64);
  },

  editStyle: async (taskId: string, pageIndex: number, elementId: string, style: any) => {
    if (useMock()) {
      return mockApi.refinement.editStyle(taskId, pageIndex, elementId, style);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.editStyle(taskId, pageIndex, elementId, style);
  },

  getSuggestions: async (taskId: string, pageIndex: number) => {
    if (useMock()) {
      return mockApi.refinement.getSuggestions(taskId, pageIndex);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.getSuggestions(taskId, pageIndex);
  },

  getQuickActions: async (taskId: string, pageIndex: number, selectedElement?: string) => {
    if (useMock()) {
      return mockApi.refinement.getQuickActions(taskId, pageIndex, selectedElement);
    }
    const { default: refinementApiReal } = await import('./refinement');
    return refinementApiReal.getQuickActions(taskId, pageIndex, selectedElement);
  },
};

export default refinementApi;
