import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Button,
  Loading,
  Empty,
  MessagePlugin,
  Tag,
  Breadcrumb,
  Space,
} from 'tdesign-react';
import {
  ChevronLeftIcon,
  FilePowerpointIcon,
  DownloadIcon,
} from 'tdesign-icons-react';
import documentsApi from '../../api/documents';
import SlideCard from './components/SlideCard';
import SlideDetailModal from './components/SlideDetailModal';
import './index.css';

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

interface DocumentPreviewData {
  document_id: string;
  title: string;
  original_filename: string;
  page_count: number;
  status: string;
  cos_url: string | null;
  slides: SlidePreview[];
  total: number;
}

export default function DocumentDetail() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DocumentPreviewData | null>(null);
  const [selectedSlide, setSelectedSlide] = useState<SlidePreview | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  useEffect(() => {
    if (documentId) {
      loadPreviewData(documentId);
    }
  }, [documentId]);

  const loadPreviewData = async (docId: string) => {
    setLoading(true);
    try {
      const response = await documentsApi.getDocumentSlidesPreview(docId);
      setData(response);
    } catch (error: any) {
      console.error('Failed to load preview data:', error);
      const msg = error?.response?.data?.detail || 'Failed to load document preview';
      MessagePlugin.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSlideClick = (slide: SlidePreview) => {
    setSelectedSlide(slide);
    setModalVisible(true);
  };

  const handleCloseModal = () => {
    setModalVisible(false);
    setSelectedSlide(null);
  };

  const handleBack = () => {
    navigate('/library');
  };

  const handleDownload = () => {
    if (!documentId) return;
    const url = documentsApi.getDocumentFileUrl(documentId);
    const link = document.createElement('a');
    link.href = url;
    link.download = (data?.original_filename || 'document') + '.pptx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (loading) {
    return (
      <div className="document-detail-page">
        <div className="loading-container">
          <Loading size="large" />
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="document-detail-page">
        <Empty description="Document not found" />
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Button onClick={handleBack}>Back to Library</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="document-detail-page">
      {/* Header */}
      <div className="detail-header">
        <div className="detail-header-left">
          <Button
            variant="text"
            icon={<ChevronLeftIcon />}
            onClick={handleBack}
          >
            Back
          </Button>
          <Breadcrumb>
            <Breadcrumb.BreadcrumbItem onClick={handleBack} style={{ cursor: 'pointer' }}>
              Document Library
            </Breadcrumb.BreadcrumbItem>
            <Breadcrumb.BreadcrumbItem>
              {data.title}
            </Breadcrumb.BreadcrumbItem>
          </Breadcrumb>
        </div>
        <Space>
          <Button
            icon={<DownloadIcon />}
            onClick={handleDownload}
          >
            Download
          </Button>
        </Space>
      </div>

      {/* Document Info */}
      <div className="detail-info">
        <div className="detail-info-main">
          <FilePowerpointIcon size="32px" style={{ color: '#D24726', flexShrink: 0 }} />
          <div className="detail-info-text">
            <h2 className="detail-title">{data.title}</h2>
            <div className="detail-meta">
              <Tag theme="primary" variant="light">{data.page_count} pages</Tag>
              <Tag theme="success" variant="light">{data.status}</Tag>
              <span className="detail-filename">{data.original_filename}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Slides Grid */}
      <div className="slides-section">
        <h3 className="slides-section-title">
          Page Overview ({data.total} pages)
        </h3>
        {data.slides.length === 0 ? (
          <Empty description="No pages found" />
        ) : (
          <div className="slides-grid">
            {data.slides.map((slide) => (
              <SlideCard
                key={slide.id}
                slide={slide}
                onClick={() => handleSlideClick(slide)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Slide Detail Modal */}
      <SlideDetailModal
        visible={modalVisible}
        slide={selectedSlide}
        documentTitle={data.title}
        onClose={handleCloseModal}
      />
    </div>
  );
}
