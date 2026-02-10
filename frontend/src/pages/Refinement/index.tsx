import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Button,
  Layout,
  Space,
  DialogPlugin,
  Loading,
  Empty,
  MessagePlugin,
} from 'tdesign-react';
import { ChevronLeftIcon, DownloadIcon } from 'tdesign-icons-react';
import refinementApi from '../../api/refinement.mock';
import { RefinementMessage } from '../../types/refinement';
import { useRefinementStore } from '../../stores/refinementStore';
import PageList from './components/PageList';
import ChatPanel from './components/ChatPanel';
import './index.css';

const { Header, Content, Aside } = Layout;

export default function Refinement() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const {
    task,
    currentPageIndex,
    pages,
    messages,
    loading,
    setTask,
    setPages,
    setCurrentPageIndex,
    addMessage,
    setLoading,
  } = useRefinementStore();

  const [currentMessages, setCurrentMessages] = useState<RefinementMessage[]>([]);

  useEffect(() => {
    if (taskId) {
      loadTask(taskId);
    }
  }, [taskId]);

  useEffect(() => {
    if (currentPageIndex !== null && messages[currentPageIndex]) {
      setCurrentMessages(messages[currentPageIndex]);
    }
  }, [currentPageIndex, messages]);

  const loadTask = async (id: string) => {
    setLoading(true);
    try {
      const response = await refinementApi.getTaskDetail(id);
      setTask(response.task);
      setPages(response.pages);
      setCurrentPageIndex(response.task.current_page_index);
    } catch (error) {
      console.error('Failed to load task:', error);
      MessagePlugin.error('加载精修任务失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!taskId) return;

    const dialog = DialogPlugin.confirm({
      header: '确认导出',
      body: '确定要导出精修后的PPT吗？',
      onConfirm: async () => {
        try {
          const response = await refinementApi.exportRefinedPPT(taskId);
          window.open(response.download_url, '_blank');
          MessagePlugin.success('导出成功');
          dialog.destroy();
        } catch (error) {
          console.error('Export failed:', error);
          MessagePlugin.error('导出失败');
        }
      },
    });
  };

  const handleBackToList = () => {
    navigate('/refinement');
  };

  if (loading) {
    return (
      <div className="refinement-page loading">
        <Loading size="large" />
      </div>
    );
  }

  if (!task) {
    return (
      <div className="refinement-page empty">
        <Empty description="精修任务不存在" />
        <Button theme="primary" onClick={handleBackToList}>
          返回精修列表
        </Button>
      </div>
    );
  }

  return (
    <div className="refinement-page">
      <Layout>
        <Header className="refinement-header">
          <div className="header-left">
            <Button variant="text" icon={<ChevronLeftIcon />} onClick={handleBackToList}>
              返回
            </Button>
            <h2 className="task-title">{task.title}</h2>
          </div>
          <div className="header-right">
            <Space>
              <Button theme="primary" icon={<DownloadIcon />} onClick={handleExport}>
                导出PPT
              </Button>
            </Space>
          </div>
        </Header>

        <Layout>
          <Aside className="pages-sidebar">
            <div className="sidebar-header">
              <h3>页面列表</h3>
            </div>
            <div className="pages-list">
              {pages.length === 0 ? (
                <Empty description="暂无页面" />
              ) : (
                <PageList
                  pages={pages}
                  currentPageIndex={currentPageIndex}
                  onPageSelect={setCurrentPageIndex}
                />
              )}
            </div>
          </Aside>

          <Content className="refinement-content">
            {currentPageIndex !== null && pages[currentPageIndex] ? (
              <ChatPanel
                messages={currentMessages}
                onSendMessage={async (message) => {
                  try {
                    const response = await refinementApi.sendMessage(
                      taskId!,
                      currentPageIndex,
                      message
                    );
                    addMessage(currentPageIndex, {
                      id: response.message_id,
                      role: 'user',
                      content: message,
                      type: 'chat',
                      timestamp: new Date().toISOString(),
                    });
                    addMessage(currentPageIndex, {
                      id: `${response.message_id}-assistant`,
                      role: 'assistant',
                      content: response.assistant_message,
                      type: 'modification',
                      timestamp: new Date().toISOString(),
                    });
                  } catch (error) {
                    console.error('Send message failed:', error);
                    MessagePlugin.error('发送消息失败');
                  }
                }}
              />
            ) : (
              <Empty description="选择一个页面开始精修" />
            )}
          </Content>
        </Layout>
      </Layout>
    </div>
  );
}
