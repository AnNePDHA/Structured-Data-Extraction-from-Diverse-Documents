import { useEffect, useRef, useState } from 'react';
import { fieldKey, useClickOutside } from '../utils.js';
import { DropdownItem, DropdownPanel, triggerStyle } from '../components/Dropdown.jsx';
import {
  IconCard, IconCheck, IconChevronDown, IconDoc, IconEdit, IconPlus, IconReceipt, IconSave, IconScroll, IconSparkle, IconTrash,
} from '../components/Icons.jsx';

const SCHEMA_ICONS = { invoice: IconReceipt, id_card: IconCard, contract: IconScroll };
const schemaIcon = (key, builtin) => {
  const Icon = SCHEMA_ICONS[key] || (builtin ? IconDoc : IconSave);
  return <Icon size={14} />;
};

function SchemaDropdown({ current, schemas, onSelect }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useClickOutside(ref, () => setOpen(false));
  const presets = schemas.filter((s) => s.builtin);
  const saved = schemas.filter((s) => !s.builtin);
  const pick = (key) => { onSelect(key); setOpen(false); };

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button onClick={() => setOpen((o) => !o)} style={triggerStyle(open, 42)}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
          <span style={{ color: 'var(--text-2)', display: 'inline-flex' }}>
            {current.key ? schemaIcon(current.key, current.builtin) : <IconSparkle size={14} />}
          </span>
          <span style={{ fontSize: 14, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {current.name}
          </span>
          {!current.key && <span className="badge badge-primary">Custom</span>}
          {current.key && !current.builtin && <span className="badge badge-success">Saved</span>}
          {current.key && current.builtin && <span className="badge">Preset · config/fields/{current.key}.json</span>}
          {current.dirty && <span className="badge badge-warning">Modified</span>}
        </span>
        <IconChevronDown size={15} style={{ color: 'var(--text-3)', transform: open ? 'rotate(180deg)' : 'none', transition: 'transform .15s' }} />
      </button>

      {open && (
        <DropdownPanel maxHeight={340}>
          <div className="group-label">Custom</div>
          <DropdownItem icon={<IconDoc size={14} />} active={!current.key} label="Default" hint="Editable schema" onClick={() => pick(null)} />
          {presets.length > 0 && <div className="group-label">Presets</div>}
          {presets.map((s) => (
            <DropdownItem key={s.key} icon={schemaIcon(s.key, true)} active={current.key === s.key}
              label={s.name} hint={`${s.field_count} fields`} onClick={() => pick(s.key)} />
          ))}
          {saved.length > 0 && <div className="group-label">Your saved schemas</div>}
          {saved.map((s) => (
            <DropdownItem key={s.key} icon={<IconSave size={14} />} active={current.key === s.key}
              label={s.name} hint={`${s.field_count} fields`} onClick={() => pick(s.key)} />
          ))}
        </DropdownPanel>
      )}
    </div>
  );
}

function FieldEditor({ initial, onSubmit, onCancel, submitLabel, dashed }) {
  const [name, setName] = useState(initial?.name || '');
  const [desc, setDesc] = useState(initial?.description || '');
  const [format, setFormat] = useState(initial?.format || '');
  const nameRef = useRef(null);
  useEffect(() => { nameRef.current?.focus(); }, []);

  const submit = () => {
    if (!fieldKey(name)) return;
    onSubmit({ name: fieldKey(name), description: desc.trim(), format: format.trim() });
  };

  return (
    <div className="slide-in" style={{
      padding: 14, background: '#FAFBFD', borderRadius: 8, marginBottom: 8,
      border: `1px ${dashed ? 'dashed' : 'solid'} var(--primary)`,
      boxShadow: dashed ? 'none' : '0 0 0 3px rgba(30,64,175,0.10)',
    }}>
      <div style={{ marginBottom: 10 }}>
        <label className="label">Field name</label>
        <input ref={nameRef} className="input mono" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. tax_code"
          onKeyDown={(e) => { if (e.key === 'Enter') submit(); if (e.key === 'Escape') onCancel(); }} />
      </div>
      <div style={{ marginBottom: 10 }}>
        <label className="label">Description</label>
        <textarea className="textarea" rows={2} value={desc} onChange={(e) => setDesc(e.target.value)}
          placeholder="e.g. Seller tax identification number containing 10–13 digits" />
      </div>
      <div>
        <label className="label">Format <span style={{ color: 'var(--text-3)', fontWeight: 400 }}>(optional)</span></label>
        <input className="input" value={format} onChange={(e) => setFormat(e.target.value)}
          placeholder="e.g. keep the original format as printed" />
        <div className="helper">Description and format are rendered into the prompt as <span className="mono">{'{{fields_schema}}'}</span>.</div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6, marginTop: 12 }}>
        <button className="btn btn-ghost btn-sm" onClick={onCancel}>Cancel</button>
        <button className="btn btn-primary btn-sm" disabled={!fieldKey(name)} onClick={submit}>
          {dashed ? <IconPlus size={13} /> : <IconCheck size={13} strokeWidth={2.5} />} {submitLabel}
        </button>
      </div>
    </div>
  );
}

