import { useState } from 'react';
import { Input, Textarea, Tag, Button, Space, MessagePlugin } from 'tdesign-react';
import { EditIcon, CheckIcon, CloseIcon, AddIcon, DeleteIcon } from 'tdesign-icons-react';
import type { PPTOutline, OutlineChapter } from '../../../types/outline';

interface OutlinePreviewProps {
  outline: PPTOutline;
  onUpdate: (outline: PPTOutline) => void;
}

export default function OutlinePreview({ outline, onUpdate }: OutlinePreviewProps) {
  const [editingTitle, setEditingTitle] = useState(false);
  const [editingObjective, setEditingObjective] = useState(false);
  const [editingChapterId, setEditingChapterId] = useState<string | null>(null);
  
  const [tempTitle, setTempTitle] = useState(outline.title);
  const [tempObjective, setTempObjective] = useState(outline.objective);
  const [tempChapterTitle, setTempChapterTitle] = useState('');
  const [tempChapterSummary, setTempChapterSummary] = useState('');

  // 编辑标题
  const startEditTitle = () => {
    setTempTitle(outline.title);
    setEditingTitle(true);
  };

  const saveTitle = () => {
    if (!tempTitle.trim()) {
      MessagePlugin.warning('标题不能为空');
      return;
    }
    onUpdate({ ...outline, title: tempTitle.trim() });
    setEditingTitle(false);
  };

  const cancelEditTitle = () => {
    setTempTitle(outline.title);
    setEditingTitle(false);
  };

  // 编辑制作目标
  const startEditObjective = () => {
    setTempObjective(outline.objective);
    setEditingObjective(true);
  };

  const saveObjective = () => {
    onUpdate({ ...outline, objective: tempObjective });
    setEditingObjective(false);
  };

  const cancelEditObjective = () => {
    setTempObjective(outline.objective);
    setEditingObjective(false);
  };

  // 编辑章节
  const startEditChapter = (chapter: OutlineChapter) => {
    setEditingChapterId(chapter.id);
    setTempChapterTitle(chapter.title);
    setTempChapterSummary(chapter.summary);
  };

  const saveChapter = () => {
    if (!tempChapterTitle.trim()) {
      MessagePlugin.warning('章节标题不能为空');
      return;
    }
    
    const updatedChapters = outline.chapters.map((ch) =>
      ch.id === editingChapterId
        ? { ...ch, title: tempChapterTitle.trim(), summary: tempChapterSummary }
        : ch
    );
    
    onUpdate({ ...outline, chapters: updatedChapters });
    setEditingChapterId(null);
  };

  const cancelEditChapter = () => {
    setEditingChapterId(null);
  };

  // 删除章节
  const deleteChapter = (chapterId: string) => {
    if (outline.chapters.length <= 1) {
      MessagePlugin.warning('至少需要保留一个章节');
      return;
    }
    
    const updatedChapters = outline.chapters.filter((ch) => ch.id !== chapterId);
    const recalculatedChapters = updatedChapters.map((ch, index) => ({
      ...ch,
      order: index + 1,
    }));
    
    const totalPages = recalculatedChapters.reduce((sum, ch) => sum + ch.page_count, 0);
    
    onUpdate({
      ...outline,
      chapters: recalculatedChapters,
      total_pages: totalPages,
    });
    
    MessagePlugin.success('章节已删除');
  };

  // 添加章节
  const addChapter = () => {
    const newChapter: OutlineChapter = {
      id: `chapter-${Date.now()}`,
      title: '新章节',
      summary: '',
      page_count: 2,
      order: outline.chapters.length + 1,
      keywords: [],
    };
    
    onUpdate({
      ...outline,
      chapters: [...outline.chapters, newChapter],
      total_pages: outline.total_pages + 2,
    });
  };

  // 调整章节顺序
  const moveChapter = (index: number, direction: 'up' | 'down') => {
    if (
      (direction === 'up' && index === 0) ||
      (direction === 'down' && index === outline.chapters.length - 1)
    ) {
      return;
    }

    const newChapters = [...outline.chapters];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    [newChapters[index], newChapters[targetIndex]] = [newChapters[targetIndex], newChapters[index]];
    
    const reorderedChapters = newChapters.map((ch, i) => ({
      ...ch,
      order: i + 1,
    }));
    
    onUpdate({ ...outline, chapters: reorderedChapters });
  };

  return (
    <div className="outline-preview">
      {/* 标题区域 */}
      <div className="preview-header">
        {editingTitle ? (
          <div className="edit-row">
            <Input
              value={tempTitle}
              onChange={(v) => setTempTitle(String(v))}
              placeholder="PPT标题"
              maxlength={100}
            />
            <Space size="small">
              <Button
                variant="text"
                theme="primary"
                icon={<CheckIcon />}
                onClick={saveTitle}
              />
              <Button
                variant="text"
                icon={<CloseIcon />}
                onClick={cancelEditTitle}
              />
            </Space>
          </div>
        ) : (
          <div className="preview-title" onClick={startEditTitle}>
            {outline.title || '未命名大纲'}
            <EditIcon className="edit-icon" />
          </div>
        )}

        {editingObjective ? (
          <div className="edit-row">
            <Textarea
              value={tempObjective}
              onChange={(v) => setTempObjective(String(v))}
              placeholder="制作目标"
              autosize={{ minRows: 2, maxRows: 4 }}
            />
            <Space size="small" direction="vertical">
              <Button
                variant="text"
                theme="primary"
                icon={<CheckIcon />}
                onClick={saveObjective}
              />
              <Button
                variant="text"
                icon={<CloseIcon />}
                onClick={cancelEditObjective}
              />
            </Space>
          </div>
        ) : (
          <div className="preview-objective" onClick={startEditObjective}>
            {outline.objective || '点击添加制作目标'}
            <EditIcon className="edit-icon" />
          </div>
        )}

        <div className="preview-meta">
          <span>
            {outline.generation_type === 'smart' ? '智能生成' : '向导式生成'}
          </span>
          {outline.target_audience && <span>受众：{outline.target_audience}</span>}
          {outline.duration && <span>时长：{outline.duration}</span>}
        </div>
      </div>

      {/* 章节列表 */}
      <div className="preview-chapters">
        {outline.chapters.map((chapter, index) => (
          <div key={chapter.id} className="preview-chapter">
            <div className="preview-chapter-order">{index + 1}</div>
            <div className="preview-chapter-content">
              {editingChapterId === chapter.id ? (
                <div className="chapter-edit-form">
                  <Input
                    value={tempChapterTitle}
                    onChange={(v) => setTempChapterTitle(String(v))}
                    placeholder="章节标题"
                    style={{ marginBottom: 8 }}
                  />
                  <Textarea
                    value={tempChapterSummary}
                    onChange={(v) => setTempChapterSummary(String(v))}
                    placeholder="内容摘要"
                    autosize={{ minRows: 2, maxRows: 4 }}
                  />
                  <div className="chapter-edit-actions">
                    <Button
                      size="small"
                      theme="primary"
                      onClick={saveChapter}
                    >
                      保存
                    </Button>
                    <Button
                      size="small"
                      variant="outline"
                      onClick={cancelEditChapter}
                    >
                      取消
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <div
                    className="preview-chapter-title"
                    onClick={() => startEditChapter(chapter)}
                  >
                    {chapter.title}
                    <EditIcon className="edit-icon" />
                  </div>
                  {chapter.summary && (
                    <div className="preview-chapter-summary">{chapter.summary}</div>
                  )}
                  <div className="preview-chapter-meta">
                    <Tag size="small" variant="light">
                      {chapter.page_count}页
                    </Tag>
                    {chapter.keywords?.map((keyword) => (
                      <Tag key={keyword} size="small" variant="outline">
                        {keyword}
                      </Tag>
                    ))}
                  </div>
                </>
              )}
            </div>
            <div className="preview-chapter-actions">
              <Button
                variant="text"
                size="small"
                onClick={() => moveChapter(index, 'up')}
                disabled={index === 0}
              >
                ↑
              </Button>
              <Button
                variant="text"
                size="small"
                onClick={() => moveChapter(index, 'down')}
                disabled={index === outline.chapters.length - 1}
              >
                ↓
              </Button>
              <Button
                variant="text"
                size="small"
                theme="danger"
                icon={<DeleteIcon />}
                onClick={() => deleteChapter(chapter.id)}
              />
            </div>
          </div>
        ))}
      </div>

      {/* 添加章节按钮 */}
      <Button
        variant="dashed"
        icon={<AddIcon />}
        onClick={addChapter}
        style={{ width: '100%' }}
      >
        添加章节
      </Button>

      {/* 总计 */}
      <div className="preview-total">
        共 <strong>{outline.chapters.length}</strong> 个章节，
        预计 <strong>{outline.total_pages}</strong> 页
      </div>
    </div>
  );
}
