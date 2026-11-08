import { useMemo, useRef, useState } from 'react';
import { useClickOutside } from '../utils.js';
import { IconCheck, IconChevronDown } from './Icons.jsx';

export const DropdownItem = ({ icon, label, hint, active, onClick, disabled }) => (
  <button
    onClick={disabled ? undefined : onClick}
    disabled={disabled}
    style={{
      width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '9px 10px',
      background: active ? 'var(--primary-50)' : 'transparent', border: 0, borderRadius: 6,
      color: active ? 'var(--primary)' : 'var(--text)', transition: 'background .1s', textAlign: 'left',
      opacity: disabled ? 0.5 : 1, cursor: disabled ? 'not-allowed' : 'pointer',
    }}
    onMouseOver={(e) => { if (!active && !disabled) e.currentTarget.style.background = '#F1F4F9'; }}
    onMouseOut={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; }}
  >
    <span style={{ color: active ? 'var(--primary)' : 'var(--text-3)', display: 'inline-flex' }}>{icon}</span>
    <span style={{ flex: 1, fontSize: 13.5, fontWeight: active ? 600 : 500 }}>{label}</span>
    <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{hint}</span>
    {active && <IconCheck size={13} strokeWidth={2.5} />}
  </button>
);

export const VendorBadge = ({ vendor }) => (
  <div style={{
    width: 24, height: 24, borderRadius: 5, background: '#F1F4F9', color: 'var(--text-2)', flexShrink: 0,
    display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700,
  }}>
    {(vendor || '?')[0].toUpperCase()}
  </div>
);

export const DropdownPanel = ({ children, maxHeight = 360 }) => (
  <div className="fade-in" style={{
    position: 'absolute', top: 'calc(100% + 6px)', left: 0, right: 0,
    background: '#fff', border: '1px solid var(--border)', borderRadius: 8,
    boxShadow: 'var(--shadow-lg)', zIndex: 20, padding: 6, maxHeight, overflow: 'auto',
  }}>
    {children}
  </div>
);

export const triggerStyle = (open, height) => ({
  width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10,
  height, padding: '0 14px', background: '#fff', border: '1px solid var(--border-strong)',
  borderRadius: 6, color: 'var(--text)', transition: 'border-color .15s, box-shadow .15s',
  ...(open ? { borderColor: 'var(--primary)', boxShadow: '0 0 0 3px rgba(30,64,175,0.12)' } : {}),
});

// options: [{ id, vendor, title, subtitle, tag, tagTone, disabled }]
export function ModelDropdown({ label, hint, options, value, onChange, placeholder = 'Select a model…' }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useClickOutside(ref, () => setOpen(false));
  const selected = options.find((o) => o.id === value);

  const groups = useMemo(() => {
    const m = new Map();
    options.forEach((o) => {
      const v = o.vendor || 'Other';
      if (!m.has(v)) m.set(v, []);
      m.get(v).push(o);
    });
    return [...m.entries()];
  }, [options]);

  return (
    <div>
      <label className="label">{label}</label>
      {hint && <div className="helper" style={{ marginTop: -4, marginBottom: 6 }}>{hint}</div>}
      <div ref={ref} style={{ position: 'relative' }}>
        <button onClick={() => setOpen((o) => !o)} style={triggerStyle(open, 52)}>
          {selected ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
              <VendorBadge vendor={selected.vendor} />
              <span style={{ minWidth: 0, textAlign: 'left' }}>
                <span style={{ fontSize: 14, fontWeight: 600, display: 'block' }}>{selected.title}</span>
                <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{selected.vendor} · {selected.subtitle}</span>
              </span>
            </span>
          ) : (
            <span style={{ color: 'var(--text-3)' }}>{placeholder}</span>
          )}
          <IconChevronDown size={15} style={{ color: 'var(--text-3)', transform: open ? 'rotate(180deg)' : 'none', transition: 'transform .15s' }} />
        </button>

        {open && (
          <DropdownPanel>
            {groups.length === 0 && <div style={{ padding: 12, fontSize: 13, color: 'var(--text-3)' }}>No options configured.</div>}
            {groups.map(([vendor, items]) => (
              <div key={vendor}>
                <div className="group-label">{vendor}</div>
                {items.map((o) => (
                  <button
                    key={o.id}
                    disabled={o.disabled}
                    onClick={() => { onChange(o.id); setOpen(false); }}
                    title={o.disabledReason}
                    style={{
                      width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: 10,
                      background: o.id === value ? 'var(--primary-50)' : 'transparent', border: 0, borderRadius: 6,
                      textAlign: 'left', transition: 'background .1s',
                      opacity: o.disabled ? 0.5 : 1, cursor: o.disabled ? 'not-allowed' : 'pointer',
                    }}
                    onMouseOver={(e) => { if (o.id !== value && !o.disabled) e.currentTarget.style.background = '#F1F4F9'; }}
                    onMouseOut={(e) => { if (o.id !== value) e.currentTarget.style.background = 'transparent'; }}
                  >
                    <VendorBadge vendor={o.vendor} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--text)' }}>{o.title}</div>
                      <div style={{ fontSize: 11, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                        <span>{o.subtitle}</span>
                        {o.tag && <span className={`badge ${o.tagTone ? `badge-${o.tagTone}` : ''}`} style={{ padding: '1px 6px', fontSize: 10 }}>{o.tag}</span>}
                      </div>
                    </div>
                    {o.id === value && <IconCheck size={14} strokeWidth={2.5} style={{ color: 'var(--primary)' }} />}
                  </button>
                ))}
              </div>
            ))}
          </DropdownPanel>
        )}
      </div>
    </div>
  );
}
