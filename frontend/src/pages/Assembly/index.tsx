import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Button,
  Card,
  Layout,
  Input,
  Slider,
  Dialog,
  Space,
  Loading,
  Empty,
  MessagePlugin,
} from 'tdesign-react';
import { AddIcon, RollbackIcon, RollfrontIcon, DownloadIcon } from 'tdesign-icons-react';
import assemblyApi from '../../api/assembly.mock';
import { AssemblyDraft } from '../../types/assembly';
import { useAssemblyStore } from '../../stores/assemblyStore';
import ChapterPanel from './components/ChapterPanel';
import SlidePreview from './components/SlidePreview';
import './index.css';

const { Header, Content, Aside } = Layout;
const { Textarea } = Input;

export default function Assembly() {
  const { draftId } = useParams<{ draftId: string }>();
  const navigate = useNavigate();
  const { draft, setDraft, loading, setLoading, canUndo, canRedo, undoDescription, redoDescription } =
    useAssemblyStore();

  const [newChapterTitle, setNewChapterTitle] = useState('');
  const [newChapterDesc, setNewChapterDesc] = useState('');
  const [newChapterPages, setNewChapterPages] = useState(5);
  const [showAddChapter, setShowAddChapter] = useState(false);
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);

  useEffect(() => {
    if (draftId) {
      loadDraft(draftId);
    }
  }, [draftId]);

  const loadDraft = async (id: string) => {
    setLoading(true);
    try {
      const response = await assemblyApi.getDraftDetail(id);
      setDraft(response.draft);
    } catch (error) {
      console.error('Failed to load draft:', error);
      MessagePlugin.error('加载草稿失败');
    } finally {
      setLoading(false);
    }
  };

  const createNewDraft = async () => {
    setLoading(true);
    try {
      const response = await assemblyApi.createDraft('新PPT');
      navigate(`/assembly/${response.draft_id}`);
    } catch (error) {
      console.error('Failed to create draft:', error);
      MessagePlugin.error('创建草稿失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAddChapter = async () => {
    if (!newChapterTitle.trim()) {
      MessagePlugin.warning('请输入章节标题');
      return;
    }

    try {
      await assemblyApi.addChapter(draftId!, {
        title: newChapterTitle,
        description: newChapterDesc,
        required_pages: newChapterPages,
      });

      setNewChapterTitle('');
      setNewChapterDesc('');
      setNewChapterPages(5);
      setShowAddChapter(false);

      await loadDraft(draftId!);
      MessagePlugin.success('章节添加成功');
    } catch (error) {
      console.error('Failed to add chapter:', error);
      MessagePlugin.error('添加章节失败');
    }
  };

  const handleExport = async () => {
    if (!draftId) return;

    const dialog = Dialog.confirm({
      header: '导出PPT',
      body: '确定要导出当前PPT吗？',
      onConfirm: async () => {
        try {
          const response = await assemblyApi.exportPPT(draftId);
          window.open(response.download_url, '_blank');
          dialog.destroy();
          MessagePlugin.success('导出成功');
        } catch (error) {
          console.error('Export failed:', error);
          MessagePlugin.error('导出失败');
        }
      },
    });
  };

  const handleUndo = async () => {
    if (!draftId) return;
    try {
      await assemblyApi.undo(draftId);
      await loadDraft(draftId);
    } catch (error) {
      console.error('Undo failed:', error);
      MessagePlugin.error('撤销失败');
    }
  };

  const handleRedo = async () => {
    if (!draftId) return;
    try {
      await assemblyApi.redo(draftId);
      await loadDraft(draftId);
    } catch (error) {
      console.error('Redo failed:', error);
      MessagePlugin.error('重做失败');
    }
  };

  if (loading) {
    return (
      <div className="assembly-page loading">
        <Loading size="large" />
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="assembly-page empty">
        <Empty description="还没有PPT草稿" />
        <Button theme="primary" icon={<AddIcon />} onClick={createNewDraft}>
          创建新PPT
        </Button>
      </div>
    );
  }

  return (
    <div className="assembly-page">
      <Layout>
        <Header className="assembly-header">
          <div className="header-left">
            <Input
              value={draft.title}
              onChange={(value) => setDraft({ ...draft, title: String(value) })}
              placeholder="PPT标题"
              size="large"
              style={{ width: 300 }}
            />
          </div>
          <div className="header-right">
            <Space>
              <Button
                variant="outline"
                icon={<RollbackIcon />}
                disabled={!canUndo}
                onClick={handleUndo}
                title={undoDescription}
              >
                撤销
              </Button>
              <Button
                variant="outline"
                icon={<RollfrontIcon />}
                disabled={!canRedo}
                onClick={handleRedo}
                title={redoDescription}
              >
                重做
              </Button>
              <Button
                theme="primary"
                icon={<DownloadIcon />}
                onClick={handleExport}
              >
                导出PPT
              </Button>
            </Space>
          </div>
        </Header>

        <Layout>
          <Aside className="chapters-sidebar">
            <div className="chapters-header">
              <h3>章节</h3>
              <Button
                size="small"
                variant="text"
                icon={<AddIcon />}
                onClick={() => setShowAddChapter(true)}
              >
                添加章节
              </Button>
            </div>
            <div className="chapters-list">
              {draft.chapters.length === 0 ? (
                <Empty description="暂无章节" />
              ) : (
                draft.chapters.map((chapter) => (
                  <ChapterPanel
                    key={chapter.id}
                    chapter={chapter}
                    selected={selectedChapterId === chapter.id}
                    onSelect={() => setSelectedChapterId(chapter.id)}
                    onRefresh={() => loadDraft(draftId!)}
                  />
                ))
              )}
            </div>
          </Aside>

          <Content className="assembly-content">
            {selectedChapterId ? (
              <div className="chapter-detail">
                {draft.chapters
                  .filter((ch) => ch.id === selectedChapterId)
                  .map((chapter) => (
                    <div key={chapter.id}>
                      <h2>{chapter.title}</h2>
                      <p className="chapter-desc">{chapter.description}</p>
                      <div className="slides-grid">
                        {chapter.pages.map((page) => (
                          <SlidePreview
                            key={page.slide_id}
                            page={page}
                            chapterId={chapter.id}
                            draftId={draftId!}
                            onRefresh={() => loadDraft(draftId!)}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            ) : (
              <div className="assembly-placeholder">
                <Empty description="选择一个章节查看详情" />
              </div>
            )}
          </Content>
        </Layout>
      </Layout>

      {/* Add Chapter Dialog */}
      <Dialog
        header="添加章节"
        visible={showAddChapter}
        onConfirm={handleAddChapter}
        onClose={() => setShowAddChapter(false)}
      >
        <div className="add-chapter-form">
          <div className="form-item">
            <label>章节标题</label>
            <Input
              value={newChapterTitle}
              onChange={(value) => setNewChapterTitle(String(value))}
              placeholder="请输入章节标题"
            />
          </div>
          <div className="form-item">
            <label>内容概要</label>
            <Textarea
              value={newChapterDesc}
              onChange={(value) => setNewChapterDesc(String(value))}
              placeholder="描述章节的主要内容"
              autosize={{ minRows: 4 }}
            />
          </div>
          <div className="form-item">
            <label>页数需求 ({newChapterPages}页)</label>
            <Slider
              value={newChapterPages}
              onChange={(value) => setNewChapterPages(Number(value))}
              min={3}
              max={8}
              step={1}
              marks={{ 3: '3', 5: '5', 8: '8' }}
            />
          </div>
        </div>
      </Dialog>
    </div>
  );
}
