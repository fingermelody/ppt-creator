import { Layout as TLayout, Menu } from 'tdesign-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FolderIcon, EditIcon, FileCopyIcon, ViewListIcon, PreciseMonitorIcon, InternetIcon } from 'tdesign-icons-react';
import type { MenuValue } from 'tdesign-react';
import './Layout.css';

const { Header, Content, Aside } = TLayout;
const { MenuItem } = Menu;

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();

  const menuItems = [
    { value: '/generation', label: 'PPT生成', icon: <InternetIcon /> },
    { value: '/library', label: '文档库', icon: <FolderIcon /> },
    { value: '/outline', label: '大纲设计', icon: <ViewListIcon /> },
    { value: '/assembly', label: 'PPT组装', icon: <EditIcon /> },
    { value: '/refinement', label: 'PPT精修', icon: <PreciseMonitorIcon /> },
    { value: '/drafts', label: '草稿管理', icon: <FileCopyIcon /> },
  ];

  const handleMenuChange = (value: MenuValue) => {
    navigate(String(value));
  };

  // 根据当前路径确定激活的菜单项
  const getActiveMenu = () => {
    const path = location.pathname;
    if (path.startsWith('/generation')) return '/generation';
    if (path.startsWith('/library')) return '/library';
    if (path.startsWith('/assembly')) return '/assembly';
    if (path.startsWith('/outline')) return '/outline';
    if (path.startsWith('/refinement')) return '/refinement';
    return path;
  };

  return (
    <TLayout className="layout-container">
      <Header className="layout-header">
        <div className="header-content">
          <h1 className="app-title">PPT智能生成与文档库管理系统</h1>
        </div>
      </Header>
      <TLayout>
        <Aside className="layout-sider">
          <Menu
            value={getActiveMenu()}
            onChange={handleMenuChange}
            theme="light"
          >
            {menuItems.map((item) => (
              <MenuItem key={item.value} value={item.value} icon={item.icon}>
                {item.label}
              </MenuItem>
            ))}
          </Menu>
        </Aside>
        <Content className="layout-content">
          <div className="content-wrapper">{children}</div>
        </Content>
      </TLayout>
    </TLayout>
  );
}
