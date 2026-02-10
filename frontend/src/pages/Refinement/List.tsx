import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  Row,
  Col,
  Input,
  Space,
  Tag,
  DialogPlugin,
  MessagePlugin,
  Loading,
  Tabs,
} from 'tdesign-react';
import {
  SearchIcon,
  AddIcon,
  EditIcon,
  DeleteIcon,
  DownloadIcon,
  TimeIcon,
  FileIcon,
} from 'tdesign-icons-react';
import assemblyApi from '../../api/assembly.mock';
import refinementApi from '../../api/refinement.mock';
import './List.css';

interface RefinementItem {
  id: string;
  title: string;
  status: 'editing' | 'saved' | 'exported';
  page_count: number;
  modification_count: number;
  created_at: string;
  updated_at: string;
  draft_id: string;
}

interface DraftItem {
  id: string;
  title: string;
  total_pages: number;
  chapter_count: number;
  status: string;
  updated_at: string;
}

const { TabPanel } = Tabs;

export default function RefinementList() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('tasks');
  const [searchValue, setSearchValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [refinementTasks, setRefinementTasks] = useState<RefinementItem[]>([]);
  const [drafts, setDrafts] = useState<DraftItem[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // 加载已有的精修任务（模拟数据）
      const mockTasks: RefinementItem[] = [
        {
          id: 'task-001',
          title: '新产品发布会PPT',
          status: 'editing',
          page_count: 5,
          modification_count: 3,
          created_at: '2026-02-01T10:00:00Z',
          updated_at: '2026-02-08T15:30:00Z',
          draft_id: 'draft-002',
        },
        {
          id: 'task-002',
          title: '年度工作总结',
          status: 'saved',
          page_count: 12,
          modification_count: 8,
          created_at: '2026-02-05T09:00:00Z',
          updated_at: '2026-02-07T18:00:00Z',
          draft_id: 'draft-001',
        },
      ];
      setRefinementTasks(mockTasks);

      // 加载可用于精修的草稿
      const draftsResponse = await assemblyApi.getDrafts();
      const completedDrafts = (draftsResponse.drafts || [])
        .filter((d: any) => d.total_pages > 0)
        .map((d: any) => ({
          id: d.id,
          title: d.title,
          total_pages: d.total_pages,
          chapter_count: d.chapters?.length || 0,
          status: d.status,
          updated_at: d.updated_at,
        }));
      setDrafts(completedDrafts);
    } catch (error) {
      console.error('Failed to load data:', error);
      MessagePlugin.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFromDraft = async (draftId: string, draftTitle: string) => {
    try {
      const response = await refinementApi.createTask(draftId, draftTitle);
      MessagePlugin.success('精修任务创建成功');
      navigate(`/refinement/${response.task_id}`);
    } catch (error) {
      console.error('Failed to create refinement task:', error);
      MessagePlugin.error('创建精修任务失败');
    }
  };

  const handleOpenTask = (taskId: string) => {
    navigate(`/refinement/${taskId}`);
  };

  const handleDeleteTask = (taskId: string, taskTitle: string) => {
    const dialog = DialogPlugin.confirm({
      header: '确认删除',
      body: `确定要删除精修任务"${taskTitle}"吗？此操作不可恢复。`,
      confirmBtn: { theme: 'danger', content: '删除' },
      onConfirm: async () => {
        try {
          // 模拟删除
          setRefinementTasks((prev) => prev.filter((t) => t.id !== taskId));
          MessagePlugin.success('删除成功');
          dialog.destroy();
        } catch (error) {
          MessagePlugin.error('删除失败');
        }
      },
    });
  };

  const handleExportTask = async (taskId: string) => {
    try {
      const response = await refinementApi.exportRefinedPPT(taskId);
      window.open(response.download_url, '_blank');
      MessagePlugin.success('导出成功');
    } catch (error) {
      MessagePlugin.error('导出失败');
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { theme: 'primary' | 'success' | 'warning'; label: string }> = {
      editing: { theme: 'primary', label: '编辑中' },
      saved: { theme: 'success', label: '已保存' },
      exported: { theme: 'warning', label: '已导出' },
    };
    const config = statusMap[status] || { theme: 'primary', label: status };
    return <Tag theme={config.theme}>{config.label}</Tag>;
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const filteredTasks = refinementTasks.filter((task) =>
    task.title.toLowerCase().includes(searchValue.toLowerCase())
  );

  const filteredDrafts = drafts.filter((draft) =>
    draft.title.toLowerCase().includes(searchValue.toLowerCase())
  );

  if (loading) {
    return (
      <div className="refinement-list-page loading">
        <Loading size="large" />
      </div>
    );
  }

  return (
    <div className="refinement-list-page">
      <div className="page-header">
        <h1>PPT精修</h1>
        <p className="page-description">
          通过AI对话方式精细调整PPT内容，支持文本编辑、表格修改、样式调整等操作
        </p>
      </div>

      <div className="page-toolbar">
        <Input
          value={searchValue}
          onChange={(value) => setSearchValue(String(value))}
          placeholder="搜索精修任务或草稿..."
          prefixIcon={<SearchIcon />}
          clearable
          style={{ width: 300 }}
        />
      </div>

      <Tabs value={activeTab} onChange={(val) => setActiveTab(String(val))}>
        <TabPanel value="tasks" label="精修任务">
          <div className="tab-content">
            {filteredTasks.length === 0 ? (
              <div className="empty-container">
                <div className="empty-text">暂无精修任务，请从草稿创建</div>
                <Button
                  theme="primary"
                  icon={<AddIcon />}
                  onClick={() => setActiveTab('drafts')}
                >
                  从草稿创建
                </Button>
              </div>
            ) : (
              <Row gutter={[16, 16]}>
                {filteredTasks.map((task) => (
                  <Col key={task.id} xs={12} sm={8} md={6} lg={6} xl={4}>
                    <div onClick={() => handleOpenTask(task.id)} style={{ cursor: 'pointer' }}>
                      <Card
                        className="task-card"
                        hoverShadow
                        title={
                          <div className="card-header">
                            <span className="card-title" title={task.title}>
                              {task.title}
                            </span>
                            {getStatusTag(task.status)}
                          </div>
                        }
                        description={
                          <div className="card-body">
                            <div className="task-info">
                              <div className="info-item">
                                <FileIcon />
                                <span>{task.page_count} 页</span>
                              </div>
                              <div className="info-item">
                                <EditIcon />
                                <span>{task.modification_count} 次修改</span>
                              </div>
                            </div>
                            <div className="task-time">
                              <TimeIcon />
                              <span>{formatDate(task.updated_at)}</span>
                            </div>
                          </div>
                        }
                        actions={
                          <div className="card-footer">
                            <Space>
                              <Button
                                size="small"
                                variant="text"
                                icon={<EditIcon />}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleOpenTask(task.id);
                                }}
                              >
                                编辑
                              </Button>
                              <Button
                                size="small"
                                variant="text"
                                icon={<DownloadIcon />}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleExportTask(task.id);
                                }}
                              >
                                导出
                              </Button>
                              <Button
                                size="small"
                                variant="text"
                                theme="danger"
                                icon={<DeleteIcon />}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteTask(task.id, task.title);
                                }}
                              >
                                删除
                              </Button>
                            </Space>
                          </div>
                        }
                      />
                    </div>
                  </Col>
                ))}
              </Row>
            )}
          </div>
        </TabPanel>

        <TabPanel value="drafts" label="从草稿创建">
          <div className="tab-content">
            {filteredDrafts.length === 0 ? (
              <div className="empty-container">
                <div className="empty-text">暂无可用草稿</div>
                <Button theme="primary" onClick={() => navigate('/assembly')}>
                  去创建PPT草稿
                </Button>
              </div>
            ) : (
              <Row gutter={[16, 16]}>
                {filteredDrafts.map((draft) => (
                  <Col key={draft.id} xs={12} sm={8} md={6} lg={6} xl={4}>
                    <Card
                      className="draft-card"
                      hoverShadow
                      title={
                        <div className="card-header">
                          <span className="card-title" title={draft.title}>
                            {draft.title}
                          </span>
                          <Tag theme="default">{draft.status === 'completed' ? '已完成' : '草稿'}</Tag>
                        </div>
                      }
                      description={
                        <div className="card-body">
                          <div className="draft-info">
                            <div className="info-item">
                              <FileIcon />
                              <span>{draft.total_pages} 页</span>
                            </div>
                            <div className="info-item">
                              <span>{draft.chapter_count} 个章节</span>
                            </div>
                          </div>
                          <div className="draft-time">
                            <TimeIcon />
                            <span>{formatDate(draft.updated_at)}</span>
                          </div>
                        </div>
                      }
                      actions={
                        <div className="card-footer">
                          <Button
                            theme="primary"
                            icon={<AddIcon />}
                            onClick={() => handleCreateFromDraft(draft.id, draft.title)}
                          >
                            创建精修任务
                          </Button>
                        </div>
                      }
                    />
                  </Col>
                ))}
              </Row>
            )}
          </div>
        </TabPanel>
      </Tabs>
    </div>
  );
}
