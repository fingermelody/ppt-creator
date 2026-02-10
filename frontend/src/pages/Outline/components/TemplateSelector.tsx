import { Dialog } from 'tdesign-react';
import type { OutlineTemplate } from '../../../types/outline';

interface TemplateSelectorProps {
  visible: boolean;
  templates: OutlineTemplate[];
  onSelect: (template: OutlineTemplate) => void;
  onClose: () => void;
}

// 模板图标映射
const templateIcons: Record<string, string> = {
  'product_intro': '🚀',
  'work_report': '📊',
  'training': '📚',
  'project_proposal': '💡',
  'tech_sharing': '🔬',
};

export default function TemplateSelector({
  visible,
  templates = [],
  onSelect,
  onClose,
}: TemplateSelectorProps) {
  return (
    <Dialog
      header="选择大纲模板"
      visible={visible}
      footer={false}
      onClose={onClose}
      width={800}
      className="template-dialog"
    >
      <div className="template-grid">
        {templates?.map((template) => (
          <div
            key={template.id}
            className="template-item"
            onClick={() => onSelect(template)}
          >
            <div className="template-icon">
              {templateIcons[template.id] || '📄'}
            </div>
            <div className="template-name">{template.name}</div>
            <div className="template-desc">{template.description}</div>
            <div className="template-chapters-count">
              包含 {template.default_chapters?.length || 0} 个章节模板
            </div>
          </div>
        ))}
      </div>

      {(!templates || templates.length === 0) && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#8f959e' }}>
          暂无可用模板
        </div>
      )}
    </Dialog>
  );
}
