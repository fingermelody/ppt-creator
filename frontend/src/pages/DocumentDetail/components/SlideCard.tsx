import { Tag } from 'tdesign-react';
import { CheckCircleFilledIcon } from 'tdesign-icons-react';

interface SlidePreview {
  id: string;
  page_number: number;
  title: string | null;
  summary: string;
  content_text: string | null;
  thumbnail_url: string | null;
  layout_type: string | null;
  is_vectorized: number;
}

interface SlideCardProps {
  slide: SlidePreview;
  onClick: () => void;
}

export default function SlideCard({ slide, onClick }: SlideCardProps) {
  return (
    <div className="slide-card" onClick={onClick}>
      {/* Thumbnail */}
      <div className="slide-card-thumbnail">
        {slide.thumbnail_url ? (
          <img
            src={slide.thumbnail_url}
            alt={`Page ${slide.page_number}`}
            loading="lazy"
            onError={(e) => {
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              const parent = target.parentElement;
              if (parent) {
                const placeholder = parent.querySelector('.slide-card-placeholder');
                if (placeholder) {
                  (placeholder as HTMLElement).style.display = 'flex';
                }
              }
            }}
          />
        ) : null}
        <div
          className="slide-card-placeholder"
          style={{ display: slide.thumbnail_url ? 'none' : 'flex' }}
        >
          <span className="slide-card-page-large">{slide.page_number}</span>
        </div>
      </div>

      {/* Content */}
      <div className="slide-card-content">
        <div className="slide-card-header">
          <span className="slide-card-page-num">P{slide.page_number}</span>
          {slide.is_vectorized === 1 && (
            <CheckCircleFilledIcon size="14px" style={{ color: '#00a870' }} />
          )}
        </div>
        <div className="slide-card-title">
          {slide.title || `Page ${slide.page_number}`}
        </div>
        {slide.summary && (
          <div className="slide-card-summary">{slide.summary}</div>
        )}
        {slide.layout_type && (
          <Tag size="small" variant="light" style={{ marginTop: 4 }}>
            {slide.layout_type}
          </Tag>
        )}
      </div>
    </div>
  );
}
