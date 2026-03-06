/* 文档相关类型定义 */

export type DocumentStatus = 'uploading' | 'processing' | 'parsing' | 'vectorizing' | 'ready' | 'error';

export interface Document {
  id: string;
  title: string;
  filename: string;
  original_filename: string;
  category?: string;
  page_count: number;
  status: DocumentStatus;
  thumbnail?: string;
  created_at: string;
  updated_at: string;
  file_size?: number;
  cos_url?: string;  // COS 访问 URL
  vectorized_pages?: number;  // 已向量化的页数
}

export interface Slide {
  id: string;
  document_id: string;
  page_number: number;
  title: string;
  content_text: string;
  layout_type?: string;
  thumbnail?: string;
  thumbnail_url?: string;
  vector_id?: string;
  is_vectorized?: number;
  created_at: string;
}

export interface SlideElement {
  type: 'text' | 'image' | 'chart' | 'table' | 'shape';
  bbox: {
    left: number;
    top: number;
    width: number;
    height: number;
  };
  content: any;
  style?: any;
}

export interface SlideContent {
  id: string;
  elements: SlideElement[];
  background?: any;
  layout?: any;
}

export interface UploadInitResponse {
  upload_id: string;
  chunk_size: number;
}

export interface UploadChunkRequest {
  upload_id: string;
  chunk_index: number;
  chunk: Blob;
}

export interface UploadCompleteRequest {
  upload_id: string;
  title: string;
  category?: string;
}

export interface DocumentListParams {
  page: number;
  limit: number;
  category?: string;
  status?: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export interface PreviewResponse {
  success: boolean;
  preview_url?: string;
  filename?: string;
  preview_type?: 'cos' | 'local';
  cos_url?: string;
  message?: string;
  status?: string;
}
