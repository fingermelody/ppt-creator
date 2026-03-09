import { Card, Button, Space, Tag, Tooltip } from 'tdesign-react';
import { SwapIcon, DeleteIcon, FileIcon } from 'tdesign-icons-react';
import { ChapterPage } from '../../../types/assembly';
import assemblyApi from '../../../api/assembly';
import './SlidePreview.css';

interface SlidePreviewProps {
  page: ChapterPage;
  chapterId: string;
  draftId: string;
  pageIndex: number;  // 添加页面索引，用于生成不同的颜色
  onRefresh: () => void;
}

// 预定义的颜色方案，用于区分不同页面
const PLACEHOLDER_COLORS = [
  { bg: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', text: '#fff' },
  { bg: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)', text: '#fff' },
  { bg: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)', text: '#fff' },
  { bg: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)', text: '#fff' },
  { bg: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)', text: '#fff' },
  { bg: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)', text: '#333' },
  { bg: 'linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)', text: '#333' },
  { bg: 'linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)', text: '#333' },
  { bg: 'linear-gradient(135deg, #667eea 0%, #f093fb 100%)', text: '#fff' },
  { bg: 'linear-gradient(135deg, #3f51b5 0%, #2196f3 100%)', text: '#fff' },
];

export default function SlidePreview({ page, chapterId, draftId, pageIndex, onRefresh }: SlidePreviewProps) {
  const handleShowAlternatives = async () => {
    console.log('Show alternatives for:', page.slide_id);
  };

  const handleDelete = async () => {
    await assemblyApi.deletePage(draftId, chapterId, page.slide_id);
    onRefresh();
  };

  // 检查是否有有效的缩略图
  const hasThumbnail = page.thumbnail && page.thumbnail.trim() !== '';
  
  // 检查是否已绑定源素材
  const hasBoundSource = page.document_id && page.document_id.trim() !== '';
  
  // 根据页面索引获取颜色方案
  const colorScheme = PLACEHOLDER_COLORS[pageIndex % PLACEHOLDER_COLORS.length];

  // 渲染封面内容
  const renderCover = () => {
    if (hasThumbnail) {
      return <img src={page.thumbnail} alt={page.document_title} />;
    }
    
    // 如果没有缩略图，显示增强的占位内容
    return (
      <div 
        className="slide-placeholder enhanced"
        style={{ background: colorScheme.bg }}
      >
        <div className="placeholder-content" style={{ color: colorScheme.text }}>
          <div className="page-index-badge">
            {page.order + 1}
          </div>
          <div className="placeholder-title">
            {page.document_title || '未命名页面'}
          </div>
          {page.content_summary && (
            <div className="placeholder-summary">
              {page.content_summary.slice(0, 50)}
              {page.content_summary.length > 50 ? '...' : ''}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className={`slide-preview ${!hasBoundSource ? 'unmatched' : ''}`}>
      <Card
        hoverShadow
        cover={renderCover()}
        actions={
          <Space size="small">
            <Button
              size="small"
              variant="text"
              icon={<SwapIcon />}
              onClick={handleShowAlternatives}
            >
              {hasBoundSource ? '查看备选' : '选择素材'}
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
          <Tooltip content={page.document_title || '未命名'}>
            <p className="document-title">{page.document_title || '未命名'}</p>
          </Tooltip>
          <p className="page-number">第{page.page_number}页</p>
          <div className="similarity">
            {hasBoundSource ? (
              <Tag theme="success">{page.similarity.toFixed(1)}%</Tag>
            ) : (
              <Tag theme="warning">待匹配</Tag>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
