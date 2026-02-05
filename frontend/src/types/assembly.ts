/* 组装相关类型定义 */

export interface Chapter {
  id: string;
  title: string;
  description: string;
  required_pages: number;
  page_count: number;
  pages: ChapterPage[];
  created_at: string;
  updated_at: string;
}

export interface ChapterPage {
  slide_id: string;
  document_id: string;
  document_title: string;
  page_number: number;
  thumbnail: string;
  similarity: number;
  content_summary: string;
  order: number;
}

export interface AlternativePage {
  slide_id: string;
  document_id: string;
  document_title: string;
  page_number: number;
  thumbnail: string;
  similarity: number;
  content_summary: string;
}

export interface AssemblyDraft {
  id: string;
  title: string;
  description?: string;
  chapters: Chapter[];
  total_pages: number;
  status: 'draft' | 'generating' | 'completed';
  created_at: string;
  updated_at: string;
  version: number;
}

export interface DraftListResponse {
  drafts: AssemblyDraft[];
  total: number;
}

export interface DraftDetail {
  draft: AssemblyDraft;
  can_undo: boolean;
  can_redo: boolean;
  undo_description?: string;
  redo_description?: string;
}

export interface ReplacePageRequest {
  chapter_id: string;
  current_slide_id: string;
  new_slide_ids: string[];
  insert_position?: 'replace' | 'before' | 'after';
}

export interface ReplacePageResponse {
  success: boolean;
  replaced_pages: ChapterPage[];
  new_pages: ChapterPage[];
}

export interface AlternativeResponse {
  current_page: AlternativePage;
  alternatives: AlternativePage[];
}

export interface OperationRecord {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  can_undo: boolean;
}

export interface OperationHistory {
  operations: OperationRecord[];
}

export enum OperationType {
  ADD_CHAPTER = 'add_chapter',
  UPDATE_CHAPTER = 'update_chapter',
  DELETE_CHAPTER = 'delete_chapter',
  REGENERATE_CHAPTER = 'regenerate_chapter',
  REPLACE_PAGE = 'replace_page',
  DELETE_PAGE = 'delete_page',
  ADD_PAGE = 'add_page',
  REORDER_PAGES = 'reorder_pages',
  MOVE_PAGE = 'move_page',
}
