/* 常量定义 */

// 页面路径
export const ROUTES = {
  HOME: '/',
  LIBRARY: '/library',
  ASSEMBLY: '/assembly',
  REFINEMENT: '/refinement',
  DRAFTS: '/drafts',
} as const;

// 文件上传限制
export const UPLOAD = {
  MAX_FILE_SIZE: 100 * 1024 * 1024, // 100MB
  CHUNK_SIZE: 5 * 1024 * 1024, // 5MB
  ALLOWED_TYPES: ['.pptx', '.ppt'],
  ALLOWED_MIME_TYPES: [
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.ms-powerpoint',
  ],
} as const;

// PPT 页数限制
export const PPT = {
  MIN_PAGES: 1,
  MAX_PAGES: 100,
  MIN_CHAPTER_PAGES: 3,
  MAX_CHAPTER_PAGES: 8,
} as const;

// 状态映射
export const STATUS = {
  DOCUMENT: {
    UPLOADING: 'uploading',
    PARSING: 'parsing',
    READY: 'ready',
    ERROR: 'error',
  } as const,
  ASSEMBLY: {
    DRAFT: 'draft',
    GENERATING: 'generating',
    COMPLETED: 'completed',
  } as const,
  REFINEMENT: {
    EDITING: 'editing',
    SAVED: 'saved',
    EXPORTED: 'exported',
  } as const,
} as const;

// 分页配置
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_LIMIT: 20,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
} as const;

// 匹配度阈值
export const SIMILARITY = {
  HIGH: 80,
  MEDIUM: 60,
  LOW: 40,
} as const;

// LLM配置
export const LLM = {
  MAX_TOKENS: 2000,
  TEMPERATURE: 0.7,
  TOP_P: 0.9,
} as const;
