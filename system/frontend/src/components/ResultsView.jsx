import { Fragment, useEffect, useMemo, useState } from 'react';
import { api } from '../api.js';
import { formatUsd, PIPELINE_LABEL } from '../utils.js';
import {
  IconAlert, IconCheck, IconClock, IconCode, IconCopy, IconDownload, IconEdit, IconFile, IconInfo, IconLayout, IconPackage, IconSave, IconX,
} from './Icons.jsx';

// ============ JSON VIEW ============

const renderJsonValue = (val, indent) => {
  const pad = '  '.repeat(indent);
  if (val === null) return <span style={{ color: '#9CA3AF' }}>null</span>;
  if (typeof val === 'number') return <span style={{ color: '#F59E0B' }}>{String(val)}</span>;
  if (typeof val === 'boolean') return <span style={{ color: '#A78BFA' }}>{String(val)}</span>;
  if (typeof val === 'string') return <span style={{ color: '#86EFAC' }}>"{val}"</span>;
  if (Array.isArray(val)) {
    if (val.length === 0) return <span>[]</span>;
    return (
      <>
        [
        {val.map((v, i) => (
          <Fragment key={i}>{'\n'}{pad}  {renderJsonValue(v, indent + 1)}{i < val.length - 1 ? ',' : ''}</Fragment>
        ))}
        {'\n'}{pad}]
      </>
    );
  }
  if (typeof val === 'object') {
    const keys = Object.keys(val);
    if (keys.length === 0) return <span>{'{}'}</span>;
    return (
      <>
        {'{'}
        {keys.map((k, i) => (
          <Fragment key={k}>
            {'\n'}{pad}  <span style={{ color: '#7DD3FC' }}>"{k}"</span>: {renderJsonValue(val[k], indent + 1)}{i < keys.length - 1 ? ',' : ''}
          </Fragment>
        ))}
        {'\n'}{pad}{'}'}
      </>
    );
  }
  return <span>{String(val)}</span>;
};

function JsonView({ job }) {
  const [payload, setPayload] = useState(null);
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    api.exportJson(job.id).then((t) => setPayload(JSON.parse(t))).catch(() => setPayload(null));
  }, [job.id, job.edited_fields]);

  const copy = () => {
    navigator.clipboard?.writeText(JSON.stringify(payload, null, 2)).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, gap: 10, flexWrap: 'wrap' }}>
        <div style={{ fontSize: 12, color: 'var(--text-3)', fontFamily: 'var(--mono)' }}>{job.id}.json — fields + run metadata</div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn btn-secondary btn-sm" onClick={copy} disabled={!payload}>
            <IconCopy size={13} /> {copied ? 'Copied' : 'Copy JSON'}
          </button>
          <a className="btn btn-secondary btn-sm" href={api.exportUrl(job.id, 'json')}>
            <IconDownload size={13} /> Download .json
          </a>
        </div>
      </div>
      <div style={{ background: '#0F172A', borderRadius: 10, overflow: 'hidden', border: '1px solid #1E293B' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 14px', borderBottom: '1px solid #1E293B', background: '#0B1220' }}>
          {[0, 1, 2].map((i) => <div key={i} style={{ width: 10, height: 10, borderRadius: '50%', background: '#475569' }} />)}
          <div style={{ marginLeft: 8, fontSize: 11, color: '#64748B', fontFamily: 'var(--mono)' }}>application/json</div>
        </div>
        <pre style={{
          margin: 0, padding: '18px 20px', color: '#E2E8F0', fontFamily: 'var(--mono)', fontSize: 12.5, lineHeight: 1.65,
          maxHeight: 'calc(100vh - 380px)', minHeight: 200, overflow: 'auto', whiteSpace: 'pre',
        }}>
          {payload ? renderJsonValue(payload, 0) : 'Loading…'}
        </pre>
      </div>
    </div>
  );
}

// ============ ARTIFACTS VIEW ============

const ARTIFACT_LABELS = {
  'prompt.txt': 'Rendered prompt',
  'ocr_text.txt': 'OCR text',
  'raw_response.txt': 'Raw model response',
  'request.json': 'Request',
  'fields.json': 'Field config',
};

