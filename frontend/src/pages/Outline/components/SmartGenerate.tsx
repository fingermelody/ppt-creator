import { useState } from 'react';
import { Button, Textarea, Space, MessagePlugin, Alert } from 'tdesign-react';
import outlineApi from '../../../api/outline.mock';
import { useOutlineStore } from '../../../stores/outlineStore';
import type { PPTOutline } from '../../../types/outline';

interface SmartGenerateProps {
  onGenerated: (outline: PPTOutline) => void;
}

const PLACEHOLDER_TEXT = `请描述您要制作的PPT，建议包含以下信息：

【PPT主题】如：2024年度产品发布会
【制作目标】如：向客户介绍新产品的核心功能和优势
【章节规划】如：
  - 第一章：公司简介（介绍公司背景和发展历程）
  - 第二章：产品概述（展示产品定位和核心卖点）
  - 第三章：功能详解（详细说明产品的主要功能）
  - 第四章：案例展示（展示成功客户案例）
  - 第五章：商务合作（说明合作方式和联系方式）

示例输入：
"我需要制作一个关于AI智能客服系统的产品介绍PPT，目标是向潜在客户展示我们产品的技术优势和应用价值。内容包括：公司介绍、产品核心功能（智能问答、多轮对话、知识库管理）、技术架构、客户案例、商务报价。风格偏商务简约。"`;

const EXAMPLE_TEXT = `我需要制作一个关于AI智能客服系统的产品介绍PPT，目标是向潜在客户展示我们产品的技术优势和应用价值。

【PPT主题】AI智能客服系统产品介绍

【制作目标】向潜在客户展示产品技术优势和应用价值，促成商务合作

【章节规划】
- 第一章：公司简介（公司背景、发展历程、核心团队）
- 第二章：产品概述（产品定位、核心功能介绍）
- 第三章：功能详解（智能问答、多轮对话、知识库管理）
- 第四章：技术架构（系统架构、技术亮点）
- 第五章：客户案例（典型客户、应用效果）
- 第六章：商务合作（报价方案、联系方式）

风格偏好：商务简约风格`;

const MIN_LENGTH = 100;
const MAX_LENGTH = 2000;

export default function SmartGenerate({ onGenerated }: SmartGenerateProps) {
  const { smartDescription, setSmartDescription, generating, setGenerating } =
    useOutlineStore();
  
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [confidence, setConfidence] = useState<number | null>(null);

  const charCount = smartDescription.length;
  const isValidLength = charCount >= MIN_LENGTH && charCount <= MAX_LENGTH;
  const isUnderMin = charCount > 0 && charCount < MIN_LENGTH;
  const isOverMax = charCount > MAX_LENGTH;

  const handleGenerate = async () => {
    if (!isValidLength) {
      if (isUnderMin) {
        MessagePlugin.warning(`描述内容至少需要${MIN_LENGTH}字`);
      } else if (isOverMax) {
        MessagePlugin.warning(`描述内容不能超过${MAX_LENGTH}字`);
      }
      return;
    }

    setGenerating(true);
    setSuggestions([]);
    setConfidence(null);

    try {
      const response = await outlineApi.smartGenerate({
        description: smartDescription,
      });

      onGenerated(response.outline);
      setSuggestions(response.suggestions);
      setConfidence(response.confidence);
      MessagePlugin.success('大纲生成成功');
    } catch (error) {
      console.error('Smart generate failed:', error);
      MessagePlugin.error('生成失败，请重试');
    } finally {
      setGenerating(false);
    }
  };

  const handleClear = () => {
    setSmartDescription('');
    setSuggestions([]);
    setConfidence(null);
  };

  const handleLoadExample = () => {
    setSmartDescription(EXAMPLE_TEXT);
  };

  const getCharCountClass = () => {
    if (isOverMax) return 'char-count error';
    if (isUnderMin) return 'char-count warning';
    return 'char-count';
  };

  return (
    <div className="smart-generate">
      <div className="smart-input-area">
        <Textarea
          value={smartDescription}
          onChange={(value) => setSmartDescription(String(value))}
          placeholder={PLACEHOLDER_TEXT}
          autosize={{ minRows: 10, maxRows: 20 }}
          maxlength={MAX_LENGTH + 100}
          disabled={generating}
        />
      </div>

      <div className="smart-actions">
        <Space>
          <Button
            variant="text"
            onClick={handleLoadExample}
            disabled={generating}
          >
            查看示例
          </Button>
          <Button
            variant="text"
            onClick={handleClear}
            disabled={generating || !smartDescription}
          >
            清空
          </Button>
        </Space>

        <Space>
          <span className={getCharCountClass()}>
            {charCount} / {MAX_LENGTH} 字
            {isUnderMin && ` (至少${MIN_LENGTH}字)`}
          </span>
          <Button
            theme="primary"
            loading={generating}
            disabled={!isValidLength}
            onClick={handleGenerate}
          >
            智能生成大纲
          </Button>
        </Space>
      </div>

      {suggestions.length > 0 && (
        <Alert
          theme="info"
          title="优化建议"
          message={
            <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
              {suggestions.map((suggestion, index) => (
                <li key={index}>{suggestion}</li>
              ))}
            </ul>
          }
          style={{ marginTop: '16px' }}
        />
      )}

      {confidence !== null && (
        <div style={{ marginTop: '12px', fontSize: '13px', color: '#8f959e' }}>
          生成置信度：{Math.round(confidence * 100)}%
        </div>
      )}
    </div>
  );
}
