import { Card, Badge } from 'tdesign-react';
import { RefinedPage } from '../../../types/refinement';
import './PageList.css';

interface PageListProps {
  pages: RefinedPage[];
  currentPageIndex: number | null;
  onPageSelect: (pageIndex: number) => void;
}

export default function PageList({ pages, currentPageIndex, onPageSelect }: PageListProps) {
  return (
    <div className="page-list">
      {pages.map((page) => (
        <div
          key={page.page_index}
          className={`page-item ${currentPageIndex === page.page_index ? 'selected' : ''}`}
          onClick={() => onPageSelect(page.page_index)}
        >
          <Card hoverShadow>
            <div className="page-item-content">
              <div className="page-thumbnail">
                <span className="page-number">{page.page_index + 1}</span>
              </div>
              <div className="page-info">
                {/* 优先显示章节标题，其次显示页面标题 */}
                <span className="page-title">
                  {page.section_title || page.title || `页面 ${page.page_index + 1}`}
                </span>
                {/* 如果有章节标题且页面标题不同，显示页面标题作为副标题 */}
                {page.section_title && page.title && page.section_title !== page.title && (
                  <span className="page-subtitle">{page.title}</span>
                )}
                <div className="page-meta">
                  {(page.modification_count ?? 0) > 0 && (
                    <Badge count={page.modification_count} />
                  )}
                </div>
              </div>
            </div>
          </Card>
        </div>
      ))}
    </div>
  );
}
