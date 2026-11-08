import { Fragment } from 'react';
import { IconCheck, IconCpu, IconDoc, IconHistory, IconSparkle } from './Icons.jsx';

export const STEPS = [
  { id: 1, name: 'Upload' },
  { id: 2, name: 'Document Type' },
  { id: 3, name: 'Extraction Pipeline' },
  { id: 4, name: 'Model Configuration' },
  { id: 5, name: 'Results' },
];

const NAV = [
  { id: 'extract', label: 'Extract', icon: <IconSparkle size={14} /> },
  { id: 'history', label: 'History', icon: <IconHistory size={14} /> },
  { id: 'models', label: 'Models', icon: <IconCpu size={14} /> },
  { id: 'prompts', label: 'Prompts', icon: <IconDoc size={14} /> },
];

const StepCircle = ({ status, n }) => {
  const base = {
    width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
    display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all .25s',
  };
  if (status === 'completed') {
    return <div style={{ ...base, background: 'var(--success)', color: '#fff' }}><IconCheck size={16} strokeWidth={3} /></div>;
  }
  if (status === 'current') {
    return (
      <div style={{ ...base, background: 'var(--primary)', color: '#fff', fontSize: 13, fontWeight: 600, boxShadow: '0 0 0 4px rgba(30,64,175,0.14)' }}>
        {n}
      </div>
    );
  }
  return (
    <div style={{ ...base, border: '1.5px solid var(--border-strong)', color: 'var(--text-3)', background: '#fff', fontSize: 13, fontWeight: 500 }}>
      {n}
    </div>
  );
};

export const Stepper = ({ current, completed, onStepClick }) => (
  <div style={{ display: 'flex', alignItems: 'center', width: '100%', maxWidth: 1120, margin: '0 auto' }}>
    {STEPS.map((step, i) => {
      const status = completed.has(step.id) ? 'completed' : current === step.id ? 'current' : 'upcoming';
      const clickable = completed.has(step.id) || step.id === current;
      return (
        <Fragment key={step.id}>
          <button
            onClick={() => clickable && onStepClick(step.id)}
            disabled={!clickable}
            style={{
              display: 'flex', alignItems: 'center', gap: 12, background: 'transparent', border: 0, padding: 0,
              cursor: clickable ? 'pointer' : 'default', color: 'inherit',
            }}
          >
            <StepCircle status={status} n={step.id} />
            <div className="stepper-label" style={{ textAlign: 'left' }}>
              <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600, lineHeight: 1 }}>
                Step {step.id}
              </div>
              <div style={{
                fontSize: 13.5, fontWeight: status === 'current' ? 700 : 500,
                color: status === 'upcoming' ? 'var(--text-3)' : 'var(--text)', marginTop: 3, whiteSpace: 'nowrap',
              }}>
                {step.name}
              </div>
            </div>
          </button>
          {i < STEPS.length - 1 && (
            <div style={{
              flex: 1, height: 1.5, margin: '0 16px', transition: 'background .3s',
              background: completed.has(step.id)
                ? 'var(--success)'
                : status === 'current' ? 'linear-gradient(90deg, var(--primary) 0%, var(--border) 100%)' : 'var(--border)',
            }} />
          )}
        </Fragment>
      );
    })}
  </div>
);

export const Header = ({ page, stepper }) => (
  <header style={{
    position: 'sticky', top: 0, zIndex: 30,
    background: 'rgba(255,255,255,0.92)',
    backdropFilter: 'blur(12px) saturate(140%)', WebkitBackdropFilter: 'blur(12px) saturate(140%)',
    borderBottom: '1px solid var(--border)',
  }}>
    <div style={{
      maxWidth: 1400, margin: '0 auto', padding: '12px 32px',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 24,
    }}>
      <a href="#/extract" style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0, color: 'inherit', textDecoration: 'none' }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: 'linear-gradient(135deg, #1E40AF 0%, #2563EB 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <path d="M9 15 l2 2 l4 -4" />
          </svg>
        </div>
        <div style={{ fontWeight: 700, fontSize: 16, letterSpacing: '-0.01em' }}>DocuExtract</div>
      </a>
      <nav style={{ display: 'flex', gap: 4 }}>
        {NAV.map((n) => (
          <a key={n.id} href={`#/${n.id}`} className={`nav-link${page === n.id ? ' active' : ''}`}>
            {n.icon}{n.label}
          </a>
        ))}
      </nav>
    </div>
    {stepper && (
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '4px 32px 14px' }}>{stepper}</div>
    )}
  </header>
);

export const Footer = () => (
  <footer style={{
    maxWidth: 1400, margin: '0 auto', padding: '20px 32px 36px',
    color: 'var(--text-3)', fontSize: 12,
    display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap',
  }}>
    <div>Master thesis system · VLM Direct vs. OCR-LLM · {new Date().getFullYear()}</div>
    <div style={{ display: 'flex', gap: 16 }}>
      <a href="/docs" target="_blank" rel="noreferrer" style={{ color: 'inherit', textDecoration: 'none' }}>API reference</a>
      <a href="#/models" style={{ color: 'inherit', textDecoration: 'none' }}>Models</a>
      <a href="#/prompts" style={{ color: 'inherit', textDecoration: 'none' }}>Prompts</a>
    </div>
  </footer>
);

export const PageHeading = ({ title, sub, actions }) => (
  <div style={{ marginBottom: 20, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
    <div>
      <h2 className="page-title">{title}</h2>
      {sub && <p className="page-sub">{sub}</p>}
    </div>
    {actions && <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>{actions}</div>}
  </div>
);
