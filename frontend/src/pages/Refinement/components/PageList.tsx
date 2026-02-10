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
                <p className="page-source">来源: 第{page.source_page_number}页</p>
                <div className="page-meta">
                  {page.modification_count > 0 && (
                    <Badge count={page.modification_count} />
                  )}
                  <span className="page-version">v{page.version}</span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      ))}
    </div>
  );
}
