import { Card, Button, Space, Tag, Tooltip } from 'tdesign-react';
import { SwapIcon, DeleteIcon } from 'tdesign-icons-react';
import { ChapterPage } from '../../../types/assembly';
import './SlidePreview.css';

interface SlidePreviewProps {
  page: ChapterPage;
  chapterId: string;
  draftId: string;
  onRefresh: () => void;
}

export default function SlidePreview({ page, chapterId, draftId, onRefresh }: SlidePreviewProps) {
  const handleShowAlternatives = async () => {
    console.log('Show alternatives for:', page.slide_id);
  };

  const handleDelete = async () => {
    const assemblyMockApi = await import('../../../api/assembly.mock');
    await assemblyMockApi.default.deletePage(draftId, chapterId, page.slide_id);
    onRefresh();
  };

  return (
    <div className="slide-preview">
      <Card
        hoverShadow
        cover={page.thumbnail || 'https://via.placeholder.com/300x200?text=Slide'}
        actions={
          <Space size="small">
            <Button
              size="small"
              variant="text"
              icon={<SwapIcon />}
              onClick={handleShowAlternatives}
            >
              查看备选
            </Button>
            <Button
              size="small"
              variant="text"
              theme="danger"
              icon={<DeleteIcon />}
              onClick={handleDelete}
            >
              删除
            </Button>
          </Space>
        }
      >
        <div className="slide-info">
          <Tooltip content={page.document_title}>
            <p className="document-title">{page.document_title}</p>
          </Tooltip>
          <p className="page-number">第{page.page_number}页</p>
          <div className="similarity">
            <Tag theme="success">{page.similarity.toFixed(1)}%</Tag>
          </div>
        </div>
      </Card>
    </div>
  );
}
