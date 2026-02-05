import { Layout as TLayout, Menu } from 'tdesign-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { FolderIcon, EditIcon, FileCopyIcon } from 'tdesign-icons-react';
import type { MenuValue } from 'tdesign-react';
import './Layout.css';

const { Header, Content, Aside } = TLayout;
const { MenuItem } = Menu;

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();

  const menuItems = [
    { value: '/library', label: '文档库', icon: <FolderIcon /> },
    { value: '/assembly', label: 'PPT组装', icon: <EditIcon /> },
    { value: '/drafts', label: '草稿管理', icon: <FileCopyIcon /> },
  ];

  const handleMenuChange = (value: MenuValue) => {
    navigate(String(value));
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
            value={location.pathname.startsWith('/assembly') ? '/assembly' : location.pathname}
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
