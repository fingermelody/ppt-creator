import { useState } from 'react';
import { Layout, Textarea, Button, Space, Avatar, Empty } from 'tdesign-react';
import { UserIcon, ServiceIcon, ClearIcon, EnterIcon } from 'tdesign-icons-react';
import { RefinementMessage } from '../../../types/refinement';
import './ChatPanel.css';

const { Content } = Layout;

interface ChatPanelProps {
  messages: RefinementMessage[];
  onSendMessage: (message: string) => void;
}

export default function ChatPanel({ messages, onSendMessage }: ChatPanelProps) {
  const [inputMessage, setInputMessage] = useState('');

  const handleSend = () => {
    if (!inputMessage.trim()) return;
    onSendMessage(inputMessage);
    setInputMessage('');
  };

  const handleKeyDown = (_value: string, context: { e: React.KeyboardEvent<HTMLTextAreaElement> }) => {
    if (context.e.key === 'Enter' && !context.e.shiftKey) {
      context.e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      <Layout>
        <Content className="chat-messages">
          {messages.length === 0 ? (
            <Empty description="开始对话，AI将帮助您精修页面" />
          ) : (
            <div className="messages-list">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`message-item ${message.role === 'user' ? 'user' : 'assistant'}`}
                >
                  <Avatar size="large">
                    {message.role === 'user' ? <UserIcon /> : <ServiceIcon />}
                  </Avatar>
                  <div className="message-content">
                    <div className="message-bubble">
                      <p>{message.content}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Content>

        <div className="chat-input">
          <Textarea
            value={inputMessage}
            onChange={(value) => setInputMessage(String(value))}
            onKeydown={handleKeyDown}
            placeholder="输入修改指令，例如：修改标题为'产品概述'"
            autosize={{ minRows: 2, maxRows: 4 }}
          />
          <div className="input-actions">
            <Space>
              <Button variant="outline" icon={<ClearIcon />} onClick={() => setInputMessage('')}>
                清空
              </Button>
              <Button theme="primary" icon={<EnterIcon />} onClick={handleSend}>
                发送
              </Button>
            </Space>
          </div>
        </div>
      </Layout>
    </div>
  );
}