function ArtifactsView({ job }) {
  const names = job.artifacts || [];
  const [active, setActive] = useState(names[0]);
  const [content, setContent] = useState('');
  useEffect(() => {
    if (!active) return;
    setContent('Loading…');
    api.jobArtifact(job.id, active).then(setContent).catch((e) => setContent(`Error: ${e.message}`));
  }, [job.id, active]);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 10, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {names.map((n) => (
            <button key={n} className={`btn btn-sm ${n === active ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setActive(n)}>
              <IconFile size={13} /> {ARTIFACT_LABELS[n] || n}
            </button>
          ))}
        </div>
        <a className="btn btn-secondary btn-sm" href={api.bundleUrl(job.id)}>
          <IconPackage size={13} /> Download run bundle (.zip)
        </a>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-3)', fontFamily: 'var(--mono)', marginBottom: 6 }}>
        system/data/jobs/{job.id}/{active}
      </div>
      <pre className="code-block" style={{ maxHeight: 'calc(100vh - 380px)', minHeight: 200 }}>{content}</pre>
    </div>
  );
}

// ============ FORMATTED VIEW ============

const tooltipShell = {
  background: '#0F172A', color: '#E2E8F0', border: '1px solid #1E293B', borderRadius: 10,
  boxShadow: '0 16px 40px rgba(15,23,41,0.25)', padding: 14,
};

const TipHead = ({ children }) => (
  <div style={{ fontSize: 10.5, color: '#94A3B8', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600, marginBottom: 8 }}>{children}</div>
);

const TipRow = ({ label, value, total = false }) => {
  const border = total ? { borderTop: '1px solid #1E293B', paddingTop: 6, marginTop: 2 } : {};
  return (
    <>
      <span style={{ color: '#94A3B8', ...border }}>{label}</span>
      <span style={{ fontFamily: 'var(--mono)', fontWeight: total ? 700 : 500, textAlign: 'right', ...border }}>{value}</span>
    </>
  );
};

const TipGrid = ({ children }) => (
  <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 5, fontSize: 12.5 }}>{children}</div>
);

function HoverStat({ label, value, suffix, tooltip, accent = 'var(--text)', align = 'left' }) {
  const [hover, setHover] = useState(false);
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: 'relative', flex: 1, minWidth: 140, padding: '14px 16px', background: '#fff',
        border: '1px solid var(--border)', borderRadius: 12, cursor: 'help', transition: 'border-color .15s, box-shadow .15s',
        ...(hover ? { borderColor: 'var(--border-strong)', boxShadow: 'var(--shadow-md)' } : {}),
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>{label}</div>
        {tooltip && <IconInfo size={11} style={{ color: 'var(--text-3)', opacity: hover ? 1 : 0.5, transition: 'opacity .15s' }} />}
      </div>
      <div style={{ fontSize: 22, fontWeight: 700, marginTop: 4, fontFamily: 'var(--mono)', color: accent }}>
        {value}{suffix && <span style={{ fontSize: 13, color: 'var(--text-3)', fontWeight: 500, marginLeft: 4 }}>{suffix}</span>}
      </div>
      {hover && tooltip && (
        <div style={{ position: 'absolute', top: 'calc(100% + 8px)', ...(align === 'right' ? { right: 0 } : { left: 0 }), zIndex: 30, animation: 'fadeIn .15s ease-out' }}>
          {tooltip}
        </div>
      )}
    </div>
  );
}

function tokenBreakdown(usage) {
  if (!usage) return null;
  const input = usage.prompt_tokens || 0;
  const output = usage.completion_tokens || 0;
  const total = usage.total_tokens || input + output;
  const thinking = usage.thinking_tokens ?? Math.max(0, total - input - output);
  return { input, output, thinking, total };
}

function StatsRow({ job, result, fields }) {
  const values = Object.values(fields);
  const found = values.filter((v) => v !== null && v !== '').length;
  const tokens = tokenBreakdown(result.usage);
  const cost = result.cost || {};
  const isVlm = job.pipeline === 'vlm_direct';
  const modelName = result.model_display_name || job.model_id;
  const stageLabels = {
    prepare: 'Document prep',
    ocr: `OCR · ${result.ocr_engine_display_name || job.ocr_engine_id}`,
    model: `${isVlm ? 'Vision model' : 'LLM'} · ${modelName}`,
    parse: 'Parse output',
  };
  const stages = Object.entries(result.stage_sec || {});

  return (
    <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
      <HoverStat label="Fields extracted" value={found} suffix={`/ ${values.length}`} />
      <HoverStat
        label="Latency" value={(result.latency_sec || 0).toFixed(1)} suffix="s"
        tooltip={(
          <div style={{ ...tooltipShell, width: 280 }}>
            <TipHead>Latency breakdown (measured)</TipHead>
            <TipGrid>
              {stages.map(([k, s]) => <TipRow key={k} label={stageLabels[k] || k} value={`${Number(s).toFixed(2)}s`} />)}
              <TipRow label="Total (incl. client setup)" value={`${(result.latency_sec || 0).toFixed(2)}s`} total />
            </TipGrid>
          </div>
        )}
      />
      <HoverStat
        label="Tokens used" value={tokens ? tokens.total.toLocaleString() : 'n/a'}
        tooltip={tokens && (
          <div style={{ ...tooltipShell, width: 240 }}>
            <TipHead>Tokens used</TipHead>
            <TipGrid>
              <TipRow label="Input" value={tokens.input.toLocaleString()} />
              <TipRow label="Output" value={tokens.output.toLocaleString()} />
              {tokens.thinking > 0 && <TipRow label="Thinking" value={tokens.thinking.toLocaleString()} />}
              <TipRow label="Total" value={tokens.total.toLocaleString()} total />
            </TipGrid>
          </div>
        )}
      />
      <HoverStat
        label="Est. cost" value={formatUsd(cost.total_usd)} accent={cost.total_usd === null || cost.total_usd === undefined ? 'var(--text-3)' : 'var(--success)'} align="right"
        tooltip={(
          <div style={{ ...tooltipShell, width: 260 }}>
            <TipHead>Estimated cost</TipHead>
            <TipGrid>
              <TipRow label="LLM" value={formatUsd(cost.llm_usd)} />
              {!isVlm && <TipRow label="OCR (1 page)" value={formatUsd(cost.ocr_usd)} />}
              <TipRow label="Total" value={formatUsd(cost.total_usd)} total />
            </TipGrid>
            <div style={{ fontSize: 10.5, color: '#64748B', marginTop: 10, lineHeight: 1.5 }}>
              Tokens × price_per_1m in config/models.json{isVlm ? '' : ' + price_per_page in config/ocr_engines.json'}.
            </div>
          </div>
        )}
      />
    </div>
  );
}

function FieldValueRow({ name, value, editing, draft, onDraft, changed }) {
  const isNull = value === null || value === undefined || value === '';
  return (
    <div style={{
      padding: '14px 18px', margin: '0 -16px', borderBottom: '1px solid var(--border)',
      borderLeft: changed ? '4px solid var(--primary)' : '4px solid transparent',
      background: changed ? 'linear-gradient(90deg, rgba(30,64,175,0.06) 0%, transparent 70%)' : 'transparent',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 6 }}>
        <div style={{
          fontFamily: 'var(--mono)', fontSize: 12, fontWeight: 600, color: 'var(--text-2)', letterSpacing: '0.02em',
          whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
        }}>{name}</div>
        {changed && <span className="badge badge-primary"><IconEdit size={10} /> Edited</span>}
      </div>
      {editing ? (
        <textarea className="textarea" rows={Math.min(4, Math.max(1, Math.ceil(String(draft ?? '').length / 70)))}
          style={{ minHeight: 40, fontSize: 15 }} value={draft ?? ''} placeholder="null (not found)"
          onChange={(e) => onDraft(e.target.value)} />
      ) : isNull ? (
        <span style={{ color: 'var(--text-3)', fontStyle: 'italic', fontSize: 14 }}>not found</span>
      ) : (
        <div style={{ fontSize: 17, fontWeight: 600, lineHeight: 1.35, wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}>{String(value)}</div>
      )}
    </div>
  );
}

function FormattedView({ job, onJobUpdate }) {
  const result = job.result;
  const predicted = result.predicted || {};
  const fields = job.edited_fields || predicted;
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(fields);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => { setDraft(fields); }, [job.edited_fields, job.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const normalized = Object.fromEntries(Object.entries(draft).map(([k, v]) => [k, v === '' ? null : v]));
      onJobUpdate(await api.saveJobFields(job.id, normalized));
      setEditing(false);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const canEdit = job.status === 'done';

  return (
    <div>
      <StatsRow job={job} result={result} fields={fields} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 10, flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <a className="btn btn-secondary btn-sm" href={api.exportUrl(job.id, 'json')}><IconDownload size={13} /> JSON</a>
          <a className="btn btn-secondary btn-sm" href={api.exportUrl(job.id, 'csv')}><IconDownload size={13} /> CSV</a>
          <a className="btn btn-secondary btn-sm" href={api.bundleUrl(job.id)}><IconPackage size={13} /> Run bundle</a>
        </div>
        {canEdit && (editing ? (
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn btn-ghost btn-sm" onClick={() => { setDraft(fields); setEditing(false); }}><IconX size={13} /> Cancel</button>
            <button className="btn btn-primary btn-sm" onClick={save} disabled={saving}><IconSave size={13} /> {saving ? 'Saving…' : 'Save edits'}</button>
          </div>
        ) : (
          <button className="btn btn-secondary btn-sm" onClick={() => setEditing(true)}><IconEdit size={13} /> Edit values</button>
        ))}
      </div>
      {error && <div className="alert alert-danger" style={{ marginBottom: 10 }}>{error}</div>}

      <div className="card" style={{ padding: '4px 22px 12px' }}>
        {Object.keys(fields).map((k) => (
          <FieldValueRow
            key={k} name={k} value={fields[k]} editing={editing} draft={draft[k]}
            onDraft={(v) => setDraft({ ...draft, [k]: v })}
            changed={job.edited_fields ? (job.edited_fields[k] ?? null) !== (predicted[k] ?? null) : false}
          />
        ))}
      </div>
    </div>
  );
}

// ============ RESULTS ============

export default function ResultsView({ job, onJobUpdate, actions }) {
  const [view, setView] = useState('formatted');
  const result = job.result;
  const failed = job.status === 'failed';
  const subtitle = useMemo(() => {
    const parts = [PIPELINE_LABEL[job.pipeline], result?.model_display_name || job.model_id];
    if (job.ocr_engine_id) parts.push(result?.ocr_engine_display_name || job.ocr_engine_id);
    if (job.schema_key) parts.push(`schema: ${job.schema_key}`);
    return parts.filter(Boolean).join(' · ');
  }, [job, result]);

  if (!result) return null;

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 18, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h2 className="page-title">Extraction results</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
            {failed
              ? <span className="badge badge-danger"><IconAlert size={11} /> Failed</span>
              : <span className="badge badge-success"><IconCheck size={11} strokeWidth={3} /> Completed successfully</span>}
            {job.edited && <span className="badge badge-primary"><IconEdit size={10} /> Edited</span>}
            <span style={{ fontSize: 13, color: 'var(--text-2)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
              <IconClock size={12} /> {(result.latency_sec || 0).toFixed(1)}s
            </span>
            <span style={{ fontSize: 13, color: 'var(--text-3)' }}>{subtitle}</span>
          </div>
        </div>
        {actions}
      </div>

      {failed && (
        <div className="alert alert-danger" style={{ marginBottom: 16 }}>
          <IconAlert size={15} style={{ flexShrink: 0, marginTop: 1 }} />
          <div style={{ wordBreak: 'break-word' }}><strong>The model call failed.</strong> {result.error}</div>
        </div>
      )}

      <div className="segmented" style={{ marginBottom: 16 }}>
        {[
          { id: 'formatted', label: 'Formatted view', icon: <IconLayout size={13} /> },
          { id: 'json', label: 'JSON view', icon: <IconCode size={13} /> },
          { id: 'artifacts', label: 'Run artifacts', icon: <IconFile size={13} /> },
        ].map((t) => (
          <button key={t.id} className={view === t.id ? 'active' : ''} onClick={() => setView(t.id)}>{t.icon}{t.label}</button>
        ))}
      </div>

      {view === 'formatted' && <FormattedView job={job} onJobUpdate={onJobUpdate} />}
      {view === 'json' && <JsonView job={job} />}
      {view === 'artifacts' && <ArtifactsView job={job} />}
    </div>
  );
}
