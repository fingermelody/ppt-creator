import { create } from 'zustand';
import {
  RefinementTask,
  RefinedPage,
  RefinementMessage,
  ModificationRecord,
} from '../types/refinement';

interface RefinementState {
  task: RefinementTask | null;
  currentPageIndex: number;
  pages: RefinedPage[];
  messages: Record<number, RefinementMessage[]>; // page_index -> messages
  modifications: ModificationRecord[];
  loading: boolean;
  error: string | null;

  // Actions
  setTask: (task: RefinementTask | null) => void;
  updateTask: (updates: Partial<RefinementTask>) => void;
  setPages: (pages: RefinedPage[]) => void;
  setCurrentPageIndex: (pageIndex: number) => void;
  updatePage: (pageIndex: number, updates: Partial<RefinedPage>) => void;
  addMessage: (pageIndex: number, message: RefinementMessage) => void;
  setMessages: (pageIndex: number, messages: RefinementMessage[]) => void;
  addModification: (modification: ModificationRecord) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useRefinementStore = create<RefinementState>((set) => ({
  task: null,
  currentPageIndex: 0,
  pages: [],
  messages: {},
  modifications: [],
  loading: false,
  error: null,

  setTask: (task) => set({ task }),

  updateTask: (updates) =>
    set((state) => ({
      task: state.task ? { ...state.task, ...updates } : null,
    })),

  setPages: (pages) => set({ pages }),

  setCurrentPageIndex: (pageIndex) => set({ currentPageIndex: pageIndex }),

  updatePage: (pageIndex, updates) =>
    set((state) => ({
      pages: state.pages.map((page) =>
        page.page_index === pageIndex ? { ...page, ...updates } : page
      ),
    })),

  addMessage: (pageIndex, message) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [pageIndex]: [...(state.messages[pageIndex] || []), message],
      },
    })),

  setMessages: (pageIndex, messages) =>
    set((state) => ({
      messages: {
        ...state.messages,
        [pageIndex]: messages,
      },
    })),

  addModification: (modification) =>
    set((state) => ({
      modifications: [...state.modifications, modification],
    })),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  reset: () =>
    set({
      task: null,
      currentPageIndex: 0,
      pages: [],
      messages: {},
      modifications: [],
      loading: false,
      error: null,
    }),
}));
