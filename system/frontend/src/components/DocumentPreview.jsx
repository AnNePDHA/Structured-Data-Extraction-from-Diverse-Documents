import { useState } from 'react';
import { formatBytes } from '../utils.js';
import { IconCheck, IconFile, IconTrash, IconZoomIn, IconZoomOut } from './Icons.jsx';

const PreviewToolbar = ({ zoom, setZoom, doc, onRemove }) => (
  <div style={{
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '10px 14px', borderBottom: '1px solid var(--border)',
    background: '#FAFBFD', borderTopLeftRadius: 12, borderTopRightRadius: 12, gap: 12,
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0, flex: 1 }}>
      <div style={{
        width: 34, height: 34, borderRadius: 7, background: 'var(--primary-50)', flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)',
      }}>
        <IconFile size={15} />
      </div>
      <div style={{ minWidth: 0, flex: 1 }}>
        <div title={doc.filename} style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {doc.filename}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 5, marginTop: 1, flexWrap: 'wrap' }}>
          {doc.size ? <><span>{formatBytes(doc.size)}</span><span>·</span></> : null}
          <span>Page 1 / {doc.pages || 1}</span>
          {doc.pages > 1 && <><span>·</span><span>first page used</span></>}
          <span>·</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3, color: 'var(--success)', fontWeight: 500 }}>
            <IconCheck size={10} strokeWidth={3} /> Uploaded
          </span>
        </div>
      </div>
    </div>
    <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      <button className="btn btn-ghost btn-icon" onClick={() => setZoom(Math.max(0.5, zoom - 0.1))} aria-label="Zoom out">
        <IconZoomOut size={15} />
      </button>
      <div style={{ fontSize: 12, fontVariantNumeric: 'tabular-nums', color: 'var(--text-2)', minWidth: 38, textAlign: 'center', fontWeight: 500 }}>
        {Math.round(zoom * 100)}%
      </div>
      <button className="btn btn-ghost btn-icon" onClick={() => setZoom(Math.min(2, zoom + 0.1))} aria-label="Zoom in">
        <IconZoomIn size={15} />
      </button>
      {onRemove && (
        <>
          <div style={{ width: 1, height: 20, background: 'var(--border)', margin: '0 6px' }} />
          <button className="btn btn-ghost btn-icon" onClick={onRemove} aria-label="Remove file" title="Remove and upload another" style={{ color: 'var(--text-2)' }}>
            <IconTrash size={14} />
          </button>
        </>
      )}
    </div>
  </div>
);

// stickyTop matches the header height: taller on the Extract page because of the stepper row
export default function DocumentPreview({ doc, imageUrl, scanning = false, onRemove, stickyTop = 132 }) {
  const [zoom, setZoom] = useState(0.9);
  return (
    <div className="card" style={{
      position: 'sticky', top: stickyTop, overflow: 'hidden',
      display: 'flex', flexDirection: 'column', maxHeight: `calc(100vh - ${stickyTop + 20}px)`,
    }}>
      <PreviewToolbar zoom={zoom} setZoom={setZoom} doc={doc} onRemove={onRemove} />
      <div style={{
        flex: 1, minHeight: 0, overflow: 'auto',
        background: 'linear-gradient(180deg, #F1F4F9 0%, #E6EBF2 100%)', padding: 20,
      }}>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <div style={{
            width: `${zoom * 100}%`, transition: 'width .15s ease', position: 'relative',
            background: '#fff', borderRadius: 4, overflow: 'hidden',
            boxShadow: '0 6px 20px rgba(15,23,41,0.10), 0 2px 4px rgba(15,23,41,0.05)',
          }}>
            <img src={imageUrl || doc.preview_url} alt={doc.filename} style={{ display: 'block', width: '100%' }} />
            {scanning && (
              <>
                <div style={{
                  position: 'absolute', left: 0, right: 0, height: 2,
                  background: 'linear-gradient(90deg, transparent, var(--primary), transparent)',
                  boxShadow: '0 0 12px rgba(30,64,175,0.6)',
                  animation: 'drawScan 2.2s ease-in-out infinite', pointerEvents: 'none',
                }} />
                <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, rgba(30,64,175,0.04), transparent 40%)', pointerEvents: 'none' }} />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
