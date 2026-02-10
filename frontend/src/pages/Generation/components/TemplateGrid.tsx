/* 模板网格组件 */

import { Tag, Tooltip } from 'tdesign-react';
import { CheckCircleIcon, StarIcon } from 'tdesign-icons-react';
import type { PPTTemplate } from '../../../types/generation';
import { TEMPLATE_CATEGORY_NAMES } from '../../../types/generation';
import './TemplateGrid.css';

interface TemplateGridProps {
  templates: PPTTemplate[];
  selectedId?: string;
  onSelect: (template: PPTTemplate) => void;
}

export default function TemplateGrid({ templates, selectedId, onSelect }: TemplateGridProps) {
  if (templates.length === 0) {
    return (
      <div className="template-grid-empty">
        <p>暂无可用模板</p>
      </div>
    );
  }

  return (
    <div className="template-grid">
      {templates.map((template) => (
        <div
          key={template.id}
          className={`template-item ${selectedId === template.id ? 'selected' : ''}`}
          onClick={() => onSelect(template)}
        >
          {/* 选中标记 */}
          {selectedId === template.id && (
            <div className="selected-badge">
              <CheckCircleIcon />
            </div>
          )}

          {/* 高级标记 */}
          {template.is_premium && (
            <div className="premium-badge">
              <StarIcon />
            </div>
          )}

          {/* 预览图 */}
          <div className="template-preview">
            <img
              src={template.thumbnail_url}
              alt={template.name}
              loading="lazy"
            />
          </div>

          {/* 模板信息 */}
          <div className="template-info">
            <Tooltip content={template.name}>
              <h4 className="template-name">{template.name}</h4>
            </Tooltip>
            <div className="template-meta">
              <Tag size="small" variant="light">
                {TEMPLATE_CATEGORY_NAMES[template.category]}
              </Tag>
              <span className="usage-count">{template.usage_count} 次使用</span>
            </div>
          </div>

          {/* 配色预览 */}
          <div className="color-scheme">
            <span
              className="color-dot"
              style={{ backgroundColor: template.color_scheme.primary }}
              title="主色"
            />
            <span
              className="color-dot"
              style={{ backgroundColor: template.color_scheme.secondary }}
              title="辅色"
            />
            <span
              className="color-dot"
              style={{ backgroundColor: template.color_scheme.accent }}
              title="强调色"
            />
          </div>
        </div>
      ))}
    </div>
  );
}
