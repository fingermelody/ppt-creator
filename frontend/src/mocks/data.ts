/* Mock 数据 */

import { Document, Slide, AssemblyDraft, Chapter, ChapterPage, RefinementTask, RefinedPage, RefinementMessage } from '../types';

// Mock 文档数据
export const mockDocuments: Document[] = [
  {
    id: 'doc-001',
    title: '公司介绍PPT',
    category: '企业介绍',
    page_count: 12,
    status: 'ready',
    thumbnail: 'https://via.placeholder.com/400x300?text=Company+Intro',
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-02-01T10:00:00Z',
    file_size: 5242880,
  },
  {
    id: 'doc-002',
    title: '产品展示PPT',
    category: '产品介绍',
    page_count: 15,
    status: 'ready',
    thumbnail: 'https://via.placeholder.com/400x300?text=Product+Showcase',
    created_at: '2026-02-02T10:00:00Z',
    updated_at: '2026-02-02T10:00:00Z',
    file_size: 6291456,
  },
  {
    id: 'doc-003',
    title: '技术方案PPT',
    category: '技术文档',
    page_count: 20,
    status: 'ready',
    thumbnail: 'https://via.placeholder.com/400x300?text=Technical+Plan',
    created_at: '2026-02-03T10:00:00Z',
    updated_at: '2026-02-03T10:00:00Z',
    file_size: 8388608,
  },
  {
    id: 'doc-004',
    title: '市场分析PPT',
    category: '市场分析',
    page_count: 10,
    status: 'ready',
    thumbnail: 'https://via.placeholder.com/400x300?text=Market+Analysis',
    created_at: '2026-02-04T10:00:00Z',
    updated_at: '2026-02-04T10:00:00Z',
    file_size: 4194304,
  },
];

// Mock 页面数据
export const mockSlides: Record<string, Slide[]> = {
  'doc-001': Array.from({ length: 12 }, (_, i) => ({
    id: `slide-doc001-${i + 1}`,
    document_id: 'doc-001',
    page_number: i + 1,
    title: `页面 ${i + 1}`,
    content_text: `这是文档1的第${i + 1}页内容，包含文字和图表...`,
    layout_type: 'title-content',
    thumbnail: `https://via.placeholder.com/400x300?text=Page+${i + 1}`,
    embedding: new Array(768).fill(0).map(() => Math.random()),
    created_at: '2026-02-01T10:00:00Z',
  })),
};

// Mock 草稿数据
export const mockDrafts: AssemblyDraft[] = [
  {
    id: 'draft-001',
    title: '2026年度工作总结PPT',
    description: '年度工作总结和计划',
    chapters: [],
    total_pages: 0,
    status: 'draft',
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-02-01T10:00:00Z',
    version: 1,
  },
  {
    id: 'draft-002',
    title: '新产品发布会PPT',
    description: '新产品发布展示',
    chapters: [
      {
        id: 'chapter-001',
        title: '产品概述',
        description: '介绍产品的基本功能和特点',
        required_pages: 5,
        page_count: 5,
        pages: [
          {
            slide_id: 'slide-001',
            document_id: 'doc-002',
            document_title: '产品展示PPT',
            page_number: 1,
            thumbnail: 'https://via.placeholder.com/280x200?text=Product+Overview',
            similarity: 95.5,
            content_summary: '产品概述内容',
            order: 0,
          },
          {
            slide_id: 'slide-002',
            document_id: 'doc-002',
            document_title: '产品展示PPT',
            page_number: 2,
            thumbnail: 'https://via.placeholder.com/280x200?text=Features',
            similarity: 92.3,
            content_summary: '产品特性展示',
            order: 1,
          },
          {
            slide_id: 'slide-003',
            document_id: 'doc-002',
            document_title: '产品展示PPT',
            page_number: 3,
            thumbnail: 'https://via.placeholder.com/280x200?text=Benefits',
            similarity: 88.7,
            content_summary: '产品优势',
            order: 2,
          },
          {
            slide_id: 'slide-004',
            document_id: 'doc-002',
            document_title: '产品展示PPT',
            page_number: 5,
            thumbnail: 'https://via.placeholder.com/280x200?text=Use+Cases',
            similarity: 85.2,
            content_summary: '使用场景',
            order: 3,
          },
          {
            slide_id: 'slide-005',
            document_id: 'doc-002',
            document_title: '产品展示PPT',
            page_number: 6,
            thumbnail: 'https://via.placeholder.com/280x200?text=Target+Users',
            similarity: 82.1,
            content_summary: '目标用户',
            order: 4,
          },
        ],
        created_at: '2026-02-01T10:00:00Z',
        updated_at: '2026-02-01T10:00:00Z',
      },
    ],
    total_pages: 5,
    status: 'completed',
    created_at: '2026-02-01T10:00:00Z',
    updated_at: '2026-02-01T10:00:00Z',
    version: 2,
  },
];

