import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Button, 
  Table, 
  Upload, 
  Dialog, 
  Tag, 
  Space, 
  Loading, 
  Empty, 
  MessagePlugin,
  Tooltip
} from 'tdesign-react';
import { 
  UploadIcon, 
  EditIcon, 
  BrowseIcon, 
  DeleteIcon, 
  CheckCircleFilledIcon, 
  CloseCircleFilledIcon,
  DownloadIcon,
  FileIcon,
  FilePowerpointIcon
} from 'tdesign-icons-react';
import documentsApi from '../../api/documents';
import { Document } from '../../types/document';
import './index.css';

// 上传状态枚举
type UploadStatus = 'idle' | 'uploading' | 'completing' | 'success' | 'error';

// 格式化文件大小
const formatFileSize = (bytes?: number) => {
  if (!bytes) return '-';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

// 格式化日期
const formatDate = (dateStr: string) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export default function Library() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>('idle');
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  // 预览相关状态
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewDocument, setPreviewDocument] = useState<Document | null>(null);
  
  // 使用 ref 来避免在 finally 中重置进度时的竞态条件
  const uploadAbortedRef = useRef(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await documentsApi.getDocuments({ page: 1, limit: 50 });
      setDocuments(response.documents);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };

  // 重置上传状态
  const resetUploadState = useCallback(() => {
    setUploadProgress(0);
    setUploadStatus('idle');
    setUploadError(null);
    uploadAbortedRef.current = false;
  }, []);

  // 关闭上传弹窗
  const handleCloseUploadModal = useCallback(() => {
    // 如果正在上传中，提示用户
    if (uploadStatus === 'uploading' || uploadStatus === 'completing') {
      MessagePlugin.warning('上传正在进行中，请等待完成');
      return;
    }
    setUploadModalVisible(false);
    // 延迟重置状态，避免闪烁
    setTimeout(resetUploadState, 300);
  }, [uploadStatus, resetUploadState]);

  const handleUpload = async (file: File) => {
    // 重置状态
    resetUploadState();
    setUploadModalVisible(true);
    setUploadStatus('uploading');

    try {
      const CHUNK_SIZE = 5 * 1024 * 1024;
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

      // 1. 初始化上传
      const initRes = await documentsApi.initUpload(file.name, file.size, totalChunks);
      const uploadId = initRes.upload_id;

      // 检查是否被中断
      if (uploadAbortedRef.current) {
        return;
      }

      // 2. 上传分片
      for (let i = 0; i < totalChunks; i++) {
        // 检查是否被中断
        if (uploadAbortedRef.current) {
          return;
        }

        const start = i * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);

        await documentsApi.uploadChunk(uploadId, i, chunk);
        
        // 分片上传完成，更新进度（最多到 95%，留 5% 给完成阶段）
        const progress = Math.round(((i + 1) / totalChunks) * 95);
        setUploadProgress(progress);
      }

      // 检查是否被中断
      if (uploadAbortedRef.current) {
        return;
      }

      // 3. 完成上传
      setUploadStatus('completing');
      setUploadProgress(98); // 表示正在处理
      
      await documentsApi.completeUpload({
        upload_id: uploadId,
        title: file.name.replace(/\.(pptx|ppt)$/i, ''),
      });

      // 4. 上传成功
      setUploadProgress(100);
      setUploadStatus('success');
      MessagePlugin.success('上传成功！');
      
      // 刷新文档列表
      await loadDocuments();
      
      // 延迟关闭弹窗，让用户看到成功状态
      setTimeout(() => {
        setUploadModalVisible(false);
        resetUploadState();
      }, 1500);

    } catch (error: any) {
      console.error('Upload failed:', error);
      
      // 设置错误状态，但保持当前进度（不重置为 0）
      setUploadStatus('error');
      
      // 提取错误信息
      const errorMessage = error?.response?.data?.detail 
        || error?.response?.data?.message 
        || error?.message 
        || '上传失败，请重试';
      
      setUploadError(errorMessage);
      
      // 错误提示（API client 可能已经显示了，这里记录日志）
      console.error('Upload error details:', errorMessage);
    }
    // 注意：移除 finally 块，不再自动重置进度
    // 进度重置由用户关闭弹窗时触发
  };

  const handleStartAssembly = () => {
    navigate('/assembly');
  };

  const handleDelete = async (documentId: string) => {
    const confirmDialog = Dialog.confirm({
      header: '确认删除',
      body: '确定要删除此文档吗？',
      onConfirm: async () => {
        try {
          await documentsApi.deleteDocument(documentId);
          await loadDocuments();
          confirmDialog.destroy();
        } catch (error) {
          console.error('Delete failed:', error);
        }
      },
    });
  };

  // 预览文档
  const handlePreview = (doc: Document) => {
    setPreviewDocument(doc);
    setPreviewVisible(true);
  };

  // 下载文档
  const handleDownload = (doc: Document) => {
    const url = documentsApi.getDocumentFileUrl(doc.id);
    const link = document.createElement('a');
    link.href = url;
    link.download = doc.title + '.pptx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { theme: 'warning' | 'primary' | 'success' | 'danger' | 'default'; label: string }> = {
      uploading: { theme: 'warning', label: '上传中' },
      parsing: { theme: 'primary', label: '解析中' },
      ready: { theme: 'success', label: '就绪' },
      error: { theme: 'danger', label: '错误' },
    };
    const config = statusMap[status] || { theme: 'default', label: status };
    return <Tag theme={config.theme}>{config.label}</Tag>;
  };

  // 表格列定义
  const columns = [
    {
      colKey: 'title',
      title: '文档名称',
      width: 300,
      cell: ({ row }: { row: Document }) => (
        <div className="document-name-cell">
          <FilePowerpointIcon size="24px" style={{ color: '#D24726', marginRight: '12px', flexShrink: 0 }} />
          <Tooltip content={row.title}>
            <span className="document-title">{row.title}</span>
          </Tooltip>
        </div>
      ),
    },
    {
      colKey: 'page_count',
      title: '页数',
      width: 80,
      align: 'center' as const,
      cell: ({ row }: { row: Document }) => `${row.page_count} 页`,
    },
    {
      colKey: 'file_size',
      title: '大小',
      width: 100,
      align: 'center' as const,
      cell: ({ row }: { row: Document }) => formatFileSize(row.file_size),
    },
    {
      colKey: 'status',
      title: '状态',
      width: 100,
      align: 'center' as const,
      cell: ({ row }: { row: Document }) => getStatusTag(row.status),
    },
    {
      colKey: 'created_at',
      title: '上传时间',
      width: 180,
      cell: ({ row }: { row: Document }) => formatDate(row.created_at),
    },
    {
      colKey: 'actions',
      title: '操作',
      width: 200,
      fixed: 'right' as const,
      cell: ({ row }: { row: Document }) => (
        <Space>
          <Tooltip content="查看">
            <Button
              size="small"
              variant="text"
              shape="circle"
              icon={<BrowseIcon />}
              disabled={row.status !== 'ready'}
              onClick={() => handlePreview(row)}
            />
          </Tooltip>
          <Tooltip content="下载">
            <Button
              size="small"
              variant="text"
              shape="circle"
              icon={<DownloadIcon />}
              disabled={row.status !== 'ready'}
              onClick={() => handleDownload(row)}
            />
          </Tooltip>
          <Tooltip content="删除">
            <Button
              size="small"
              variant="text"
              shape="circle"
              theme="danger"
              icon={<DeleteIcon />}
              onClick={() => handleDelete(row.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="library-page">
      <div className="page-header">
        <h2 className="page-title">文档库</h2>
        <Space>
          <Upload
            theme="custom"
            accept=".pptx,.ppt"
            autoUpload={false}
            onChange={(files) => {
              if (files && files.length > 0) {
                const file = files[0];
                if (file.raw) {
                  handleUpload(file.raw);
                }
              }
            }}
          >
            <Button theme="primary" icon={<UploadIcon />}>
              上传PPT
            </Button>
          </Upload>
          <Button theme="default" icon={<EditIcon />} onClick={handleStartAssembly}>
            开始组装PPT
          </Button>
        </Space>
      </div>

      {loading ? (
        <div className="loading-container">
          <Loading size="large" />
        </div>
      ) : documents.length === 0 ? (
        <Empty description="暂无文档，请上传PPT文件" />
      ) : (
        <div className="document-table-container">
          <Table
            data={documents}
            columns={columns}
            rowKey="id"
            hover
            stripe
            size="medium"
            tableLayout="fixed"
            pagination={{
              pageSize: 20,
              showJumper: true,
              showPageSize: true,
              pageSizeOptions: [10, 20, 50],
            }}
          />
        </div>
      )}

      {/* 上传进度弹窗 */}
      <Dialog
        header={uploadStatus === 'error' ? '上传失败' : uploadStatus === 'success' ? '上传成功' : '上传中'}
        visible={uploadModalVisible}
        footer={uploadStatus === 'error' || uploadStatus === 'success' ? (
          <Button theme="primary" onClick={handleCloseUploadModal}>
            {uploadStatus === 'error' ? '关闭' : '完成'}
          </Button>
        ) : null}
        closeOnOverlayClick={false}
        closeOnEscKeydown={false}
        onClose={handleCloseUploadModal}
      >
        <div className="upload-progress">
          {uploadStatus === 'success' ? (
            <>
              <CheckCircleFilledIcon size="64px" style={{ color: '#00a870' }} />
              <p style={{ marginTop: '16px', color: '#00a870', fontWeight: 500 }}>上传成功！</p>
            </>
          ) : uploadStatus === 'error' ? (
            <>
              <CloseCircleFilledIcon size="64px" style={{ color: '#e34d59' }} />
              <p style={{ marginTop: '16px', color: '#e34d59', fontWeight: 500 }}>
                {uploadError || '上传失败，请重试'}
              </p>
              <p style={{ marginTop: '8px', color: '#999', fontSize: '12px' }}>
                最后进度: {uploadProgress}%
              </p>
            </>
          ) : (
            <>
              <Loading size="large" />
              <p>
                {uploadStatus === 'completing' ? '正在处理文件...' : '上传进度:'} {uploadProgress}%
              </p>
            </>
          )}
        </div>
      </Dialog>

      {/* 预览弹窗 */}
      <Dialog
        header={previewDocument?.title || '文档预览'}
        visible={previewVisible}
        width={600}
        footer={
          <Space>
            <Button onClick={() => setPreviewVisible(false)}>关闭</Button>
            {previewDocument && (
              <Button theme="primary" icon={<DownloadIcon />} onClick={() => handleDownload(previewDocument)}>
                下载文档
              </Button>
            )}
          </Space>
        }
        onClose={() => setPreviewVisible(false)}
      >
        {previewDocument && (
          <div className="preview-content">
            <div className="preview-info">
              <div className="preview-icon">
                <FilePowerpointIcon size="80px" style={{ color: '#D24726' }} />
              </div>
              <div className="preview-details">
                <div className="preview-item">
                  <span className="label">文档名称：</span>
                  <span className="value">{previewDocument.title}</span>
                </div>
                <div className="preview-item">
                  <span className="label">页数：</span>
                  <span className="value">{previewDocument.page_count} 页</span>
                </div>
                <div className="preview-item">
                  <span className="label">文件大小：</span>
                  <span className="value">{formatFileSize(previewDocument.file_size)}</span>
                </div>
                <div className="preview-item">
                  <span className="label">上传时间：</span>
                  <span className="value">{formatDate(previewDocument.created_at)}</span>
                </div>
                <div className="preview-item">
                  <span className="label">状态：</span>
                  <span className="value">{getStatusTag(previewDocument.status)}</span>
                </div>
              </div>
            </div>
            <div className="preview-tip">
              <FileIcon size="16px" />
              <span>PPT 文件需要下载后使用 PowerPoint 或 WPS 打开查看</span>
            </div>
          </div>
        )}
      </Dialog>
    </div>
  );
}