function FieldRow({ field, onEdit, onDelete }) {
  return (
    <div
      style={{
        padding: '12px 14px', background: '#fff', border: '1px solid var(--border)', borderRadius: 8, marginBottom: 8,
        display: 'flex', alignItems: 'flex-start', gap: 12, transition: 'border-color .15s',
      }}
      onMouseOver={(e) => { e.currentTarget.style.borderColor = 'var(--border-strong)'; }}
      onMouseOut={(e) => { e.currentTarget.style.borderColor = 'var(--border)'; }}
    >
      <div style={{
        width: 26, height: 26, borderRadius: 6, background: 'var(--primary-50)', color: 'var(--primary)', flexShrink: 0, marginTop: 1,
        display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'var(--mono)', fontWeight: 600, fontSize: 12,
      }}>{'{ }'}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 13.5, fontWeight: 600, marginBottom: 2 }}>{field.name}</div>
        <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.5, wordBreak: 'break-word' }}>
          {field.description || <span style={{ color: 'var(--text-3)', fontStyle: 'italic' }}>No description — add one to improve extraction accuracy.</span>}
        </div>
        {field.format && (
          <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 4 }}>
            <span style={{ fontWeight: 600 }}>Format:</span> {field.format}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', gap: 2, flexShrink: 0 }}>
        <button className="btn btn-ghost btn-icon" onClick={onEdit} title="Edit field" style={{ width: 32, height: 32 }}>
          <IconEdit size={14} />
        </button>
        <button className="btn btn-ghost btn-icon" onClick={onDelete} title="Delete field" style={{ width: 32, height: 32, color: 'var(--text-2)' }}>
          <IconTrash size={13} />
        </button>
      </div>
    </div>
  );
}

export default function SchemaFieldsPanel({ current, schemas, fields, onSchemaSelect, onRename, setFields }) {
  const [renaming, setRenaming] = useState(false);
  const [renameVal, setRenameVal] = useState(current.name);
  const [adding, setAdding] = useState(false);
  const [editingIdx, setEditingIdx] = useState(-1);
  const [dupError, setDupError] = useState(null);

  useEffect(() => { setEditingIdx(-1); setAdding(false); setDupError(null); }, [current.key]);

  const canRename = !current.builtin;

  const commitRename = () => {
    if (renameVal.trim()) onRename(renameVal.trim());
    setRenaming(false);
  };

  const upsert = (idx, f) => {
    if (fields.some((x, i) => x.name === f.name && i !== idx)) {
      setDupError(`Field "${f.name}" already exists.`);
      return;
    }
    setDupError(null);
    if (idx < 0) { setFields([...fields, f]); setAdding(false); } else {
      const copy = [...fields]; copy[idx] = f; setFields(copy); setEditingIdx(-1);
    }
  };

  return (
    <>
      <div className="card" style={{ padding: 20, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', marginBottom: 12, gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: 220 }}>
            <div className="section-title">Document schema</div>
            <div className="section-sub">Pick a preset from config/fields, or build your own custom schema.</div>
          </div>
          {canRename && !renaming && (
            <button className="btn btn-ghost btn-sm" onClick={() => { setRenameVal(current.name); setRenaming(true); }}>
              <IconEdit size={13} /> Rename
            </button>
          )}
        </div>
        {renaming ? (
          <div style={{ display: 'flex', gap: 8 }}>
            <input className="input" value={renameVal} onChange={(e) => setRenameVal(e.target.value)} placeholder="Schema name" autoFocus
              onKeyDown={(e) => { if (e.key === 'Enter') commitRename(); if (e.key === 'Escape') setRenaming(false); }} />
            <button className="btn btn-ghost" onClick={() => setRenaming(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={commitRename}>Save name</button>
          </div>
        ) : (
          <SchemaDropdown current={current} schemas={schemas} onSelect={onSchemaSelect} />
        )}
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, gap: 12 }}>
          <div>
            <div className="section-title">Fields to extract</div>
            <div className="section-sub">
              {fields.length === 0
                ? 'Add at least one field — each becomes a key in the output JSON.'
                : `${fields.length} field${fields.length !== 1 ? 's' : ''} configured.`}
            </div>
          </div>
          {!adding && (
            <button className="btn btn-secondary btn-sm" onClick={() => { setAdding(true); setEditingIdx(-1); }}>
              <IconPlus size={13} strokeWidth={2.5} /> Add field
            </button>
          )}
        </div>

        {dupError && <div className="alert alert-danger" style={{ marginBottom: 10 }}>{dupError}</div>}

        {fields.map((f, i) => (editingIdx === i ? (
          <FieldEditor key={`edit-${i}`} initial={f} submitLabel="Save" onSubmit={(nf) => upsert(i, nf)} onCancel={() => setEditingIdx(-1)} />
        ) : (
          <FieldRow key={f.name + i} field={f}
            onEdit={() => { setEditingIdx(i); setAdding(false); }}
            onDelete={() => setFields(fields.filter((_, j) => j !== i))} />
        )))}

        {adding && <FieldEditor dashed submitLabel="Add field" onSubmit={(f) => upsert(-1, f)} onCancel={() => setAdding(false)} />}

        {!adding && fields.length === 0 && (
          <button
            onClick={() => setAdding(true)}
            style={{
              width: '100%', padding: '20px 14px', border: '1px dashed var(--border-strong)', background: '#FAFBFD',
              borderRadius: 8, color: 'var(--text-2)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontSize: 13,
            }}
            onMouseOver={(e) => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.background = 'var(--primary-50)'; e.currentTarget.style.color = 'var(--primary)'; }}
            onMouseOut={(e) => { e.currentTarget.style.borderColor = 'var(--border-strong)'; e.currentTarget.style.background = '#FAFBFD'; e.currentTarget.style.color = 'var(--text-2)'; }}
          >
            <IconPlus size={14} strokeWidth={2.2} /> Add your first field
          </button>
        )}
      </div>
    </>
  );
}
