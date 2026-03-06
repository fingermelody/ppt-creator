import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  Table,
  Space,
  Dialog,
  Tag,
  Input,
  Loading,
  Empty,
  MessagePlugin,
} from 'tdesign-react';
import { AddIcon, SearchIcon } from 'tdesign-icons-react';
import assemblyApi from '../../api/assembly';
import refinementApi from '../../api/refinement';
import { AssemblyDraft } from '../../types/assembly';
import './index.css';

export default function Drafts() {
  const navigate = useNavigate();
  const [drafts, setDrafts] = useState<AssemblyDraft[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');

  useEffect(() => {
    loadDrafts();
  }, []);

  const loadDrafts = async () => {
    setLoading(true);
    try {
      const response = await assemblyApi.getDrafts(1, 50);
      setDrafts(response.drafts);
    } catch (error) {
      console.error('Failed to load drafts:', error);
      MessagePlugin.error('加载草稿失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNew = () => {
    navigate('/assembly');
  };

  const handleEdit = (draft: AssemblyDraft) => {
    navigate(`/assembly/${draft.id}`);
  };

  const handleDelete = async (draftId: string) => {
    const dialog = Dialog.confirm({
      header: '确认删除',
      body: '确定要删除此草稿吗？',
      onConfirm: async () => {
        try {
          await assemblyApi.deleteDraft(draftId);
          await loadDrafts();
          MessagePlugin.success('删除成功');
          dialog.destroy();
        } catch (error) {
          console.error('Delete failed:', error);
          MessagePlugin.error('删除失败');
        }
      },
    });
  };

  const handleExport = async (draft: AssemblyDraft) => {
    try {
      const response = await assemblyApi.exportPPT(draft.id);
      window.open(response.download_url, '_blank');
    } catch (error) {
      console.error('Export failed:', error);
      MessagePlugin.error('导出失败');
    }
  };

  const handleStartRefinement = async (draftId: string) => {
    try {
      const response = await refinementApi.createTask(draftId);
      navigate(`/refinement/${response.task_id}`);
    } catch (error) {
      console.error('Failed to create refinement task:', error);
      MessagePlugin.error('创建精修任务失败');
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { theme: 'warning' | 'primary' | 'success' | 'danger' | 'default'; label: string }> = {
      draft: { theme: 'default', label: '草稿' },
      generating: { theme: 'primary', label: '生成中' },
      completed: { theme: 'success', label: '已完成' },
    };
    const config = statusMap[status] || { theme: 'default', label: status };
    return <Tag theme={config.theme}>{config.label}</Tag>;
  };

  const columns = [
    {
      colKey: 'title',
      title: '标题',
      ellipsis: true,
    },
    {
      colKey: 'chapters',
      title: '章节数',
      width: 100,
      cell: ({ row }: { row: AssemblyDraft }) => row.chapters.length,
    },
    {
      colKey: 'total_pages',
      title: '总页数',
      width: 100,
    },
    {
      colKey: 'status',
      title: '状态',
      width: 120,
      cell: ({ row }: { row: AssemblyDraft }) => getStatusTag(row.status),
    },
    {
      colKey: 'updated_at',
      title: '更新时间',
      width: 180,
      cell: ({ row }: { row: AssemblyDraft }) =>
        new Date(row.updated_at).toLocaleString('zh-CN'),
    },
    {
      colKey: 'actions',
      title: '操作',
      width: 200,
      cell: ({ row }: { row: AssemblyDraft }) => (
        <Space size="small" breakLine>
          <Button size="small" variant="text" onClick={() => handleEdit(row)}>
            编辑
          </Button>
          <Button size="small" variant="text" onClick={() => handleExport(row)}>
            导出
          </Button>
          <Button size="small" variant="text" onClick={() => handleStartRefinement(row.id)}>
            精修
          </Button>
          <Button size="small" variant="text" theme="danger" onClick={() => handleDelete(row.id)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const filteredDrafts = drafts.filter((draft) =>
    draft.title.toLowerCase().includes(searchKeyword.toLowerCase())
  );

  return (
    <div className="drafts-page">
      <div className="page-header">
        <h2 className="page-title">草稿管理</h2>
        <Button theme="primary" icon={<AddIcon />} onClick={handleCreateNew}>
          创建新草稿
        </Button>
      </div>

      <Card className="search-card">
        <Input
          placeholder="搜索草稿..."
          value={searchKeyword}
          onChange={(value) => setSearchKeyword(String(value))}
          prefixIcon={<SearchIcon />}
          size="large"
        />
      </Card>

      {loading ? (
        <div className="loading-container">
          <Loading size="large" />
        </div>
      ) : filteredDrafts.length === 0 ? (
        <Empty description={drafts.length === 0 ? '暂无草稿' : '未找到匹配的草稿'} />
      ) : (
        <Card>
          <Table data={filteredDrafts} columns={columns} rowKey="id" size="large" />
        </Card>
      )}
    </div>
  );
}
