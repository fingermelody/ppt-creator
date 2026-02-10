/* 生成进度弹窗组件 */

import { Dialog, Progress, Button, Space } from 'tdesign-react';
import {
  SearchIcon,
  ChartBarIcon,
  FileIcon,
  EditIcon,
  CheckCircleIcon,
  CloseCircleIcon,
  LoadingIcon,
} from 'tdesign-icons-react';
import type { GenerationStatus } from '../../../types/generation';
import './ProgressModal.css';

interface ProgressModalProps {
  visible: boolean;
  status: GenerationStatus;
  progress: number;
  message: string;
  onCancel: () => void;
  onComplete: () => void;
}

const STEPS = [
  { key: 'searching', label: '搜索信息', icon: SearchIcon },
  { key: 'analyzing', label: '分析内容', icon: ChartBarIcon },
  { key: 'generating', label: '生成PPT', icon: FileIcon },
  { key: 'applying_style', label: '应用风格', icon: EditIcon },
] as const;

export default function ProgressModal({
  visible,
  status,
  progress,
  message,
  onCancel,
  onComplete,
}: ProgressModalProps) {
  const isCompleted = status === 'completed';
  const isFailed = status === 'failed';
  const isProcessing = !isCompleted && !isFailed;

  const getStepStatus = (stepKey: string): 'pending' | 'active' | 'completed' => {
    const stepOrder = STEPS.map((s) => s.key);
    const currentIndex = stepOrder.indexOf(status as any);
    const stepIndex = stepOrder.indexOf(stepKey as any);

    if (isCompleted || isFailed) {
      return stepIndex <= currentIndex ? 'completed' : 'pending';
    }
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <Dialog
      visible={visible}
      header={isCompleted ? '生成完成' : isFailed ? '生成失败' : 'PPT生成中'}
      footer={false}
      closeOnOverlayClick={false}
      closeOnEscKeydown={false}
      onClose={onCancel}
      width={500}
    >
      <div className="progress-modal-content">
        {/* 进度条 */}
        <div className="progress-section">
          <Progress
            percentage={progress}
            theme={isFailed ? 'danger' : isCompleted ? 'success' : 'default'}
            size="large"
            label={`${progress}%`}
          />
        </div>

        {/* 状态消息 */}
        <div className={`status-message ${isFailed ? 'error' : ''}`}>
          {isProcessing && <LoadingIcon className="spinning" />}
          {isCompleted && <CheckCircleIcon className="success" />}
          {isFailed && <CloseCircleIcon className="error" />}
          <span>{message}</span>
        </div>

        {/* 步骤指示器 */}
        <div className="steps-indicator">
          {STEPS.map((step, index) => {
            const stepStatus = getStepStatus(step.key);
            const Icon = step.icon;
            return (
              <div key={step.key} className={`step-item ${stepStatus}`}>
                <div className="step-icon">
                  {stepStatus === 'completed' ? (
                    <CheckCircleIcon />
                  ) : stepStatus === 'active' ? (
                    <LoadingIcon className="spinning" />
                  ) : (
                    <Icon />
                  )}
                </div>
                <span className="step-label">{step.label}</span>
                {index < STEPS.length - 1 && <div className="step-connector" />}
              </div>
            );
          })}
        </div>

        {/* 操作按钮 */}
        <div className="modal-actions">
          {isProcessing && (
            <Button theme="default" onClick={onCancel}>
              取消生成
            </Button>
          )}
          {isCompleted && (
            <Space>
              <Button theme="default" onClick={onCancel}>
                继续创建
              </Button>
              <Button theme="primary" onClick={onComplete}>
                查看结果
              </Button>
            </Space>
          )}
          {isFailed && (
            <Space>
              <Button theme="default" onClick={onCancel}>
                关闭
              </Button>
              <Button theme="primary" onClick={onCancel}>
                重新生成
              </Button>
            </Space>
          )}
        </div>
      </div>
    </Dialog>
  );
}
