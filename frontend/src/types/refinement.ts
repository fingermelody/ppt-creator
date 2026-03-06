/* 精修相关类型定义 */

export interface RefinementTask {
  id: string;
  draft_id: string;
  title: string;
  status: 'editing' | 'saved' | 'exported' | 'active';
  current_page_index?: number;  // 可选，默认从0开始
  total_pages?: number;
  version?: string;
  created_at: string;
  updated_at: string;
}

export interface RefinedPage {
  id?: string;
  page_index: number;
  slide_id?: string;
  title?: string;
  source_document_id?: string;
  source_page_number?: number;
  current_content?: SlideContent;
  thumbnail_path?: string;
  version?: number;
  modification_count?: number;
  elements?: SlideElement[];
}

export interface SlideContent {
  elements: SlideElement[];
  background?: BackgroundInfo;
  layout?: LayoutInfo;
}

export interface SlideElement {
  id: string;
  type: 'text' | 'image' | 'table' | 'chart' | 'shape';
  bbox: BoundingBox;
  content: any;
  style: ElementStyle;
  zIndex: number;
}

export interface BoundingBox {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface ElementStyle {
  font_family?: string;
  font_size?: number;
  color?: string;
  bold?: boolean;
  italic?: boolean;
  alignment?: 'left' | 'center' | 'right' | 'justify';
}

export interface BackgroundInfo {
  type?: string;
  color?: string;
  image?: string;
}

export interface LayoutInfo {
  type?: string;
  width?: number;
  height?: number;
}

export interface TextElement extends SlideElement {
  type: 'text';
  content: {
    text: string;
    paragraphs?: Paragraph[];
  };
}

export interface Paragraph {
  text: string;
  level?: number;
  bullet?: string;
}

export interface TableElement extends SlideElement {
  type: 'table';
  content: {
    rows: number;
    cols: number;
    cells: TableCell[][];
    header_row?: boolean;
  };
}

export interface TableCell {
  text: string;
  row_span?: number;
  col_span?: number;
  background_color?: string;
  font_size?: number;
}

export interface RefinementMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  type: 'chat' | 'modification' | 'suggestion';
  page_index?: number;
  modification?: ModificationRecord;
  timestamp: string;
}

export interface ModificationRecord {
  id: string;
  type: ModificationType;
  description: string;
  element_id?: string;
  before: any;
  after: any;
  page_version: number;
}

export enum ModificationType {
  EDIT_TEXT = 'edit_text',
  REPLACE_IMAGE = 'replace_image',
  EDIT_TABLE = 'edit_table',
  ADD_ELEMENT = 'add_element',
  DELETE_ELEMENT = 'delete_element',
  MOVE_ELEMENT = 'move_element',
  RESIZE_ELEMENT = 'resize_element',
  CHANGE_STYLE = 'change_style',
  CHANGE_LAYOUT = 'change_layout',
}

export interface CommandResult {
  success: boolean;
  message: string;
  modification?: ModificationRecord;
  updated_page?: RefinedPage;
  needs_clarification?: boolean;
}

export interface RefinementSuggestion {
  id: string;
  type: string;
  description: string;
  element_id?: string;
  action: string;
  preview?: any;
}

export interface QuickAction {
  icon: string;
  label: string;
  command: string;
}

export interface TaskDetail {
  // 后端直接返回任务对象（不是嵌套在 task 字段中）
  id: string;
  draft_id: string;
  title: string;
  status: 'editing' | 'saved' | 'exported' | 'active';
  total_pages: number;
  version: string;
  pages: RefinedPage[];
  exported_file_path?: string;
  created_at: string;
  updated_at: string;
}
