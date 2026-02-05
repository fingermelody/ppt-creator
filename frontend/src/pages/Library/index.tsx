import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Row, Col, Upload, Dialog, Tag, Space, Loading, Empty } from 'tdesign-react';
import { UploadIcon, EditIcon, BrowseIcon, DeleteIcon } from 'tdesign-icons-react';
import documentsApi from '../../api/documents.mock';
import { Document } from '../../types/document';
import './index.css';

export default function Library() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

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

  const handleUpload = async (file: File) => {
    setUploadProgress(0);
    setUploadModalVisible(true);

    try {
      const CHUNK_SIZE = 5 * 1024 * 1024;
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

      const initRes = await documentsApi.initUpload(file.name, file.size, totalChunks);
      const uploadId = initRes.upload_id;

      for (let i = 0; i < totalChunks; i++) {
        const start = i * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);

        await documentsApi.uploadChunk(uploadId, i, chunk);
        setUploadProgress(Math.round(((i + 1) / totalChunks) * 100));
      }

      await documentsApi.completeUpload({
        upload_id: uploadId,
        title: file.name.replace('.pptx', ''),
      });

      await loadDocuments();
      setUploadModalVisible(false);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploadProgress(0);
    }
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
        <Row gutter={[20, 20]}>
          {documents.map((doc) => (
            <Col key={doc.id} span={3}>
              <Card
                hoverShadow
                cover={doc.thumbnail || 'https://via.placeholder.com/300x200?text=PPT'}
                title={doc.title}
                subtitle={getStatusTag(doc.status)}
                actions={
                  <Space>
                    <Button
                      size="small"
                      variant="text"
                      icon={<BrowseIcon />}
                      disabled={doc.status !== 'ready'}
                    >
                      查看
                    </Button>
                    <Button
                      size="small"
                      variant="text"
                      theme="danger"
                      icon={<DeleteIcon />}
                      onClick={() => handleDelete(doc.id)}
                    >
                      删除
                    </Button>
                  </Space>
                }
              >
                <div className="document-info">
                  <p>页数: {doc.page_count}</p>
                  <p>上传: {new Date(doc.created_at).toLocaleDateString()}</p>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      <Dialog
        header="上传中"
        visible={uploadModalVisible}
        footer={null}
        closeOnOverlayClick={false}
        closeOnEscKeydown={false}
        onClose={() => setUploadModalVisible(false)}
      >
        <div className="upload-progress">
          <Loading size="large" />
          <p>上传进度: {uploadProgress}%</p>
        </div>
      </Dialog>
    </div>
  );
}
