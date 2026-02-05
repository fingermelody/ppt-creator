import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'tdesign-react';
import Router from './router';
import 'tdesign-react/es/style/index.css';
import './App.css';

function App() {
  return (
    <ConfigProvider>
      <BrowserRouter>
        <Router />
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;
