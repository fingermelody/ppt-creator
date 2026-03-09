import { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Button,
  Card,
  Layout,
  Input,
  Textarea,
  Slider,
  Dialog,
  Space,
  Loading,
  Empty,
  MessagePlugin,
  DialogPlugin,
  Tag,
} from 'tdesign-react';
import { AddIcon, RollbackIcon, RollfrontIcon, DownloadIcon, ViewListIcon, BrowseIcon, RefreshIcon, ChevronRightIcon } from 'tdesign-icons-react';
import assemblyApi from '../../api/assembly';
import outlineApi from '../../api/outline';
import { AssemblyDraft } from '../../types/assembly';
import { PPTOutline } from '../../types/outline';
import { useAssemblyStore } from '../../stores/assemblyStore';
import ChapterPanel from './components/ChapterPanel';
import SlidePreview from './components/SlidePreview';
import PPTViewer from '../../components/PPTViewer';
import './index.css';

const { Header, Content, Aside } = Layout;

export default function Assembly() {
  const { draftId } = useParams<{ draftId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { draft, setDraft, loading, setLoading, canUndo, canRedo, undoDescription, redoDescription } =
    useAssemblyStore();

  const [newChapterTitle, setNewChapterTitle] = useState('');
  const [newChapterDesc, setNewChapterDesc] = useState('');
  const [newChapterPages, setNewChapterPages] = useState(5);
  const [showAddChapter, setShowAddChapter] = useState(false);
  const [selectedChapterId, setSelectedChapterId] = useState<string | null>(null);
  
  // 大纲相关状态
  const [linkedOutline, setLinkedOutline] = useState<PPTOutline | null>(null);
  const [showOutlineRequired, setShowOutlineRequired] = useState(false);
  
  // 大纲列表状态（当没有指定 draftId 时显示）
  const [availableOutlines, setAvailableOutlines] = useState<PPTOutline[]>([]);
  const [showOutlineList, setShowOutlineList] = useState(false);
  const [outlinesLoading, setOutlinesLoading] = useState(false);

  // 预览相关状态
  const [showPreview, setShowPreview] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [previewFileName, setPreviewFileName] = useState<string>('');
  
  // 自动匹配相关状态
  const [isAutoMatching, setIsAutoMatching] = useState(false);

  // 获取 URL 参数中的 outline ID
  const outlineIdFromUrl = searchParams.get('outline');

  useEffect(() => {
    if (draftId) {
      loadDraft(draftId);
      if (outlineIdFromUrl) {
        loadOutline(outlineIdFromUrl);
      }
    } else if (outlineIdFromUrl) {
      // 从大纲页面跳转过来，先查找是否有已关联的草稿
      findDraftByOutlineOrCreate(outlineIdFromUrl);
    } else {
      // 没有草稿也没有大纲参数，先检查是否有可用的大纲
      checkAvailableOutlines();
    }
  }, [draftId, outlineIdFromUrl]);

  // 检查是否有可用的大纲
  const checkAvailableOutlines = async () => {
    setOutlinesLoading(true);
    try {
      // 获取所有大纲
      const response = await outlineApi.getOutlines({});
      const outlines = response.outlines || [];
      
      // 过滤出已确认（confirmed）状态的大纲，这些可以直接用于组装
      // 注意：后端返回 'completed'，前端转换为 'confirmed'
      const confirmedOutlines = outlines.filter(o => o.status === 'confirmed');
      
      if (confirmedOutlines.length > 0) {
        // 有已确认的大纲，显示大纲列表
        setAvailableOutlines(confirmedOutlines);
        setShowOutlineList(true);
        setShowOutlineRequired(false);
      } else if (outlines.length > 0) {
        // 有草稿状态的大纲，也显示列表但提示需要先确认
        setAvailableOutlines(outlines);
        setShowOutlineList(true);
        setShowOutlineRequired(false);
      } else {
        // 没有任何大纲，显示创建提示
        setShowOutlineRequired(true);
        setShowOutlineList(false);
      }
    } catch (error) {
      console.error('Failed to check available outlines:', error);
      setShowOutlineRequired(true);
    } finally {
      setOutlinesLoading(false);
    }
  };

  const findDraftByOutlineOrCreate = async (outlineId: string) => {
    setLoading(true);
    try {
      // 先尝试查找已有的草稿
      const existingDraft = await assemblyApi.getDraftByOutlineId(outlineId);
      if (existingDraft && existingDraft.draft) {
        // 找到已有草稿，直接使用
        navigate(`/assembly/${existingDraft.draft.id}?outline=${outlineId}`, { replace: true });
        return;
      }
      
      // 没有找到，则基于大纲创建新草稿
      await initializeFromOutline(outlineId);
    } catch (error) {
      console.error('Failed to find draft by outline:', error);
      // 尝试创建新草稿
      await initializeFromOutline(outlineId);
    }
  };

  const loadDraft = async (id: string) => {
    setLoading(true);
    try {
      const response = await assemblyApi.getDraftDetail(id);
      setDraft(response.draft);
      
      // 检查是否需要自动匹配页面（如果所有页面都没有 source_slide_id）
      if (response.draft && response.draft.chapters) {
        const needsAutoMatch = response.draft.chapters.some(chapter => 
          chapter.pages.length > 0 && 
          chapter.pages.every(page => !page.document_id || page.document_id === '')
        );
        
        if (needsAutoMatch) {
          // 自动触发智能匹配
          MessagePlugin.info('正在智能匹配素材页面...');
          await handleAutoMatch(id);
        }
      }
    } catch (error) {
      console.error('Failed to load draft:', error);
      MessagePlugin.error('加载草稿失败');
    } finally {
      setLoading(false);
    }
  };

  // 自动匹配页面
  const handleAutoMatch = async (targetDraftId?: string) => {
    const id = targetDraftId || draftId;
    if (!id) return;

    setIsAutoMatching(true);
    try {
      const response = await assemblyApi.autoMatchPages(id);
      MessagePlugin.success(response.message);
      
      // 重新加载草稿
      const draftResponse = await assemblyApi.getDraftDetail(id);
      setDraft(draftResponse.draft);
    } catch (error) {
      console.error('Auto match failed:', error);
      MessagePlugin.warning('智能匹配未找到足够的相关素材，您可以手动添加页面');
    } finally {
      setIsAutoMatching(false);
    }
  };

  const loadOutline = async (outlineId: string) => {
    try {
      const outline = await outlineApi.getOutlineDetail(outlineId);
      setLinkedOutline(outline);
    } catch (error) {
      console.error('Failed to load outline:', error);
    }
  };

  const initializeFromOutline = async (outlineId: string) => {
    setLoading(true);
    try {
      // 获取大纲详情
      const outline = await outlineApi.getOutlineDetail(outlineId);
      setLinkedOutline(outline);
      
      // 基于大纲创建草稿
      const response = await assemblyApi.createDraftFromOutline(outline);
      navigate(`/assembly/${response.draft_id}?outline=${outlineId}`, { replace: true });
    } catch (error) {
      console.error('Failed to initialize from outline:', error);
      MessagePlugin.error('初始化失败');
      setShowOutlineRequired(true);
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

  const handleGoToOutline = () => {
    navigate('/outline');
  };

  // 选择大纲进行组装
  const handleSelectOutline = async (outline: PPTOutline) => {
    if (outline.status !== 'confirmed') {
      MessagePlugin.warning('请先确认该大纲再进行组装');
      navigate(`/outline?edit=${outline.id}`);
      return;
    }
    
    // 隐藏大纲列表，显示 loading
    setShowOutlineList(false);
    
    // 直接调用查找或创建草稿的逻辑
    await findDraftByOutlineOrCreate(outline.id);
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

    const confirmDialog = DialogPlugin.confirm({
      header: '导出PPT',
      body: '确定要导出当前PPT吗？',
      onConfirm: async () => {
        try {
          MessagePlugin.info('正在生成PPT文件...');
          const response = await assemblyApi.exportPPT(draftId);
          
          // 构建完整的下载 URL
          const apiBase = import.meta.env.VITE_API_BASE_URL || '';
          const downloadUrl = apiBase + response.download_url;
          
          // 创建下载链接并触发下载
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = response.file_name || 'presentation.pptx';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          confirmDialog.destroy();
          MessagePlugin.success('导出成功，文件正在下载');
        } catch (error) {
          console.error('Export failed:', error);
          MessagePlugin.error('导出失败，请重试');
        }
      },
    });
  };

  const handlePreview = async () => {
    if (!draftId) return;

    try {
      MessagePlugin.info('正在准备预览...');
      
      // 调用预览 API（会自动导出并上传到 COS）
      const response = await assemblyApi.previewPPT(draftId);
      const apiBase = import.meta.env.VITE_API_BASE_URL || '';
      const fileUrl = apiBase + response.download_url;
      
      setPreviewUrl(fileUrl);
      setPreviewFileName(response.file_name || '演示文稿.pptx');
      setShowPreview(true);
    } catch (error) {
      console.error('Preview failed:', error);
      MessagePlugin.error('预览准备失败，请重试');
    }
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

  if (loading || outlinesLoading) {
    return (
      <div className="assembly-page loading">
        <Loading size="large" />
      </div>
    );
  }

  // 显示大纲列表（当有可用大纲且没有选择特定草稿时）
  if (showOutlineList && !draft && availableOutlines.length > 0) {
    return (
      <div className="assembly-page outline-list-page">
        <Card className="outline-list-card">
          <div className="outline-list-header">
            <h2>选择大纲开始组装</h2>
            <p className="outline-list-desc">
              请选择一个已确认的大纲，系统将基于大纲内容智能匹配素材页面
            </p>
          </div>
          <div className="outline-select-list">
            {availableOutlines.map((outline) => (
              <div
                key={outline.id}
                className={`outline-item ${outline.status === 'confirmed' ? 'completed' : 'draft'}`}
                onClick={() => {
                  console.log('Outline clicked:', outline.id, outline.title);
                  handleSelectOutline(outline);
                }}
                style={{ cursor: 'pointer' }}
              >
                <div className="outline-item-content">
                  <div className="outline-item-main">
                    <h4 className="outline-item-title">{outline.title}</h4>
                    <p className="outline-item-desc">
                      {outline.chapters?.length || 0} 个章节
                      {outline.updated_at && (
                        <span className="outline-item-time">
                          · 更新于 {new Date(outline.updated_at).toLocaleDateString()}
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="outline-item-action">
                    {outline.status === 'confirmed' ? (
                      <Tag theme="success" variant="light">已确认</Tag>
                    ) : (
                      <Tag theme="warning" variant="light">草稿</Tag>
                    )}
                    <ChevronRightIcon className="outline-item-arrow" />
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div className="outline-list-footer">
            <Space>
              <Button 
                variant="outline" 
                icon={<ViewListIcon />}
                onClick={handleGoToOutline}
              >
                管理大纲
              </Button>
              <Button 
                variant="text"
                onClick={createNewDraft}
              >
                跳过，直接创建空白PPT
              </Button>
            </Space>
          </div>
        </Card>
      </div>
    );
  }

  // 显示需要先创建大纲的提示（没有任何大纲时）
  if (showOutlineRequired && !draft) {
    return (
      <div className="assembly-page empty">
        <Card className="outline-required-card">
          <div className="outline-required-content">
            <ViewListIcon className="outline-required-icon" />
            <h2>开始制作PPT</h2>
            <p className="outline-required-desc">
              建议先设计PPT大纲，明确章节结构和内容要点，
              <br />
              系统会基于大纲自动匹配素材页面。
            </p>
            <Space direction="vertical" size="large">
              <Button 
                theme="primary" 
                size="large"
                icon={<ViewListIcon />}
                onClick={handleGoToOutline}
              >
                设计PPT大纲
              </Button>
              <Button 
                variant="text"
                onClick={createNewDraft}
              >
                跳过，直接创建空白PPT
              </Button>
            </Space>
          </div>
        </Card>
      </div>
    );
  }

  if (!draft) {
    return (
      <div className="assembly-page empty">
        <Empty description="还没有PPT草稿" />
        <Space direction="vertical" size="large">
          <Button theme="primary" icon={<ViewListIcon />} onClick={handleGoToOutline}>
            从大纲开始
          </Button>
          <Button variant="outline" icon={<AddIcon />} onClick={createNewDraft}>
            创建空白PPT
          </Button>
        </Space>
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
            {linkedOutline && (
              <span className="linked-outline-badge">
                基于大纲：{linkedOutline.title}
              </span>
            )}
          </div>
          <div className="header-right">
            <Space>
              <Button
                variant="outline"
                icon={<RefreshIcon />}
                loading={isAutoMatching}
                onClick={() => handleAutoMatch()}
                title="根据章节内容智能匹配素材页面"
              >
                智能匹配
              </Button>
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
                variant="outline"
                icon={<BrowseIcon />}
                onClick={handlePreview}
                disabled={!draft || draft.chapters.length === 0}
              >
                预览 PPT
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
                        {chapter.pages.map((page, pageIndex) => (
                          <SlidePreview
                            key={page.slide_id}
                            page={page}
                            chapterId={chapter.id}
                            draftId={draftId!}
                            pageIndex={pageIndex}
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

      {/* PPT Preview Dialog */}
      <PPTViewer
        visible={showPreview}
        fileUrl={previewUrl}
        fileName={previewFileName}
        onClose={() => setShowPreview(false)}
        onDownload={handleExport}
      />
    </div>
  );
}
