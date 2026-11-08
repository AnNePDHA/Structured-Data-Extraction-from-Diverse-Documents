import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { formatOcrPrice, formatPrice } from '../utils.js';
import { Header, PageHeading } from '../components/Layout.jsx';
import { VendorBadge } from '../components/Dropdown.jsx';
import { IconAlert, IconBolt, IconCheck, IconEdit, IconPlus, IconTrash, IconX } from '../components/Icons.jsx';

const EMPTY = {
  id: '', display_name: '', vendor: '', provider: 'openai_compatible', supports_vision: false, fixed_temperature: false,
  price_input: '', price_output: '', endpoint: '', endpoint_env: '', key_env: '', api_version_env: '', deployment: '', min_interval_sec: '',
};

const toForm = (m) => ({
  ...EMPTY,
  ...Object.fromEntries(Object.entries(m).filter(([, v]) => v !== null && v !== undefined)),
  price_input: m.price_per_1m?.input ?? '',
  price_output: m.price_per_1m?.output ?? '',
  min_interval_sec: m.min_interval_sec ?? '',
});

const toBody = (f) => {
  const blank = (v) => (v === '' || v === null || v === undefined ? null : v);
  return {
    id: f.id.trim(),
    display_name: f.display_name.trim() || f.id.trim(),
    vendor: blank(f.vendor),
    provider: f.provider,
    supports_vision: f.supports_vision,
    fixed_temperature: f.fixed_temperature,
    price_per_1m: f.price_input !== '' && f.price_output !== '' ? { input: Number(f.price_input), output: Number(f.price_output) } : null,
    endpoint: blank(f.endpoint),
    endpoint_env: blank(f.endpoint_env),
    key_env: f.key_env.trim(),
    api_version_env: blank(f.api_version_env),
    deployment: blank(f.deployment),
    min_interval_sec: f.min_interval_sec === '' ? null : Number(f.min_interval_sec),
  };
};

const PROVIDER_HINTS = {
  azure_openai: 'Azure OpenAI chat.completions. Needs endpoint, key and API version env vars.',
  azure_foundry: 'Azure AI Foundry serverless model (endpoint ends with /models).',
  openai_compatible: 'Any OpenAI-compatible endpoint: OpenRouter, Groq, Together, vLLM, Ollama…',
  gemini: 'Google AI Studio (Gemini / Gemma). Only the key env var is needed.',
};

function Field({ label, hint, children }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
      {hint && <div className="helper">{hint}</div>}
    </div>
  );
}

