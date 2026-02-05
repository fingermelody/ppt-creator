/* 工具函数 */

import dayjs from 'dayjs';
import { STATUS, SIMILARITY } from './constants';

/**
 * 格式化日期时间
 */
export function formatDateTime(date: string | Date): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss');
}

/**
 * 格式化文件大小
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
}

/**
 * 验证文件类型
 */
export function validateFileType(filename: string): boolean {
  const { ALLOWED_TYPES } = UPLOAD;
  const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'));
  return ALLOWED_TYPES.includes(extension);
}

/**
 * 验证文件大小
 */
export function validateFileSize(fileSize: number): boolean {
  return fileSize <= UPLOAD.MAX_FILE_SIZE;
}

/**
 * 获取状态颜色
 */
export function getStatusColor(status: string): string {
  const colorMap: Record<string, string> = {
    [STATUS.DOCUMENT.UPLOADING]: 'warning',
    [STATUS.DOCUMENT.PARSING]: 'primary',
    [STATUS.DOCUMENT.READY]: 'success',
    [STATUS.DOCUMENT.ERROR]: 'danger',
    [STATUS.ASSEMBLY.DRAFT]: 'default',
    [STATUS.ASSEMBLY.GENERATING]: 'primary',
    [STATUS.ASSEMBLY.COMPLETED]: 'success',
  };
  return colorMap[status] || 'default';
}

/**
 * 获取匹配度级别
 */
export function getSimilarityLevel(score: number): { label: string; color: string } {
  if (score >= SIMILARITY.HIGH) {
    return { label: '高匹配', color: 'success' };
  } else if (score >= SIMILARITY.MEDIUM) {
    return { label: '中等匹配', color: 'warning' };
  } else if (score >= SIMILARITY.LOW) {
    return { label: '低匹配', color: 'default' };
  } else {
    return { label: '不匹配', color: 'danger' };
  }
}

/**
 * 生成唯一ID
 */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * 防抖函数
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  return function (...args: Parameters<T>) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
}

/**
 * 节流函数
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let lastCall = 0;
  return function (...args: Parameters<T>) {
    const now = Date.now();
    if (now - lastCall >= delay) {
      lastCall = now;
      func.apply(this, args);
    }
  };
}

/**
 * 深拷贝
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  if (obj instanceof Date) {
    return new Date(obj.getTime()) as any;
  }
  if (obj instanceof Array) {
    return obj.map((item) => deepClone(item)) as any;
  }
  const cloned = {} as any;
  for (const key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloned[key] = deepClone(obj[key]);
    }
  }
  return cloned;
}

/**
 * 下载文件
 */
export function downloadFile(url: string, filename?: string): void {
  const link = document.createElement('a');
  link.href = url;
  if (filename) {
    link.download = filename;
  }
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// 导入常量
import { UPLOAD } from './constants';
