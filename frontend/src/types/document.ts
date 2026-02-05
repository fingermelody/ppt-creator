/* 文档相关类型定义 */

export interface Document {
  id: string;
  title: string;
  category?: string;
  page_count: number;
  status: 'uploading' | 'parsing' | 'ready' | 'error';
  thumbnail?: string;
  created_at: string;
  updated_at: string;
  file_size?: number;
}

export interface Slide {
  id: string;
  document_id: string;
  page_number: number;
  title: string;
  content_text: string;
  layout_type?: string;
  thumbnail: string;
  embedding?: number[];
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
