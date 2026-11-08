import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { PIPELINE_LABEL } from '../utils.js';
import { Header, PageHeading } from '../components/Layout.jsx';
import { IconAlert, IconCheck, IconDoc, IconSave } from '../components/Icons.jsx';

const PLACEHOLDERS = [
  ['{{fields_schema}}', 'Bullet list of fields with description and format'],
  ['{{field_names}}', 'Comma-separated field keys expected in the JSON'],
  ['{{ocr_text}}', 'OCR output (OCR → LLM pipeline only)'],
];

export default function PromptsPage() {
  const [prompts, setPrompts] = useState([]);
  const [active, setActive] = useState(null);
  const [text, setText] = useState('');
  const [original, setOriginal] = useState('');
  const [status, setStatus] = useState(null);

  useEffect(() => {
    api.prompts().then((list) => {
      setPrompts(list);
      if (list.length) setActive(list[0].name);
    }).catch((e) => setStatus({ error: e.message }));
  }, []);

  useEffect(() => {
    if (!active) return;
    setStatus(null);
    api.prompt(active).then((p) => { setText(p.text); setOriginal(p.text); }).catch((e) => setStatus({ error: e.message }));
  }, [active]);

  const dirty = text !== original;

  const save = async () => {
    setStatus(null);
    try {
      await api.savePrompt(active, text);
      setOriginal(text);
      setStatus({ ok: `Saved to config/prompts/${active}` });
    } catch (e) {
      setStatus({ error: e.message });
    }
  };

  const select = (name) => {
    if (dirty && !window.confirm('Discard unsaved changes?')) return;
    setActive(name);
  };

  return (
    <>
      <Header page="prompts" />
      <main style={{ maxWidth: 1400, margin: '0 auto', padding: '28px 24px 48px' }}>
        <PageHeading
          title="Prompt templates"
          sub="The same templates used for the 540-run benchmark. Edits apply to the next extraction."
        />
        <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 300px) minmax(0, 1fr)', gap: 24 }}>
          <div>
            <div className="card" style={{ padding: 6, marginBottom: 16 }}>
              {prompts.map((p) => (
                <button key={p.name} onClick={() => select(p.name)} style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', border: 0, borderRadius: 6, textAlign: 'left',
                  background: p.name === active ? 'var(--primary-50)' : 'transparent', color: p.name === active ? 'var(--primary)' : 'var(--text)',
                }}>
                  <IconDoc size={14} />
                  <span className="mono" style={{ flex: 1, fontSize: 13, fontWeight: p.name === active ? 600 : 500 }}>{p.name}</span>
                  {p.default_for && <span className="badge">{PIPELINE_LABEL[p.default_for]}</span>}
                </button>
              ))}
            </div>
            <div className="card" style={{ padding: 16 }}>
              <div className="section-title" style={{ fontSize: 13.5, marginBottom: 8 }}>Placeholders</div>
              {PLACEHOLDERS.map(([k, d]) => (
                <div key={k} style={{ marginBottom: 8 }}>
                  <div className="mono" style={{ fontSize: 12, color: 'var(--primary)', fontWeight: 600 }}>{k}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-2)' }}>{d}</div>
                </div>
              ))}
              <div className="helper">Field lists come from the selected schema in config/fields/*.json.</div>
            </div>
          </div>

          <div className="card" style={{ padding: 20, minWidth: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, gap: 12, flexWrap: 'wrap' }}>
              <div>
                <div className="section-title mono">config/prompts/{active}</div>
                <div className="section-sub">{dirty ? 'Unsaved changes' : 'Saved'}</div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-ghost btn-sm" disabled={!dirty} onClick={() => setText(original)}>Revert</button>
                <button className="btn btn-primary btn-sm" disabled={!dirty} onClick={save}><IconSave size={13} /> Save template</button>
              </div>
            </div>
            {status?.error && <div className="alert alert-danger" style={{ marginBottom: 10 }}><IconAlert size={15} /> {status.error}</div>}
            {status?.ok && <div className="alert alert-info" style={{ marginBottom: 10, color: 'var(--success)' }}><IconCheck size={15} /> {status.ok}</div>}
            <textarea
              className="textarea mono" value={text} onChange={(e) => setText(e.target.value)} spellCheck={false}
              style={{ minHeight: 'calc(100vh - 330px)', fontSize: 13, lineHeight: 1.6 }}
            />
          </div>
        </div>
      </main>
    </>
  );
}
