import { create } from 'zustand';
import { AssemblyDraft, Chapter, ChapterPage, OperationType } from '../types/assembly';

interface AssemblyState {
  draft: AssemblyDraft | null;
  loading: boolean;
  error: string | null;
  canUndo: boolean;
  canRedo: boolean;
  undoDescription?: string;
  redoDescription?: string;

  // Actions
  setDraft: (draft: AssemblyDraft | null) => void;
  updateDraft: (updates: Partial<AssemblyDraft>) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setUndoRedoState: (
    canUndo: boolean,
    canRedo: boolean,
    undoDescription?: string,
    redoDescription?: string
  ) => void;

  // Chapter operations
  addChapter: (chapter: Chapter) => void;
  updateChapter: (chapterId: string, updates: Partial<Chapter>) => void;
  removeChapter: (chapterId: string) => void;
  moveChapter: (fromIndex: number, toIndex: number) => void;

  // Page operations
  replacePage: (
    chapterId: string,
    oldPage: ChapterPage,
    newPages: ChapterPage[]
  ) => void;
  deletePage: (chapterId: string, slideId: string) => void;
  addPage: (chapterId: string, page: ChapterPage, order: number) => void;
  reorderPages: (chapterId: string, pageOrders: { slide_id: string; order: number }[]) => void;
  movePage: (slideId: string, fromChapterId: string, toChapterId: string, order: number) => void;
}

export const useAssemblyStore = create<AssemblyState>((set) => ({
  draft: null,
  loading: false,
  error: null,
  canUndo: false,
  canRedo: false,

  setDraft: (draft) => set({ draft }),

  updateDraft: (updates) =>
    set((state) => ({
      draft: state.draft ? { ...state.draft, ...updates } : null,
    })),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),

  setUndoRedoState: (canUndo, canRedo, undoDescription, redoDescription) =>
    set({ canUndo, canRedo, undoDescription, redoDescription }),

  addChapter: (chapter) =>
    set((state) => ({
      draft: state.draft
        ? {
            ...state.draft,
            chapters: [...state.draft.chapters, chapter],
            total_pages: state.draft.total_pages + chapter.page_count,
          }
        : null,
    })),

  updateChapter: (chapterId, updates) =>
    set((state) => ({
      draft: state.draft
        ? {
            ...state.draft,
            chapters: state.draft.chapters.map((ch) =>
              ch.id === chapterId ? { ...ch, ...updates } : ch
            ),
          }
        : null,
    })),

  removeChapter: (chapterId) =>
    set((state) => ({
      draft: state.draft
        ? {
            ...state.draft,
            chapters: state.draft.chapters.filter((ch) => ch.id !== chapterId),
            total_pages: state.draft.total_pages - state.draft.chapters.find((ch) => ch.id === chapterId)!.page_count,
          }
        : null,
    })),

  moveChapter: (fromIndex, toIndex) =>
    set((state) => {
      if (!state.draft) return state;

      const newChapters = [...state.draft.chapters];
      const [movedChapter] = newChapters.splice(fromIndex, 1);
      newChapters.splice(toIndex, 0, movedChapter);

      return {
        draft: {
          ...state.draft,
          chapters: newChapters,
        },
      };
    }),

  replacePage: (chapterId, oldPage, newPages) =>
    set((state) => ({
      draft: state.draft
        ? {
            ...state.draft,
            chapters: state.draft.chapters.map((ch) => {
              if (ch.id === chapterId) {
                const oldPageIndex = ch.pages.findIndex((p) => p.slide_id === oldPage.slide_id);
                const newPagesWithOrder = newPages.map((p, idx) => ({
                  ...p,
                  order: oldPageIndex + idx,
                }));

                return {
                  ...ch,
                  pages: [
                    ...ch.pages.slice(0, oldPageIndex),
                    ...newPagesWithOrder,
                    ...ch.pages.slice(oldPageIndex + 1),
                  ],
                  page_count: ch.page_count - 1 + newPages.length,
                };
              }
              return ch;
            }),
            total_pages: state.draft.total_pages - 1 + newPages.length,
          }
        : null,
    })),

  deletePage: (chapterId, slideId) =>
    set((state) => ({
      draft: state.draft
        ? {
            ...state.draft,
            chapters: state.draft.chapters.map((ch) => {
              if (ch.id === chapterId) {
                return {
                  ...ch,
                  pages: ch.pages.filter((p) => p.slide_id !== slideId),
                  page_count: ch.page_count - 1,
                };
              }
              return ch;
            }),
            total_pages: state.draft.total_pages - 1,
          }
        : null,
    })),

  addPage: (chapterId, page, order) =>
    set((state) => ({
      draft: state.draft
        ? {
            ...state.draft,
            chapters: state.draft.chapters.map((ch) => {
              if (ch.id === chapterId) {
                const newPages = [...ch.pages, { ...page, order }];
                newPages.sort((a, b) => a.order - b.order);
                return {
                  ...ch,
                  pages: newPages,
                  page_count: ch.page_count + 1,
                };
              }
              return ch;
            }),
            total_pages: state.draft.total_pages + 1,
          }
        : null,
    })),

  reorderPages: (chapterId, pageOrders) =>
    set((state) => ({
      draft: state.draft
        ? {
            ...state.draft,
            chapters: state.draft.chapters.map((ch) => {
              if (ch.id === chapterId) {
                const newPages = [...ch.pages];
                pageOrders.forEach(({ slide_id, order }) => {
                  const page = newPages.find((p) => p.slide_id === slide_id);
                  if (page) {
                    page.order = order;
                  }
                });
                newPages.sort((a, b) => a.order - b.order);
                return {
                  ...ch,
                  pages: newPages,
                };
              }
              return ch;
            }),
          }
        : null,
    })),

  movePage: (slideId, fromChapterId, toChapterId, order) =>
    set((state) => {
      if (!state.draft) return state;

      let pageToMove: ChapterPage | null = null;

      // Remove from source chapter
      const chapters = state.draft.chapters.map((ch) => {
        if (ch.id === fromChapterId) {
          const pages = ch.pages.filter((p) => {
            if (p.slide_id === slideId) {
              pageToMove = p;
              return false;
            }
            return true;
          });
          return {
            ...ch,
            pages: pages.map((p, idx) => ({ ...p, order: idx })),
            page_count: pages.length,
          };
        }
        return ch;
      });

      // Add to target chapter
      if (pageToMove) {
        return {
          draft: {
            ...state.draft,
            chapters: chapters.map((ch) => {
              if (ch.id === toChapterId) {
                const pages = [...ch.pages, { ...pageToMove!, order }];
                pages.sort((a, b) => a.order - b.order);
                return {
                  ...ch,
                  pages,
                  page_count: pages.length,
                };
              }
              return ch;
            }),
          },
        };
      }

      return { draft: state.draft };
    }),
}));
