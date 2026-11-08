import { ModelDropdown } from '../components/Dropdown.jsx';
import { IconCheck, IconInfo } from '../components/Icons.jsx';
import { formatOcrPrice, formatPrice } from '../utils.js';

const VLMIllustration = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <rect x="3" y="5" width="14" height="18" rx="2" stroke="currentColor" strokeWidth="1.6" />
    <line x1="6" y1="9" x2="14" y2="9" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" opacity="0.5" />
    <line x1="6" y1="12" x2="14" y2="12" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" opacity="0.5" />
    <line x1="6" y1="15" x2="11" y2="15" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" opacity="0.5" />
    <path d="M19 14 c1 -3 4 -4 6 -1 c-2 3 -5 3 -6 1z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    <circle cx="22" cy="13" r="1.2" fill="currentColor" />
  </svg>
);

const OCRIllustration = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <rect x="2" y="6" width="10" height="16" rx="1.5" stroke="currentColor" strokeWidth="1.6" />
    <line x1="4.5" y1="10" x2="9.5" y2="10" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    <line x1="4.5" y1="13" x2="9.5" y2="13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    <line x1="4.5" y1="16" x2="8" y2="16" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
    <path d="M13.5 14 L17.5 14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    <path d="M16 12 L18 14 L16 16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="22" cy="14" r="4" stroke="currentColor" strokeWidth="1.6" />
    <path d="M20.5 14 L21.5 15 L23.5 13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

// UI copy per pipeline id; ids and display names come from config/app.json
const PIPELINE_UI = {
  vlm_direct: {
    icon: <VLMIllustration />, accent: 'var(--primary)', tone: 'primary',
    title: 'VLM Pipeline',
    description: 'Directly sends the document image into a vision-language model without OCR.',
    badges: ['Faster', 'Fewer steps', 'Handles handwriting'],
  },
  ocr_llm: {
    icon: <OCRIllustration />, accent: 'var(--warning)', tone: 'warning',
    title: 'OCR → LLM Pipeline',
    description: 'Text is recognized first by an OCR engine, then structured by the language model.',
    badges: ['Better control', 'Text-only models', 'Ideal for clean text'],
  },
};

function PipelineCard({ active, onClick, ui }) {
  const ring = ui.tone === 'primary' ? 'rgba(30,64,175,0.12)' : 'rgba(217,119,6,0.12)';
  return (
    <button onClick={onClick} style={{
      flex: 1, minWidth: 240, textAlign: 'left', padding: 22, background: '#fff', borderRadius: 14, position: 'relative',
      border: `1px solid ${active ? ui.accent : 'var(--border-strong)'}`,
      boxShadow: active ? `0 0 0 4px ${ring}, var(--shadow)` : 'var(--shadow)',
      transition: 'all .18s ease', color: 'inherit', display: 'flex', flexDirection: 'column',
    }}>
      {active && (
        <div style={{
          position: 'absolute', top: 14, right: 14, width: 26, height: 26, borderRadius: '50%', background: ui.accent,
          color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <IconCheck size={14} strokeWidth={3} />
        </div>
      )}
      <div style={{
        width: 48, height: 48, borderRadius: 12, marginBottom: 14, transition: 'all .18s',
        background: active ? ui.accent : '#F1F4F9', color: active ? '#fff' : ui.accent,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>{ui.icon}</div>
      <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 6 }}>{ui.title}</div>
      <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.55, marginBottom: 14 }}>{ui.description}</div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 'auto' }}>
        {ui.badges.map((b) => (
          <span key={b} className={`badge ${active ? `badge-${ui.tone}` : ''}`}>{b}</span>
        ))}
      </div>
    </button>
  );
}

export function PipelineSection({ pipelines, pipeline, setPipeline }) {
  return (
    <div className="card fade-in" style={{ padding: 20, marginBottom: 16 }}>
      <div style={{ marginBottom: 14 }}>
        <div className="section-title">Extraction pipeline</div>
        <div className="section-sub">Pick the strategy. Model options appear once you choose.</div>
      </div>
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
        {pipelines.filter((p) => PIPELINE_UI[p.id]).map((p) => (
          <PipelineCard key={p.id} active={pipeline === p.id} onClick={() => setPipeline(p.id)} ui={PIPELINE_UI[p.id]} />
        ))}
      </div>
    </div>
  );
}

const modelOption = (m) => ({
  id: m.id,
  vendor: m.vendor || m.provider,
  title: m.display_name || m.id,
  subtitle: formatPrice(m.price_per_1m),
  tag: !m.available ? 'Missing API key' : m.supports_vision ? null : 'Text only',
  tagTone: !m.available ? 'danger' : null,
  disabled: !m.available,
  disabledReason: m.available ? undefined : `Set ${m.missing_env.join(', ')} in .env`,
});

const ocrOption = (o) => ({
  id: o.id,
  vendor: o.vendor,
  title: o.display_name || o.id,
  subtitle: formatOcrPrice(o.price_per_page),
  tag: !o.available ? 'Missing API key' : o.languages ? o.languages.join(' + ') : o.model_id,
  tagTone: !o.available ? 'danger' : null,
  disabled: !o.available,
});

export function ModelSection({ pipeline, models, ocrEngines, prompts, config, setConfig }) {
  const vlmModels = models.filter((m) => m.supports_vision);
  const set = (patch) => setConfig({ ...config, ...patch });
  const pipelinePrompts = prompts.map((p) => p.name);

  return (
    <div className="card fade-in" style={{ padding: 20, marginBottom: 16 }}>
      <div style={{ marginBottom: 14 }}>
        <div className="section-title">Model configuration</div>
        <div className="section-sub">
          {pipeline === 'vlm_direct'
            ? 'Pick a vision-language model that reads the document directly.'
            : 'OCR engine extracts text; the LLM structures it into your fields.'}
        </div>
      </div>

      {pipeline === 'vlm_direct' ? (
        <ModelDropdown label="VLM model" options={vlmModels.map(modelOption)} value={config.model} onChange={(id) => set({ model: id })} />
      ) : (
        <div style={{ display: 'grid', gap: 14 }}>
          <ModelDropdown label="OCR engine" hint="Reads characters off the page image (config/ocr_engines.json)."
            options={ocrEngines.map(ocrOption)} value={config.ocr} onChange={(id) => set({ ocr: id })} placeholder="Select an OCR engine…" />
          <ModelDropdown label="LLM model" hint="Structures raw text into your fields."
            options={models.map(modelOption)} value={config.model} onChange={(id) => set({ model: id })} />
        </div>
      )}

      <div style={{ marginTop: 14 }}>
        <label className="label">Prompt template</label>
        <select className="select mono" value={config.prompt || ''} onChange={(e) => set({ prompt: e.target.value })}>
          {pipelinePrompts.map((n) => <option key={n} value={n}>config/prompts/{n}</option>)}
        </select>
      </div>

      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-2)', fontSize: 12.5, marginTop: 14,
        padding: '10px 14px', background: 'var(--primary-50)', border: '1px solid #DCE6FE', borderRadius: 8,
      }}>
        <IconInfo size={14} style={{ color: 'var(--primary)', flexShrink: 0 }} />
        <span>Models, prices and OCR engines are read from <span className="mono">config/</span>. Add new endpoints on the <a href="#/models">Models</a> page.</span>
      </div>
    </div>
  );
}
