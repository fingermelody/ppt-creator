/* PPT 生成页面 */

import { useState, useEffect } from 'react';
import {
  Button,
  Card,
  Input,
  Select,
  Space,
  Row,
  Col,
  Tag,
  Tabs,
  Progress,
  Switch,
  Upload,
  DialogPlugin,
  MessagePlugin,
  Loading,
  Empty,
  Tooltip,
  Textarea,
} from 'tdesign-react';
import {
  SearchIcon,
  AddIcon,
  DeleteIcon,
  DownloadIcon,
  TimeIcon,
  FileIcon,
  RefreshIcon,
  BrowseIcon,
  CloudUploadIcon,
  ChartBarIcon,
  InternetIcon,
} from 'tdesign-icons-react';
import { generationApi } from '../../api/generation';
import { useGenerationStore } from '../../stores/generationStore';
import type { 
  TemplateCategory,
  GenerationStatus,
} from '../../types/generation';
import { 
  SEARCH_DEPTH_OPTIONS, 
  PAGE_COUNT_OPTIONS, 
  TEMPLATE_CATEGORY_NAMES 
} from '../../types/generation';
import TemplateGrid from './components/TemplateGrid';
import ProgressModal from './components/ProgressModal';
import './index.css';

const { TabPanel } = Tabs;

