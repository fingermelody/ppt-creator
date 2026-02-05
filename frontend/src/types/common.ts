/* 通用类型定义 */

export interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface PaginationParams {
  page: number;
  limit: number;
}

export interface PaginationMeta {
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  meta: PaginationMeta;
}

export type StatusType = 'success' | 'info' | 'warning' | 'error';