// Mock 精修任务
export const mockRefinementTask: RefinementTask = {
  id: 'task-001',
  draft_id: 'draft-002',
  title: '新产品发布会PPT',
  status: 'editing',
  current_page_index: 0,
  created_at: '2026-02-01T10:00:00Z',
  updated_at: '2026-02-01T10:00:00Z',
};

// Mock 精修页面
export const mockRefinedPages: RefinedPage[] = [
  {
    page_index: 0,
    slide_id: 'slide-001',
    source_document_id: 'doc-002',
    source_page_number: 1,
    current_content: {
      id: 'page-0',
      elements: [
        {
          id: 'element-1',
          type: 'text',
          bbox: { left: 50, top: 50, width: 400, height: 80 },
          content: { text: '新产品发布会' },
          style: { font_family: 'Arial', font_size: 36, color: '#333333', bold: true },
          zIndex: 1,
        },
      ],
      background: { type: 'solid', color: '#ffffff' },
    },
    version: 1,
    modification_count: 2,
  },
  {
    page_index: 1,
    slide_id: 'slide-002',
    source_document_id: 'doc-002',
    source_page_number: 2,
    current_content: {
      id: 'page-1',
      elements: [
        {
          id: 'element-2',
          type: 'text',
          bbox: { left: 50, top: 50, width: 600, height: 60 },
          content: { text: '产品特性' },
          style: { font_family: 'Arial', font_size: 28, color: '#333333' },
          zIndex: 1,
        },
      ],
      background: { type: 'solid', color: '#ffffff' },
    },
    version: 1,
    modification_count: 0,
  },
  {
    page_index: 2,
    slide_id: 'slide-003',
    source_document_id: 'doc-002',
    source_page_number: 3,
    current_content: {
      id: 'page-2',
      elements: [
        {
          id: 'element-3',
          type: 'text',
          bbox: { left: 50, top: 50, width: 600, height: 60 },
          content: { text: '产品优势' },
          style: { font_family: 'Arial', font_size: 28, color: '#333333' },
          zIndex: 1,
        },
      ],
      background: { type: 'solid', color: '#ffffff' },
    },
    version: 1,
    modification_count: 1,
  },
  {
    page_index: 3,
    slide_id: 'slide-004',
    source_document_id: 'doc-002',
    source_page_number: 5,
    current_content: {
      id: 'page-3',
      elements: [],
      background: { type: 'solid', color: '#ffffff' },
    },
    version: 1,
    modification_count: 0,
  },
  {
    page_index: 4,
    slide_id: 'slide-005',
    source_document_id: 'doc-002',
    source_page_number: 6,
    current_content: {
      id: 'page-4',
      elements: [],
      background: { type: 'solid', color: '#ffffff' },
    },
    version: 1,
    modification_count: 0,
  },
];

// Mock 对话消息
export const mockMessages: Record<number, RefinementMessage[]> = {
  0: [
    {
      id: 'msg-001',
      role: 'user',
      content: '把标题修改为"2026年新产品发布会"',
      type: 'chat',
      timestamp: '2026-02-01T10:30:00Z',
    },
    {
      id: 'msg-002',
      role: 'assistant',
      content: '已为您修改标题为"2026年新产品发布会"',
      type: 'modification',
      timestamp: '2026-02-01T10:30:05Z',
      modification: {
        id: 'mod-001',
        type: 'edit_text',
        description: '修改标题文本',
        element_id: 'element-1',
        before: { text: '新产品发布会' },
        after: { text: '2026年新产品发布会' },
        page_version: 1,
      },
    },
  ],
  1: [],
  2: [
    {
      id: 'msg-003',
      role: 'user',
      content: '添加一个产品特点列表',
      type: 'chat',
      timestamp: '2026-02-01T11:00:00Z',
    },
    {
      id: 'msg-004',
      role: 'assistant',
      content: '已为您添加产品特点列表，包括：1. 高效性能 2. 易于使用 3. 安全可靠',
      type: 'modification',
      timestamp: '2026-02-01T11:00:10Z',
      modification: {
        id: 'mod-002',
        type: 'add_element',
        description: '添加文本列表',
        element_id: 'element-4',
        before: null,
        after: { text: '1. 高效性能\n2. 易于使用\n3. 安全可靠' },
        page_version: 1,
      },
    },
  ],
  3: [],
  4: [],
};
