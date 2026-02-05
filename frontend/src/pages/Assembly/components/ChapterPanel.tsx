import { Card, Button, Space, Popconfirm, Tag } from 'tdesign-react';
import { RefreshIcon, DeleteIcon } from 'tdesign-icons-react';
import { Chapter } from '../../../types/assembly';
import './ChapterPanel.css';

interface ChapterPanelProps {
  chapter: Chapter;
  selected: boolean;
  onSelect: () => void;
  onRefresh: () => void;
}

export default function ChapterPanel({ chapter, selected, onSelect, onRefresh }: ChapterPanelProps) {
  const handleDelete = async () => {
    const assemblyMockApi = await import('../../../api/assembly.mock');
    await assemblyMockApi.default.deleteChapter(chapter.id);
    onRefresh();
  };

  const handleRegenerate = async () => {
    const assemblyMockApi = await import('../../../api/assembly.mock');
    await assemblyMockApi.default.regenerateChapter(chapter.id);
    onRefresh();
  };

  return (
    <div className={`chapter-panel ${selected ? 'selected' : ''}`} onClick={onSelect}>
      <Card
        title={chapter.title}
        subtitle={<Tag theme="success">{chapter.page_count}页</Tag>}
        actions={
          <Space size="small">
            <Button size="small" variant="text" icon={<RefreshIcon />} onClick={(e) => { e.stopPropagation(); handleRegenerate(); }}>
              重新生成
            </Button>
            <Popconfirm content="确定要删除此章节吗？" onConfirm={handleDelete}>
              <Button size="small" variant="text" theme="danger" icon={<DeleteIcon />} onClick={(e) => e.stopPropagation()}>
                删除
              </Button>
            </Popconfirm>
          </Space>
        }
      >
        <p className="chapter-description">{chapter.description}</p>
        <div className="chapter-meta">
          <span>需求: {chapter.required_pages}页</span>
          <span>实际: {chapter.page_count}页</span>
        </div>
      </Card>
    </div>
  );
}
