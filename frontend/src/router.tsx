import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Library from './pages/Library';
import Assembly from './pages/Assembly';
import Refinement from './pages/Refinement';
import Drafts from './pages/Drafts';

function Router() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/library" replace />} />
        <Route path="/library" element={<Library />} />
        <Route path="/assembly/:draftId?" element={<Assembly />} />
        <Route path="/refinement/:taskId" element={<Refinement />} />
        <Route path="/drafts" element={<Drafts />} />
        <Route path="*" element={<Navigate to="/library" replace />} />
      </Routes>
    </Layout>
  );
}

export default Router;
