import { Dialog, Tag, Divider } from 'tdesign-react';
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

interface SlideDetailModalProps {
  visible: boolean;
  slide: SlidePreview | null;
  documentTitle: string;
  onClose: () => void;
}

export default function SlideDetailModal({
  visible,
  slide,
  documentTitle,
  onClose,
}: SlideDetailModalProps) {
  if (!slide) return null;

  return (
    <Dialog
      visible={visible}
      header={`${documentTitle} - Page ${slide.page_number}`}
      onClose={onClose}
      footer={false}
      width={800}
      closeOnOverlayClick
      closeOnEscKeydown
    >
      <div className="slide-detail-modal">
        {/* Thumbnail Preview */}
        <div className="slide-detail-preview">
          {slide.thumbnail_url ? (
            <img
              src={slide.thumbnail_url}
              alt={`Page ${slide.page_number}`}
              className="slide-detail-image"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
              }}
            />
          ) : (
            <div className="slide-detail-placeholder">
              <span>Page {slide.page_number}</span>
            </div>
          )}
        </div>

        <Divider />

        {/* Slide Info */}
        <div className="slide-detail-info">
          <div className="slide-detail-meta">
            <Tag theme="primary" variant="light">
              Page {slide.page_number}
            </Tag>
            {slide.layout_type && (
              <Tag variant="light">{slide.layout_type}</Tag>
            )}
            {slide.is_vectorized === 1 && (
              <Tag theme="success" variant="light" icon={<CheckCircleFilledIcon />}>
                Vectorized
              </Tag>
            )}
          </div>

          {/* Title */}
          {slide.title && (
            <div className="slide-detail-section">
              <h4 className="slide-detail-label">Title</h4>
              <p className="slide-detail-title-text">{slide.title}</p>
            </div>
          )}

          {/* Full Content */}
          <div className="slide-detail-section">
            <h4 className="slide-detail-label">Content</h4>
            <div className="slide-detail-content-text">
              {slide.content_text || 'No text content on this page.'}
            </div>
          </div>
        </div>
      </div>
    </Dialog>
  );
}
