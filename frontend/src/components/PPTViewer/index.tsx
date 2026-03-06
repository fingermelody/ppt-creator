import { useState, useEffect } from 'react';
import {
  Dialog,
  Button,
  Loading,
  Space,
  MessagePlugin,
} from 'tdesign-react';
import {
  FullscreenIcon,
  FullscreenExitIcon,
  DownloadIcon,
  RefreshIcon,
} from 'tdesign-icons-react';
import './index.css';

interface PPTViewerProps {
  visible: boolean;
  fileUrl: string;
  fileName?: string;
  onClose: () => void;
  onDownload?: () => void;
}

export default function PPTViewer({
  visible,
  fileUrl,
  fileName = '演示文稿',
  onClose,
  onDownload,
}: PPTViewerProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // 预览 URL（后端已添加数据万象参数，直接使用）
  const previewUrl = fileUrl || '';

  useEffect(() => {
    if (visible && fileUrl) {
      setLoading(true);
      setError(null);
    }
  }, [visible, fileUrl]);

  const handleIframeLoad = () => {
    setLoading(false);
    setError(null);
  };

  const handleIframeError = () => {
    setLoading(false);
    setError('预览加载失败，请检查文件链接或网络连接');
    MessagePlugin.error('预览加载失败');
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    // 强制刷新 iframe
    const iframe = document.querySelector('.ppt-viewer-iframe') as HTMLIFrameElement;
    if (iframe) {
      iframe.src = previewUrl;
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleDownload = () => {
    if (onDownload) {
      onDownload();
    } else if (fileUrl) {
      const link = document.createElement('a');
      link.href = fileUrl;
      link.download = fileName || 'presentation.pptx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleClose = () => {
    setLoading(true);
    setError(null);
    setIsFullscreen(false);
    onClose();
  };

  return (
    <Dialog
      header={fileName}
      visible={visible}
      onClose={handleClose}
      width={isFullscreen ? '100vw' : '90vw'}
      placement="center"
      className={`ppt-viewer-dialog ${isFullscreen ? 'fullscreen' : ''}`}
      footer={null}
      destroyOnClose={false}
      showOverlay={!isFullscreen}
    >
      <div className="ppt-viewer-container">
        {/* 工具栏 */}
        <div className="ppt-viewer-toolbar">
          <Space size="small">
            <Button
              variant="outline"
              icon={<RefreshIcon />}
              onClick={handleRefresh}
              disabled={loading}
            >
              刷新
            </Button>
            <Button
              variant="outline"
              icon={isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
              onClick={toggleFullscreen}
            >
              {isFullscreen ? '退出全屏' : '全屏'}
            </Button>
            {onDownload && (
              <Button
                theme="primary"
                icon={<DownloadIcon />}
                onClick={handleDownload}
              >
                下载 PPT
              </Button>
            )}
          </Space>
        </div>

        {/* 预览区域 */}
        <div className="ppt-viewer-content">
          {loading && (
            <div className="ppt-viewer-loading">
              <Loading text="正在加载预览..." size="large" />
            </div>
          )}

          {error && (
            <div className="ppt-viewer-error">
              <p>{error}</p>
              <Button
                theme="primary"
                icon={<RefreshIcon />}
                onClick={handleRefresh}
              >
                重试
              </Button>
            </div>
          )}

          {previewUrl && !error && (
            <iframe
              className="ppt-viewer-iframe"
              src={previewUrl}
              onLoad={handleIframeLoad}
              onError={handleIframeError}
              title="PPT预览"
              sandbox="allow-scripts allow-same-origin allow-popups"
            />
          )}

          {!fileUrl && !error && (
            <div className="ppt-viewer-empty">
              <p>暂无可预览的文件</p>
            </div>
          )}
        </div>
      </div>
    </Dialog>
  );
}
