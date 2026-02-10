import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Tabs,
  Button,
  Input,
  Loading,
  MessagePlugin,
  Space,
  Tag,
  Empty,
} from 'tdesign-react';
import { CheckCircleIcon, AddIcon } from 'tdesign-icons-react';
import outlineApi from '../../api/outline.mock';
import { useOutlineStore } from '../../stores/outlineStore';
import type { PPTOutline, OutlineTemplate } from '../../types/outline';
import SmartGenerate from './components/SmartGenerate';
import WizardGenerate from './components/WizardGenerate';
import OutlinePreview from './components/OutlinePreview';
import TemplateSelector from './components/TemplateSelector';
import './index.css';

const { TabPanel } = Tabs;

export default function Outline() {
  const navigate = useNavigate();
  const {
    generationType,
    setGenerationType,
    currentOutline,
    setCurrentOutline,
    outlines,
    setOutlines,
    loading,
    setLoading,
    templates,
    setTemplates,
    reset,
  } = useOutlineStore();

  const [showTemplates, setShowTemplates] = useState(false);
  const [confirmingOutline, setConfirmingOutline] = useState(false);

  useEffect(() => {
    loadOutlines();
    loadTemplates();
    
    return () => {
      // 清理状态
    };
  }, []);

  const loadOutlines = async () => {
    setLoading(true);
    try {
      const response = await outlineApi.getOutlines({ status: 'draft' });
      setOutlines(response.outlines);
    } catch (error) {
      console.error('Failed to load outlines:', error);
      MessagePlugin.error('加载大纲列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await outlineApi.getTemplates();
      setTemplates(response.templates);
    } catch (error) {
      console.error('Failed to load templates:', error);
    }
  };

  const handleTabChange = (value: string | number) => {
    setGenerationType(value as 'smart' | 'wizard');
    setCurrentOutline(null);
  };

  const handleOutlineGenerated = (outline: PPTOutline) => {
    setCurrentOutline(outline);
    setOutlines([outline, ...outlines.filter(o => o.id !== outline.id)]);
  };

  const handleTemplateSelect = async (template: OutlineTemplate) => {
    setShowTemplates(false);
    setLoading(true);
    
    try {
      const response = await outlineApi.applyTemplate(template.id);
      handleOutlineGenerated(response.outline);
      MessagePlugin.success('模板应用成功');
    } catch (error) {
      console.error('Failed to apply template:', error);
      MessagePlugin.error('应用模板失败');
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmOutline = async () => {
    if (!currentOutline) return;

    setConfirmingOutline(true);
    try {
      const response = await outlineApi.confirmOutline(currentOutline.id);
      MessagePlugin.success(response.message);
      
      // 跳转到组装页面
      navigate(`/assembly/${response.assembly_draft_id}?outline=${currentOutline.id}`);
    } catch (error) {
      console.error('Failed to confirm outline:', error);
      MessagePlugin.error('确认大纲失败');
    } finally {
      setConfirmingOutline(false);
    }
  };

  const handleLoadOutline = async (outline: PPTOutline) => {
    setLoading(true);
    try {
      const detail = await outlineApi.getOutlineDetail(outline.id);
      setCurrentOutline(detail);
      setGenerationType(detail.generation_type);
    } catch (error) {
      console.error('Failed to load outline:', error);
      MessagePlugin.error('加载大纲详情失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteOutline = async (outlineId: string) => {
    try {
      await outlineApi.deleteOutline(outlineId);
      setOutlines(outlines.filter(o => o.id !== outlineId));
      if (currentOutline?.id === outlineId) {
        setCurrentOutline(null);
      }
      MessagePlugin.success('删除成功');
    } catch (error) {
      console.error('Failed to delete outline:', error);
      MessagePlugin.error('删除失败');
    }
  };

  return (
    <div className="outline-page">
      <div className="outline-header">
        <div className="header-left">
          <h2>PPT大纲设计</h2>
          <p className="header-desc">
            选择生成方式，快速构建PPT框架结构
          </p>
        </div>
        <div className="header-right">
          <Space>
            <Button
              variant="outline"
              icon={<AddIcon />}
              onClick={() => setShowTemplates(true)}
            >
              使用模板
            </Button>
            {currentOutline && (
              <Button
                theme="primary"
                icon={<CheckCircleIcon />}
                loading={confirmingOutline}
                onClick={handleConfirmOutline}
              >
                确认大纲，开始组装
              </Button>
            )}
          </Space>
        </div>
      </div>

      <div className="outline-main">
        <div className="outline-content">
          <Card className="generate-card">
            <Tabs
              value={generationType}
              onChange={handleTabChange}
              theme="card"
            >
              <TabPanel value="smart" label="智能生成">
                <SmartGenerate onGenerated={handleOutlineGenerated} />
              </TabPanel>
              <TabPanel value="wizard" label="向导式生成">
                <WizardGenerate onGenerated={handleOutlineGenerated} />
              </TabPanel>
            </Tabs>
          </Card>

          {currentOutline && (
            <Card className="preview-card" title="大纲预览">
              <OutlinePreview
                outline={currentOutline}
                onUpdate={setCurrentOutline}
              />
            </Card>
          )}
        </div>

        <div className="outline-sidebar">
          <Card className="drafts-card" title="大纲草稿">
            {loading ? (
              <Loading size="small" />
            ) : outlines.length === 0 ? (
              <Empty description="暂无大纲草稿" />
            ) : (
              <div className="drafts-list">
                {outlines.map((outline) => (
                  <div
                    key={outline.id}
                    className={`draft-item ${currentOutline?.id === outline.id ? 'active' : ''}`}
                    onClick={() => handleLoadOutline(outline)}
                  >
                    <div className="draft-info">
                      <div className="draft-title">{outline.title || '未命名大纲'}</div>
                      <div className="draft-meta">
                        <span>{outline.chapters.length}个章节</span>
                        <span>·</span>
                        <span>{outline.total_pages}页</span>
                      </div>
                    </div>
                    <div className="draft-tags">
                      <Tag size="small" theme={outline.generation_type === 'smart' ? 'primary' : 'default'}>
                        {outline.generation_type === 'smart' ? '智能生成' : '向导式'}
                      </Tag>
                    </div>
                    <Button
                      variant="text"
                      theme="danger"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteOutline(outline.id);
                      }}
                    >
                      删除
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* 模板选择对话框 */}
      <TemplateSelector
        visible={showTemplates}
        templates={templates}
        onSelect={handleTemplateSelect}
        onClose={() => setShowTemplates(false)}
      />
    </div>
  );
}