function ModelForm({ initial, isNew, providers, onClose, onSaved }) {
  const [f, setF] = useState(initial);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value });

  const submit = async () => {
    setSaving(true);
    setError(null);
    try {
      const body = toBody(f);
      if (isNew) await api.createModel(body); else await api.updateModel(initial.id, body);
      onSaved();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <div className="card modal fade-in" onMouseDown={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <div className="section-title" style={{ fontSize: 17 }}>{isNew ? 'Add model endpoint' : `Edit ${initial.id}`}</div>
            <div className="section-sub">Saved to config/models.json. API keys stay in .env — only the variable name is stored.</div>
          </div>
          <button className="btn btn-ghost btn-icon" onClick={onClose}><IconX size={16} /></button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Field label="Model id" hint="Exact name sent to the API / deployment.">
            <input className="input mono" value={f.id} onChange={set('id')} disabled={!isNew} placeholder="e.g. gemini-2.5-flash" />
          </Field>
          <Field label="Display name">
            <input className="input" value={f.display_name} onChange={set('display_name')} placeholder="e.g. Gemini 2.5 Flash" />
          </Field>
          <Field label="Vendor">
            <input className="input" value={f.vendor} onChange={set('vendor')} placeholder="e.g. Google" />
          </Field>
          <Field label="Provider">
            <select className="select" value={f.provider} onChange={set('provider')}>
              {providers.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </Field>
        </div>
        <div className="helper" style={{ marginTop: 6 }}>{PROVIDER_HINTS[f.provider]}</div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 14 }}>
          <Field label="API key env var">
            <input className="input mono" value={f.key_env} onChange={set('key_env')} placeholder="e.g. OPENROUTER_API_KEY" />
          </Field>
          {f.provider !== 'gemini' && (
            <Field label="Endpoint env var" hint="Or fill a literal endpoint URL below.">
              <input className="input mono" value={f.endpoint_env} onChange={set('endpoint_env')} placeholder="e.g. AZURE_FOUNDRY_ENDPOINT" />
            </Field>
          )}
          {f.provider !== 'gemini' && (
            <Field label="Endpoint URL">
              <input className="input mono" value={f.endpoint} onChange={set('endpoint')} placeholder="https://openrouter.ai/api/v1" />
            </Field>
          )}
          {f.provider === 'azure_openai' && (
            <>
              <Field label="API version env var">
                <input className="input mono" value={f.api_version_env} onChange={set('api_version_env')} placeholder="AZURE_OPENAI_API_VERSION" />
              </Field>
              <Field label="Deployment" hint="Defaults to the model id.">
                <input className="input mono" value={f.deployment} onChange={set('deployment')} />
              </Field>
            </>
          )}
          <Field label="Price input (USD / 1M)">
            <input className="input mono" type="number" step="0.001" min="0" value={f.price_input} onChange={set('price_input')} />
          </Field>
          <Field label="Price output (USD / 1M)">
            <input className="input mono" type="number" step="0.001" min="0" value={f.price_output} onChange={set('price_output')} />
          </Field>
          <Field label="Min seconds between calls" hint="For rate-limited free tiers.">
            <input className="input mono" type="number" step="0.5" min="0" value={f.min_interval_sec} onChange={set('min_interval_sec')} />
          </Field>
        </div>

        <div style={{ display: 'flex', gap: 20, marginTop: 14 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <input type="checkbox" checked={f.supports_vision} onChange={set('supports_vision')} /> Supports images (usable for VLM Direct)
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <input type="checkbox" checked={f.fixed_temperature} onChange={set('fixed_temperature')} /> Fixed temperature (don't send 0)
          </label>
        </div>

        {error && <div className="alert alert-danger" style={{ marginTop: 14 }}><IconAlert size={15} /> {error}</div>}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 20 }}>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={submit} disabled={saving || !f.id.trim() || !f.key_env.trim()}>
            <IconCheck size={14} strokeWidth={2.5} /> {saving ? 'Saving…' : 'Save model'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ModelsPage() {
  const [models, setModels] = useState([]);
  const [ocr, setOcr] = useState([]);
  const [providers, setProviders] = useState([]);
  const [form, setForm] = useState(null);
  const [tests, setTests] = useState({});
  const [error, setError] = useState(null);

  const load = () => Promise.all([api.models(), api.ocrEngines(), api.providers()])
    .then(([m, o, p]) => { setModels(m); setOcr(o); setProviders(p); })
    .catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  const test = async (id) => {
    setTests((t) => ({ ...t, [id]: { running: true } }));
    try {
      const r = await api.testModel(id);
      setTests((t) => ({ ...t, [id]: r }));
    } catch (e) {
      setTests((t) => ({ ...t, [id]: { ok: false, error: e.message } }));
    }
  };

  const remove = async (id) => {
    if (!window.confirm(`Remove ${id} from config/models.json?`)) return;
    try { await api.deleteModel(id); load(); } catch (e) { setError(e.message); }
  };

  return (
    <>
      <Header page="models" />
      <main style={{ maxWidth: 1400, margin: '0 auto', padding: '28px 24px 48px' }}>
        <PageHeading
          title="Models"
          sub="Model endpoints, prices and capabilities from config/models.json. Changes apply to the next extraction."
          actions={<button className="btn btn-primary" onClick={() => setForm({ initial: EMPTY, isNew: true })}><IconPlus size={14} /> Add model</button>}
        />
        {error && <div className="alert alert-danger" style={{ marginBottom: 12 }}><IconAlert size={15} /> {error}</div>}

        <div className="card" style={{ overflow: 'auto', marginBottom: 28 }}>
          <table className="table">
            <thead>
              <tr><th>Model</th><th>Provider</th><th>Pipelines</th><th>Price</th><th>Credentials</th><th>Connection test</th><th /></tr>
            </thead>
            <tbody>
              {models.map((m) => {
                const t = tests[m.id];
                return (
                  <tr key={m.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <VendorBadge vendor={m.vendor || m.provider} />
                        <div>
                          <div style={{ fontWeight: 600 }}>{m.display_name || m.id}</div>
                          <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-3)' }}>{m.id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="mono" style={{ fontSize: 12 }}>{m.provider}</td>
                    <td>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {m.supports_vision && <span className="badge badge-primary">VLM Direct</span>}
                        <span className="badge badge-warning">OCR → LLM</span>
                      </div>
                    </td>
                    <td style={{ fontSize: 12, color: 'var(--text-2)' }}>
                      {formatPrice(m.price_per_1m)}
                      {m.price_source && <div><a href={m.price_source} target="_blank" rel="noreferrer" style={{ fontSize: 11 }}>source</a></div>}
                    </td>
                    <td>
                      {m.available
                        ? <span className="badge badge-success"><IconCheck size={10} strokeWidth={3} /> {m.key_env}</span>
                        : <span className="badge badge-danger" title="Add to .env">Missing {m.missing_env.join(', ')}</span>}
                    </td>
                    <td style={{ fontSize: 12, maxWidth: 260 }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => test(m.id)} disabled={!m.available || t?.running}>
                        <IconBolt size={12} /> {t?.running ? 'Testing…' : 'Test'}
                      </button>
                      {t && !t.running && (
                        <div style={{ marginTop: 6, color: t.ok ? 'var(--success)' : 'var(--danger)', wordBreak: 'break-word' }}>
                          {t.ok ? `OK · ${t.latency_sec}s` : (t.error || 'Failed').slice(0, 160)}
                        </div>
                      )}
                    </td>
                    <td style={{ whiteSpace: 'nowrap', textAlign: 'right' }}>
                      <button className="btn btn-ghost btn-icon" title="Edit" onClick={() => setForm({ initial: toForm(m), isNew: false })}><IconEdit size={14} /></button>
                      <button className="btn btn-ghost btn-icon" title="Delete" onClick={() => remove(m.id)}><IconTrash size={14} /></button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div style={{ marginBottom: 12 }}>
          <div className="section-title">OCR engines</div>
          <div className="section-sub">Read from config/ocr_engines.json, used by the OCR → LLM pipeline.</div>
        </div>
        <div className="card" style={{ overflow: 'auto' }}>
          <table className="table">
            <thead><tr><th>Engine</th><th>Type</th><th>Languages / model</th><th>Price</th><th>Credentials</th></tr></thead>
            <tbody>
              {ocr.map((o) => (
                <tr key={o.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{o.display_name}</div>
                    <div className="mono" style={{ fontSize: 11.5, color: 'var(--text-3)' }}>{o.id}</div>
                  </td>
                  <td className="mono" style={{ fontSize: 12 }}>{o.engine}</td>
                  <td className="mono" style={{ fontSize: 12 }}>{o.languages ? o.languages.join(', ') : o.model_id}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-2)' }}>{formatOcrPrice(o.price_per_page)}</td>
                  <td>
                    {o.available
                      ? <span className="badge badge-success"><IconCheck size={10} strokeWidth={3} /> {o.key_env || 'local'}</span>
                      : <span className="badge badge-danger">Missing {o.missing_env.join(', ')}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
      {form && (
        <ModelForm {...form} providers={providers} onClose={() => setForm(null)} onSaved={() => { setForm(null); load(); }} />
      )}
    </>
  );
}
