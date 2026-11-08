import { useEffect, useState } from 'react';
import { IconBrain, IconCheck, IconCode, IconEye, IconFile, IconTarget } from '../components/Icons.jsx';

export const stageList = (pipeline, modelName, ocrName) => (pipeline === 'vlm_direct'
  ? [
    { key: 'prepare', label: 'Preparing document page', icon: <IconFile size={14} /> },
    { key: 'model', label: `Running ${modelName || 'vision model'}`, icon: <IconEye size={14} /> },
    { key: 'parse', label: 'Parsing structured output', icon: <IconCode size={14} /> },
  ]
  : [
    { key: 'prepare', label: 'Preparing document page', icon: <IconFile size={14} /> },
    { key: 'ocr', label: `Running OCR (${ocrName || 'engine'})`, icon: <IconTarget size={14} /> },
    { key: 'model', label: `Running ${modelName || 'LLM'}`, icon: <IconBrain size={14} /> },
    { key: 'parse', label: 'Parsing structured output', icon: <IconCode size={14} /> },
  ]);

export default function ProcessingPanel({ pipeline, stage, modelName, ocrName, startedAt }) {
  const stages = stageList(pipeline, modelName, ocrName);
  const current = Math.max(0, stages.findIndex((s) => s.key === stage));
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 200);
    return () => clearInterval(t);
  }, []);
  const elapsed = startedAt ? (now - startedAt) / 1000 : 0;

  return (
    <div style={{ padding: '4px 0' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18 }}>
        <div style={{
          width: 32, height: 32, borderRadius: '50%', border: '3px solid var(--primary-50)',
          borderTopColor: 'var(--primary)', animation: 'spin 0.9s linear infinite',
        }} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 600 }}>Extracting structured data…</div>
          <div style={{ fontSize: 12.5, color: 'var(--text-2)' }}>
            {stage ? 'Live progress reported by the backend job.' : 'Job queued, waiting for a worker…'}
          </div>
        </div>
        <div className="mono" style={{ fontSize: 13, color: 'var(--text-2)', fontVariantNumeric: 'tabular-nums' }}>{elapsed.toFixed(1)}s</div>
      </div>

      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        {stages.map((s, i) => {
          const done = i < current;
          const active = i === current;
          return (
            <div key={s.key} style={{
              display: 'flex', alignItems: 'center', gap: 12, padding: '8px 0',
              opacity: done || active ? 1 : 0.45, transition: 'opacity .3s',
            }}>
              <div style={{
                width: 22, height: 22, borderRadius: '50%', flexShrink: 0, color: '#fff',
                background: done ? 'var(--success)' : active ? 'var(--primary)' : '#E4E8EE',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {done ? <IconCheck size={12} strokeWidth={3} />
                  : active ? <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#fff', animation: 'pulse 1s infinite' }} />
                    : <span style={{ fontSize: 10, fontWeight: 700 }}>{i + 1}</span>}
              </div>
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: 'var(--text-2)', display: 'inline-flex' }}>{s.icon}</span>
                <span style={{ fontSize: 13.5, fontWeight: active ? 600 : 500 }}>{s.label}</span>
              </div>
              {active && (
                <div style={{ width: 140, height: 4, background: 'var(--primary-50)', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: '40%', background: 'var(--primary)', animation: 'indeterminate 1.2s ease-in-out infinite' }} />
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div>
        {[0, 1, 2].map((i) => (
          <div key={i} style={{ display: 'flex', gap: 12, padding: '10px 0', alignItems: 'center' }}>
            <div className="skeleton" style={{ width: 120, height: 12 }} />
            <div className="skeleton" style={{ flex: 1, height: 14 }} />
            <div className="skeleton" style={{ width: 60, height: 10 }} />
          </div>
        ))}
      </div>
    </div>
  );
}
