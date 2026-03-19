import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Library from './pages/Library';
import Outline from './pages/Outline';
import Assembly from './pages/Assembly';
import Refinement from './pages/Refinement';
import RefinementList from './pages/Refinement/List';
import Generation from './pages/Generation';
import Drafts from './pages/Drafts';

function Router() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/generation" replace />} />
        <Route path="/generation" element={<Generation />} />
        <Route path="/library" element={<Library />} />
        <Route path="/outline" element={<Outline />} />
        <Route path="/assembly/:draftId?" element={<Assembly />} />
        <Route path="/refinement" element={<RefinementList />} />
        <Route path="/refinement/:taskId" element={<Refinement />} />
        <Route path="/drafts" element={<Drafts />} />
        <Route path="*" element={<Navigate to="/generation" replace />} />
      </Routes>
    </Layout>
  );
}

export default Router;
