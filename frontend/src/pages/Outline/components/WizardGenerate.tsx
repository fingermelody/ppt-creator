import { useState, useEffect } from 'react';
import {
  Button,
  Input,
  Textarea,
  Steps,
  Radio,
  RadioGroup,
  Space,
  Slider,
  Tag,
  Checkbox,
  MessagePlugin,
} from 'tdesign-react';
import {
  AddIcon,
  DeleteIcon,
  MoveIcon,
  StarFilledIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CheckCircleIcon,
} from 'tdesign-icons-react';
import outlineApi from '../../../api/outline';
import { useOutlineStore } from '../../../stores/outlineStore';
import type {
  PPTOutline,
  WizardStep1Data,
  WizardStep2Data,
  WizardStep3Data,
} from '../../../types/outline';
import {
  DURATION_OPTIONS,
  TARGET_AUDIENCE_OPTIONS,
} from '../../../types/outline';

const { StepItem } = Steps;

interface WizardGenerateProps {
  onGenerated: (outline: PPTOutline) => void;
}

interface ChapterInput {
  id: string;
  title: string;
  pageCount: number;
  summary: string;
  keywords: string[];
}

export default function WizardGenerate({ onGenerated }: WizardGenerateProps) {
  const {
    currentStep,
    setCurrentStep,
    setGenerating,
    generating,
    resetWizard,
  } = useOutlineStore();

  // 步骤1数据
  const [title, setTitle] = useState('');
  const [objective, setObjective] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [duration, setDuration] = useState('');

  // 步骤2数据
  const [chapters, setChapters] = useState<ChapterInput[]>([
    { id: '1', title: '', pageCount: 2, summary: '', keywords: [] },
  ]);

  // 步骤4数据
  const [skipStyle, setSkipStyle] = useState(true);
  const [styleTemplateId, setStyleTemplateId] = useState<string | undefined>();

  // AI建议加载状态
  const [loadingSuggestion, setLoadingSuggestion] = useState<string | null>(null);

  // 会话ID
  const [sessionId, setSessionId] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      resetWizard();
    };
  }, []);

  const generateId = () => Math.random().toString(36).substring(2, 15);

  // 步骤1验证
  const isStep1Valid = title.trim() && objective.trim();

  // 步骤2验证
  const isStep2Valid = chapters.length > 0 && chapters.every((ch) => ch.title.trim());

  // 步骤3验证
  const isStep3Valid = chapters.every((ch) => ch.summary.trim());

  const handleNext = async () => {
    if (currentStep === 1) {
      if (!isStep1Valid) {
        MessagePlugin.warning('请填写PPT标题和制作目标');
        return;
      }

      // 创建会话并保存步骤1
      if (!sessionId) {
        try {
          const response = await outlineApi.createWizardSession();
          setSessionId(response.session_id);

          await outlineApi.saveWizardStep1(response.session_id, {
            title,
            objective,
            target_audience: targetAudience,
            duration: duration as WizardStep1Data['duration'],
          });
        } catch (error) {
          console.error('Failed to save step 1:', error);
          MessagePlugin.error('保存失败');
          return;
        }
      }
    }

    if (currentStep === 2) {
      if (!isStep2Valid) {
        MessagePlugin.warning('请填写所有章节标题');
        return;
      }

      if (sessionId) {
        try {
          const response = await outlineApi.saveWizardStep2(sessionId, {
            chapters: chapters.map((ch) => ({
              title: ch.title,
              page_count: ch.pageCount,
            })),
          });

          // 更新章节ID
          if (response.chapter_ids) {
            setChapters(
              chapters.map((ch, i) => ({
                ...ch,
                id: response.chapter_ids![i] || ch.id,
              }))
            );
          }
        } catch (error) {
          console.error('Failed to save step 2:', error);
          MessagePlugin.error('保存失败');
          return;
        }
      }
    }

    if (currentStep === 3) {
      if (!isStep3Valid) {
        MessagePlugin.warning('请填写所有章节的内容摘要');
        return;
      }

      if (sessionId) {
        try {
          await outlineApi.saveWizardStep3(sessionId, {
            chapters: chapters.map((ch) => ({
              chapter_id: ch.id,
              summary: ch.summary,
              keywords: ch.keywords,
            })),
          });
        } catch (error) {
          console.error('Failed to save step 3:', error);
          MessagePlugin.error('保存失败');
          return;
        }
      }
    }

    setCurrentStep(currentStep + 1);
  };

  const handlePrev = () => {
    setCurrentStep(currentStep - 1);
  };

  const handleComplete = async () => {
    if (!sessionId) {
      MessagePlugin.error('会话不存在');
      return;
    }

    setGenerating(true);

    try {
      // 保存步骤4
      await outlineApi.saveWizardStep4(sessionId, {
        style_template_id: styleTemplateId,
        skip_style: skipStyle,
      });

      // 完成向导
      const response = await outlineApi.completeWizard(sessionId);
      onGenerated(response.outline);
      MessagePlugin.success(response.message);

      // 重置
      resetWizard();
      setSessionId(null);
      setTitle('');
      setObjective('');
      setTargetAudience('');
      setDuration('');
      setChapters([{ id: '1', title: '', pageCount: 2, summary: '', keywords: [] }]);
      setSkipStyle(true);
      setStyleTemplateId(undefined);
      setCurrentStep(1);
    } catch (error) {
      console.error('Failed to complete wizard:', error);
      MessagePlugin.error('完成失败');
    } finally {
      setGenerating(false);
    }
  };

  // 章节操作
  const addChapter = () => {
    if (chapters.length >= 15) {
      MessagePlugin.warning('最多支持15个章节');
      return;
    }
    setChapters([
      ...chapters,
      { id: generateId(), title: '', pageCount: 2, summary: '', keywords: [] },
    ]);
  };

  const removeChapter = (index: number) => {
    if (chapters.length <= 1) {
      MessagePlugin.warning('至少需要1个章节');
      return;
    }
    setChapters(chapters.filter((_, i) => i !== index));
  };

  const updateChapter = (index: number, updates: Partial<ChapterInput>) => {
    setChapters(
      chapters.map((ch, i) => (i === index ? { ...ch, ...updates } : ch))
    );
  };

  // 获取AI建议
  const getAISuggestion = async (index: number) => {
    const chapter = chapters[index];
    if (!chapter.title.trim()) {
      MessagePlugin.warning('请先填写章节标题');
      return;
    }

    setLoadingSuggestion(chapter.id);

    try {
      const response = await outlineApi.getAISuggestion(chapter.title, objective);
      updateChapter(index, { summary: response.suggestion });
    } catch (error) {
      console.error('Failed to get AI suggestion:', error);
      MessagePlugin.error('获取建议失败');
    } finally {
      setLoadingSuggestion(null);
    }
  };

  // 添加关键词
  const addKeyword = (index: number, keyword: string) => {
    if (!keyword.trim()) return;
    const chapter = chapters[index];
    if (chapter.keywords.length >= 5) {
      MessagePlugin.warning('每章节最多5个关键词');
      return;
    }
    if (chapter.keywords.includes(keyword.trim())) return;
    updateChapter(index, { keywords: [...chapter.keywords, keyword.trim()] });
  };

  const removeKeyword = (index: number, keyword: string) => {
    const chapter = chapters[index];
    updateChapter(index, {
      keywords: chapter.keywords.filter((k) => k !== keyword),
    });
  };

  const totalPages = chapters.reduce((sum, ch) => sum + ch.pageCount, 0);

  // 渲染步骤内容
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="step-theme">
            <div className="form-item">
              <label>
                PPT标题<span className="required">*</span>
              </label>
              <Input
                value={title}
                onChange={(v) => setTitle(String(v))}
                placeholder="请输入PPT标题"
                maxlength={100}
              />
            </div>

            <div className="form-item">
              <label>
                制作目标<span className="required">*</span>
              </label>
              <Textarea
                value={objective}
                onChange={(v) => setObjective(String(v))}
                placeholder="描述制作这个PPT的主要目的"
                autosize={{ minRows: 3, maxRows: 6 }}
                maxlength={500}
              />
            </div>

            <div className="form-item">
              <label>目标受众</label>
              <div className="audience-options">
                <RadioGroup
                  value={targetAudience}
                  onChange={(v) => setTargetAudience(String(v))}
                >
                  {TARGET_AUDIENCE_OPTIONS.map((opt) => (
                    <Radio.Button key={opt.value} value={opt.value}>
                      {opt.label}
                    </Radio.Button>
                  ))}
                </RadioGroup>
              </div>
            </div>

            <div className="form-item">
              <label>预计演示时长</label>
              <div className="duration-options">
                <RadioGroup
                  value={duration}
                  onChange={(v) => setDuration(String(v))}
                >
                  {DURATION_OPTIONS.map((opt) => (
                    <Radio.Button key={opt.value} value={opt.value}>
                      {opt.label}
                    </Radio.Button>
                  ))}
                </RadioGroup>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="step-chapters">
            <div className="chapters-list">
              {chapters.map((chapter, index) => (
                <div key={chapter.id} className="chapter-item">
                  <span className="chapter-drag-handle">
                    <MoveIcon />
                  </span>
                  <span className="chapter-order">{index + 1}</span>
                  <div className="chapter-inputs">
                    <Input
                      value={chapter.title}
                      onChange={(v) =>
                        updateChapter(index, { title: String(v) })
                      }
                      placeholder="章节标题"
                    />
                  </div>
                  <div className="chapter-page-count">
                    <Slider
                      value={chapter.pageCount}
                      onChange={(v) =>
                        updateChapter(index, { pageCount: Number(v) })
                      }
                      min={1}
                      max={5}
                      step={1}
                      style={{ width: 80 }}
                    />
                    <span>{chapter.pageCount}页</span>
                  </div>
                  <div className="chapter-actions">
                    <Button
                      variant="text"
                      theme="danger"
                      icon={<DeleteIcon />}
                      onClick={() => removeChapter(index)}
                      disabled={chapters.length <= 1}
                    />
                  </div>
                </div>
              ))}
            </div>

            <Button
              className="add-chapter-btn"
              variant="dashed"
              icon={<AddIcon />}
              onClick={addChapter}
              disabled={chapters.length >= 15}
            >
              添加章节
            </Button>

            <div className="chapters-summary">
              共 <strong>{chapters.length}</strong> 个章节，预计{' '}
              <strong>{totalPages}</strong> 页
            </div>
          </div>
        );

      case 3:
        return (
          <div className="step-summaries">
            {chapters.map((chapter, index) => (
              <div key={chapter.id} className="summary-item">
                <div className="summary-header">
                  <span className="summary-title">
                    第{index + 1}章：{chapter.title || '未命名'}
                  </span>
                  <span className="summary-page-count">
                    {chapter.pageCount}页
                  </span>
                </div>

                <div className="summary-content">
                  <div className="form-item">
                    <label>
                      内容摘要<span className="required">*</span>
                    </label>
                    <Textarea
                      value={chapter.summary}
                      onChange={(v) =>
                        updateChapter(index, { summary: String(v) })
                      }
                      placeholder="描述本章节的主要内容"
                      autosize={{ minRows: 2, maxRows: 4 }}
                    />
                    <Button
                      variant="text"
                      theme="primary"
                      icon={<StarFilledIcon />}
                      loading={loadingSuggestion === chapter.id}
                      onClick={() => getAISuggestion(index)}
                      size="small"
                    >
                      AI建议
                    </Button>
                  </div>

                  <div className="form-item">
                    <label>关键词标签</label>
                    <div className="keywords-input">
                      {chapter.keywords.map((keyword) => (
                        <Tag
                          key={keyword}
                          closable
                          onClose={() => removeKeyword(index, keyword)}
                        >
                          {keyword}
                        </Tag>
                      ))}
                      <Input
                        placeholder="输入关键词后回车"
                        size="small"
                        style={{ width: 120 }}
                        onEnter={(v) => {
                          addKeyword(index, String(v));
                          return '';
                        }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        );

      case 4:
        return (
          <div className="step-style">
            <div
              className="skip-style"
              onClick={() => setSkipStyle(!skipStyle)}
            >
              <Checkbox checked={skipStyle} />
              <span>不应用风格，保留原始页面样式</span>
            </div>

            {!skipStyle && (
              <div className="style-grid">
                {['商务蓝', '科技感', '简约白', '活力橙'].map((name) => (
                  <div
                    key={name}
                    className={`style-item ${
                      styleTemplateId === name ? 'selected' : ''
                    }`}
                    onClick={() => setStyleTemplateId(name)}
                  >
                    <div className="style-preview">
                      {name === '商务蓝' && '💼'}
                      {name === '科技感' && '🔮'}
                      {name === '简约白' && '⬜'}
                      {name === '活力橙' && '🟧'}
                    </div>
                    <div className="style-name">{name}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="wizard-generate">
      <Steps current={currentStep - 1} className="wizard-steps">
        <StepItem title="主题设定" />
        <StepItem title="章节规划" />
        <StepItem title="内容摘要" />
        <StepItem title="风格选择" />
      </Steps>

      <div className="wizard-content">{renderStepContent()}</div>

      <div className="wizard-actions">
        <Button
          variant="outline"
          icon={<ChevronLeftIcon />}
          onClick={handlePrev}
          disabled={currentStep === 1}
        >
          上一步
        </Button>

        {currentStep < 4 ? (
          <Button
            theme="primary"
            onClick={handleNext}
            disabled={
              (currentStep === 1 && !isStep1Valid) ||
              (currentStep === 2 && !isStep2Valid) ||
              (currentStep === 3 && !isStep3Valid)
            }
          >
            下一步
            <ChevronRightIcon />
          </Button>
        ) : (
          <Button
            theme="primary"
            icon={<CheckCircleIcon />}
            loading={generating}
            onClick={handleComplete}
          >
            完成，生成大纲
          </Button>
        )}
      </div>
    </div>
  );
}
