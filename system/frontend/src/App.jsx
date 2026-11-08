import { useHashRoute } from './utils.js';
import { Footer } from './components/Layout.jsx';
import ExtractPage from './pages/ExtractPage.jsx';
import HistoryPage from './pages/HistoryPage.jsx';
import ModelsPage from './pages/ModelsPage.jsx';
import PromptsPage from './pages/PromptsPage.jsx';

export default function App() {
  const [page = 'extract', param] = useHashRoute();
  const isExtract = !['history', 'models', 'prompts'].includes(page);

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Extract stays mounted so an in-progress wizard survives a visit to another page */}
      <div style={{ display: isExtract ? 'block' : 'none' }}>
        <ExtractPage active={isExtract} />
      </div>
      {page === 'history' && <HistoryPage jobId={param} />}
      {page === 'models' && <ModelsPage />}
      {page === 'prompts' && <PromptsPage />}
      <Footer />
    </div>
  );
}
