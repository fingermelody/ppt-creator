import { HashRouter } from 'react-router-dom';
import { ConfigProvider } from 'tdesign-react';
import Router from './router';
import 'tdesign-react/es/style/index.css';
import './App.css';

function App() {
  return (
    <ConfigProvider>
      <HashRouter>
        <Router />
      </HashRouter>
    </ConfigProvider>
  );
}

export default App;