export default function Generation() {
  const [activeTab, setActiveTab] = useState('create');
  const [searchValue, setSearchValue] = useState('');
  
  const {
    tasks,
    setTasks,
    templates,
    setTemplates,
    selectedCategory,
    setSelectedCategory,
    selectedTemplate,
    setSelectedTemplate,
    customStyleFile,
    setCustomStyleFile,
    topicInput,
    setTopicInput,
    titleInput,
    setTitleInput,
    pageCount,
    setPageCount,
    includeImages,
    setIncludeImages,
    includeCharts,
    setIncludeCharts,
    searchDepth,
    setSearchDepth,
    language,
    setLanguage,
    generating,
    setGenerating,
    generationProgress,
    setGenerationProgress,
    generationStatus,
    setGenerationStatus,
    progressMessage,
    setProgressMessage,
    loading,
    setLoading,
    setError,
    showProgressModal,
    setShowProgressModal,
    setCurrentTask,
    resetForm,
  } = useGenerationStore();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [templatesRes, tasksRes] = await Promise.all([
        generationApi.getTemplates(),
        generationApi.getTasks(),
      ]);
      setTemplates(templatesRes.templates);
      setTasks(tasksRes.tasks);
    } catch (err) {
      console.error('Failed to load data:', err);
      MessagePlugin.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleStartGeneration = async () => {
    // 验证输入
    if (!topicInput.trim()) {
      MessagePlugin.warning('请输入PPT主题描述');
      return;
    }
    if (topicInput.trim().length < 10) {
      MessagePlugin.warning('主题描述至少需要10个字符');
      return;
    }

    setGenerating(true);
    setShowProgressModal(true);
    setGenerationProgress(0);
    setGenerationStatus('pending');
    setProgressMessage('正在准备生成...');

    try {
      // 开始生成
      const response = await generationApi.startGeneration({
        topic: topicInput,
        title: titleInput || undefined,
        page_count: pageCount,
        template_id: selectedTemplate?.id,
        include_images: includeImages,
        include_charts: includeCharts,
        search_depth: searchDepth,
        language,
      });

      // 轮询进度
      await generationApi.pollProgress(
        response.task_id,
        (progress) => {
          setGenerationProgress(progress.progress);
          setGenerationStatus(progress.status);
          setProgressMessage(progress.message);
        },
        (task) => {
          setCurrentTask(task);
          setGenerating(false);
          MessagePlugin.success('PPT生成完成！');
          loadData(); // 重新加载任务列表
        },
        (errorMsg) => {
          setError(errorMsg);
          setGenerating(false);
          MessagePlugin.error(errorMsg);
        }
      );
    } catch (err) {
      console.error('Generation failed:', err);
      setGenerating(false);
      setShowProgressModal(false);
      MessagePlugin.error('生成失败，请重试');
    }
  };

  const handleCancelGeneration = () => {
    const dialog = DialogPlugin.confirm({
      header: '确认取消',
      body: '确定要取消当前生成任务吗？',
      onConfirm: () => {
        setGenerating(false);
        setShowProgressModal(false);
        resetForm();
        dialog.destroy();
        MessagePlugin.info('已取消生成');
      },
    });
  };

  const handleDeleteTask = (taskId: string, taskTitle: string) => {
    const dialog = DialogPlugin.confirm({
      header: '确认删除',
      body: `确定要删除"${taskTitle}"吗？此操作不可恢复。`,
      confirmBtn: { theme: 'danger', content: '删除' },
      onConfirm: async () => {
        try {
          await generationApi.deleteTask(taskId);
          setTasks(tasks.filter((t) => t.id !== taskId));
          MessagePlugin.success('删除成功');
          dialog.destroy();
        } catch (err) {
          MessagePlugin.error('删除失败');
        }
      },
    });
  };

  const handleExportTask = async (taskId: string) => {
    try {
      const response = await generationApi.exportPPT(taskId);
      window.open(response.download_url, '_blank');
      MessagePlugin.success('导出成功');
    } catch (err) {
      MessagePlugin.error('导出失败');
    }
  };

  const handleCustomFileUpload = (file: any) => {
    if (file.raw) {
      setCustomStyleFile(file.raw);
      setSelectedTemplate(null);
      MessagePlugin.success(`已选择自定义模板：${file.name}`);
    }
    return false; // 阻止默认上传
  };

  const getStatusTag = (status: GenerationStatus) => {
    const statusMap: Record<GenerationStatus, { theme: 'primary' | 'success' | 'warning' | 'danger' | 'default'; label: string }> = {
      pending: { theme: 'default', label: '等待中' },
      searching: { theme: 'primary', label: '搜索中' },
      analyzing: { theme: 'primary', label: '分析中' },
      generating: { theme: 'primary', label: '生成中' },
      applying_style: { theme: 'warning', label: '应用风格' },
      completed: { theme: 'success', label: '已完成' },
      failed: { theme: 'danger', label: '失败' },
    };
    const config = statusMap[status] || { theme: 'default', label: status };
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

  const filteredTasks = tasks.filter((task) =>
    task.title.toLowerCase().includes(searchValue.toLowerCase()) ||
    task.topic.toLowerCase().includes(searchValue.toLowerCase())
  );

  const filteredTemplates = templates.filter((t) =>
    selectedCategory === 'all' || t.category === selectedCategory
  );

  if (loading && templates.length === 0) {
    return (
      <div className="generation-page loading">
        <Loading size="large" />
      </div>
    );
  }

  return (
    <div className="generation-page">
      <div className="page-header">
        <h1>PPT智能生成</h1>
        <p className="page-description">
          输入主题描述，AI将自动搜索互联网信息并生成专业PPT，支持选择模板定制风格
        </p>
      </div>

      <Tabs value={activeTab} onChange={(val) => setActiveTab(String(val))}>
        <TabPanel value="create" label="创建PPT">
          <div className="tab-content create-content">
            <Row gutter={[24, 24]}>
              {/* 左侧：输入区域 */}
              <Col xs={24} lg={14}>
                <Card title="主题描述" className="input-card">
                  <div className="form-section">
                    <div className="form-item">
                      <label className="form-label">
                        PPT标题 <span className="optional">(可选，不填则自动生成)</span>
                      </label>
                      <Input
                        value={titleInput}
                        onChange={(val) => setTitleInput(String(val))}
                        placeholder="例如：人工智能发展趋势报告"
                        maxlength={100}
                        clearable
                      />
                    </div>

                    <div className="form-item">
                      <label className="form-label required">
                        主题描述 <span className="hint">（详细描述您想要生成的PPT内容）</span>
                      </label>
                      <Textarea
                        value={topicInput}
                        onChange={(val) => setTopicInput(String(val))}
                        placeholder="请详细描述您想要生成的PPT内容，例如：&#10;&#10;分析2024-2025年人工智能领域的最新发展趋势，包括：&#10;1. 大语言模型的技术突破&#10;2. AI Agent 的应用场景&#10;3. 多模态AI的发展&#10;4. AI在企业中的落地实践&#10;5. 未来展望与挑战&#10;&#10;描述越详细，生成的PPT质量越高。"
                        maxlength={2000}
                        autosize={{ minRows: 8, maxRows: 15 }}
                      />
                      <div className="char-count">
                        {topicInput.length} / 2000
                      </div>
                    </div>
                  </div>
                </Card>

                <Card title="生成选项" className="options-card">
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <div className="form-item">
                        <label className="form-label">页数</label>
                        <Select
                          value={pageCount}
                          onChange={(val) => setPageCount(Number(val))}
                          style={{ width: '100%' }}
                          options={PAGE_COUNT_OPTIONS.map((opt) => ({
                            value: opt.value,
                            label: `${opt.label} - ${opt.description}`,
                          }))}
                        />
                      </div>
                    </Col>
                    <Col span={12}>
                      <div className="form-item">
                        <label className="form-label">搜索深度</label>
                        <Select
                          value={searchDepth}
                          onChange={(val) => setSearchDepth(val as any)}
                          style={{ width: '100%' }}
                          options={SEARCH_DEPTH_OPTIONS.map((opt) => ({
                            value: opt.value,
                            label: `${opt.label} - ${opt.description}`,
                          }))}
                        />
                      </div>
                    </Col>
                    <Col span={12}>
                      <div className="form-item">
                        <label className="form-label">语言</label>
                        <Select
                          value={language}
                          onChange={(val) => setLanguage(val as any)}
                          style={{ width: '100%' }}
                          options={[
                            { value: 'zh', label: '中文' },
                            { value: 'en', label: 'English' },
                          ]}
                        />
                      </div>
                    </Col>
                    <Col span={12}>
                      <div className="form-item switch-items">
                        <div className="switch-item">
                          <Switch value={includeImages} onChange={setIncludeImages} />
                          <span className="switch-label">
                            <BrowseIcon /> 包含图片
                          </span>
                        </div>
                        <div className="switch-item">
                          <Switch value={includeCharts} onChange={setIncludeCharts} />
                          <span className="switch-label">
                            <ChartBarIcon /> 包含图表
                          </span>
                        </div>
                      </div>
                    </Col>
                  </Row>
                </Card>
              </Col>

              {/* 右侧：模板选择 */}
              <Col xs={24} lg={10}>
                <Card 
                  title="风格模板" 
                  className="template-card"
                  actions={
                    <Upload
                      theme="custom"
                      accept=".pptx,.ppt"
                      beforeUpload={handleCustomFileUpload}
                    >
                      <Button variant="outline" icon={<CloudUploadIcon />} size="small">
                        上传自定义模板
                      </Button>
                    </Upload>
                  }
                >
                  {/* 模板分类筛选 */}
                  <div className="template-filter">
                    <div className="filter-tags">
                      <Tag
                        className={`filter-tag ${selectedCategory === 'all' ? 'active' : ''}`}
                        onClick={() => setSelectedCategory('all')}
                      >
                        全部
                      </Tag>
                      {(Object.keys(TEMPLATE_CATEGORY_NAMES) as TemplateCategory[]).map((cat) => (
                        <Tag
                          key={cat}
                          className={`filter-tag ${selectedCategory === cat ? 'active' : ''}`}
                          onClick={() => setSelectedCategory(cat)}
                        >
                          {TEMPLATE_CATEGORY_NAMES[cat]}
                        </Tag>
                      ))}
                    </div>
                  </div>

                  {/* 自定义模板显示 */}
                  {customStyleFile && (
                    <div className="custom-template-info">
                      <FileIcon />
                      <span>{customStyleFile.name}</span>
                      <Button
                        variant="text"
                        size="small"
                        theme="danger"
                        onClick={() => setCustomStyleFile(null)}
                      >
                        移除
                      </Button>
                    </div>
                  )}

                  {/* 模板网格 */}
                  <TemplateGrid
                    templates={filteredTemplates}
                    selectedId={selectedTemplate?.id}
                    onSelect={(template) => {
                      setSelectedTemplate(template);
                      setCustomStyleFile(null);
                    }}
                  />
                </Card>

                {/* 生成按钮 */}
                <div className="generate-actions">
                  <Button
                    theme="primary"
                    size="large"
                    block
                    icon={<InternetIcon />}
                    onClick={handleStartGeneration}
                    loading={generating}
                    disabled={!topicInput.trim() || topicInput.trim().length < 10}
                  >
                    {generating ? '正在生成...' : '开始生成PPT'}
                  </Button>
                  <p className="generate-hint">
                    <InternetIcon /> AI将搜索互联网获取最新信息生成PPT内容
                  </p>
                </div>
              </Col>
            </Row>
          </div>
        </TabPanel>

        <TabPanel value="history" label="生成历史">
          <div className="tab-content history-content">
            <div className="history-toolbar">
              <Input
                value={searchValue}
                onChange={(val) => setSearchValue(String(val))}
                placeholder="搜索生成记录..."
                prefixIcon={<SearchIcon />}
                clearable
                style={{ width: 300 }}
              />
              <Button icon={<RefreshIcon />} onClick={loadData}>
                刷新
              </Button>
            </div>

            {filteredTasks.length === 0 ? (
              <div className="empty-container">
                <Empty description="暂无生成记录" />
                <Button
                  theme="primary"
                  icon={<AddIcon />}
                  onClick={() => setActiveTab('create')}
                >
                  创建PPT
                </Button>
              </div>
            ) : (
              <Row gutter={[16, 16]}>
                {filteredTasks.map((task) => (
                  <Col key={task.id} xs={24} sm={12} md={8} lg={6}>
                    <Card
                      className="task-card"
                      hoverShadow
                      title={
                        <div className="card-header">
                          <Tooltip content={task.title}>
                            <span className="card-title">{task.title}</span>
                          </Tooltip>
                          {getStatusTag(task.status)}
                        </div>
                      }
                      description={
                        <div className="card-body">
                          <p className="task-topic" title={task.topic}>
                            {task.topic.length > 60 ? task.topic.slice(0, 60) + '...' : task.topic}
                          </p>
                          <div className="task-info">
                            <div className="info-item">
                              <FileIcon />
                              <span>{task.total_pages} 页</span>
                            </div>
                            <div className="info-item">
                              <InternetIcon />
                              <span>{task.web_sources.length} 个来源</span>
                            </div>
                          </div>
                          <div className="task-time">
                            <TimeIcon />
                            <span>{formatDate(task.updated_at)}</span>
                          </div>
                          {task.status !== 'completed' && task.status !== 'failed' && (
                            <Progress
                              percentage={task.progress}
                              size="small"
                              style={{ marginTop: 8 }}
                            />
                          )}
                        </div>
                      }
                      actions={
                        <div className="card-footer">
                          <Space>
                            {task.status === 'completed' && (
                              <>
                                <Button
                                  size="small"
                                  variant="text"
                                  icon={<BrowseIcon />}
                                  onClick={() => {
                                    setCurrentTask(task);
                                    // 可以导航到预览页面或打开预览弹窗
                                    MessagePlugin.info('预览功能开发中');
                                  }}
                                >
                                  预览
                                </Button>
                                <Button
                                  size="small"
                                  variant="text"
                                  icon={<DownloadIcon />}
                                  onClick={() => handleExportTask(task.id)}
                                >
                                  导出
                                </Button>
                              </>
                            )}
                            <Button
                              size="small"
                              variant="text"
                              theme="danger"
                              icon={<DeleteIcon />}
                              onClick={() => handleDeleteTask(task.id, task.title)}
                            >
                              删除
                            </Button>
                          </Space>
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

      {/* 进度弹窗 */}
      <ProgressModal
        visible={showProgressModal}
        status={generationStatus}
        progress={generationProgress}
        message={progressMessage}
        onCancel={handleCancelGeneration}
        onComplete={() => {
          setShowProgressModal(false);
          setActiveTab('history');
        }}
      />
    </div>
  );
}
