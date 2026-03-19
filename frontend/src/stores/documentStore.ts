import { create } from 'zustand';
import { Document, Slide } from '../types/document';

interface DocumentState {
  documents: Document[];
  selectedDocument: Document | null;
  selectedSlides: Slide[];
  loading: boolean;
  error: string | null;

  // Actions
  setDocuments: (documents: Document[]) => void;
  addDocument: (document: Document) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  removeDocument: (id: string) => void;
  setSelectedDocument: (document: Document | null) => void;
  setSelectedSlides: (slides: Slide[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useDocumentStore = create<DocumentState>((set) => ({
  documents: [],
  selectedDocument: null,
  selectedSlides: [],
  loading: false,
  error: null,

  setDocuments: (documents) => set({ documents }),

  addDocument: (document) =>
    set((state) => ({
      documents: [document, ...state.documents],
    })),

  updateDocument: (id, updates) =>
    set((state) => ({
      documents: state.documents.map((doc) =>
        doc.id === id ? { ...doc, ...updates } : doc
      ),
      selectedDocument:
        state.selectedDocument?.id === id
          ? { ...state.selectedDocument, ...updates }
          : state.selectedDocument,
    })),

  removeDocument: (id) =>
    set((state) => ({
      documents: state.documents.filter((doc) => doc.id !== id),
      selectedDocument:
        state.selectedDocument?.id === id ? null : state.selectedDocument,
    })),

  setSelectedDocument: (document) => set({ selectedDocument: document }),

  setSelectedSlides: (slides) => set({ selectedSlides: slides }),

  setLoading: (loading) => set({ loading }),

  setError: (error) => set({ error }),
}));
