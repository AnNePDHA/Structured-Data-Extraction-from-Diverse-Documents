import { useEffect, useRef, useState } from 'react';
import { api } from '../api.js';
import { IconAlert, IconCard, IconDoc, IconFile, IconReceipt, IconScroll, IconShield, IconUpload } from '../components/Icons.jsx';

const SAMPLE_ICONS = { receipt: IconReceipt, card: IconCard, scroll: IconScroll };

const FormatBadge = ({ children }) => (
  <span style={{
    display: 'inline-flex', alignItems: 'center', gap: 4, padding: '4px 10px', borderRadius: 6,
    background: '#fff', border: '1px solid var(--border)', fontSize: 11, fontWeight: 600,
    color: 'var(--text-2)', letterSpacing: '0.04em', fontFamily: 'var(--mono)',
  }}>{children}</span>
);

export default function StepUpload({ onUploaded }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState('');
  const [error, setError] = useState(null);
  const [samples, setSamples] = useState([]);
  const inputRef = useRef(null);

  useEffect(() => { api.samples().then(setSamples).catch(() => setSamples([])); }, []);

  const run = async (promise) => {
    setError(null);
    setUploading(true);
    try {
      const doc = await promise;
      onUploaded(doc);
    } catch (e) {
      setError(e.message);
      setUploading(false);
    }
  };

  const handleFile = (file) => {
    setProgress(0);
    setPhase('Uploading document…');
    run(api.upload(file, (p) => {
      setProgress(p);
      if (p >= 100) setPhase('Rendering first page…');
    }));
  };

  const pickSample = (id) => {
    setProgress(100);
    setPhase('Loading sample document…');
    run(api.useSample(id));
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && !uploading) handleFile(file);
  };

  return (
    <div style={{ maxWidth: 880, margin: '0 auto', padding: '40px 24px' }} className="fade-in">
      <div style={{ textAlign: 'center', marginBottom: 28 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.02em', margin: 0 }}>Upload your document</h1>
        <p style={{ fontSize: 15, color: 'var(--text-2)', marginTop: 10, marginBottom: 0 }}>
          We'll keep the document in view as you define the extraction schema.
        </p>
      </div>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        style={{
          height: '60vh', minHeight: 380, borderRadius: 16,
          border: `2px dashed ${dragging ? 'var(--primary)' : 'var(--border-strong)'}`,
          background: dragging ? 'var(--primary-50)' : '#FAFBFD',
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          cursor: uploading ? 'default' : 'pointer', transition: 'border-color .2s, background .2s',
          padding: 32, textAlign: 'center', position: 'relative', overflow: 'hidden',
        }}
      >
        {!uploading ? (
          <>
            <div style={{
              width: 88, height: 88, borderRadius: '50%', marginBottom: 22, transition: 'background .2s',
              background: dragging ? 'var(--primary)' : 'var(--primary-50)', color: dragging ? '#fff' : 'var(--primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <IconUpload size={40} strokeWidth={1.5} />
            </div>
            <div style={{ fontSize: 20, fontWeight: 600 }}>Drag and drop document here</div>
            <div style={{ fontSize: 14, color: 'var(--text-2)', marginTop: 8 }}>or click to browse from computer</div>
            <div style={{ display: 'flex', gap: 8, marginTop: 28, flexWrap: 'wrap', justifyContent: 'center' }}>
              <FormatBadge>PDF</FormatBadge><FormatBadge>JPG</FormatBadge><FormatBadge>PNG</FormatBadge><FormatBadge>TIFF</FormatBadge>
            </div>

            {error && (
              <div className="alert alert-danger" style={{ marginTop: 20, maxWidth: 460 }} onClick={(e) => e.stopPropagation()}>
                <IconAlert size={15} /> <span>{error}</span>
              </div>
            )}

            {samples.length > 0 && (
              <div style={{ marginTop: 32, paddingTop: 24, borderTop: '1px solid var(--border)', width: '100%', maxWidth: 560 }}>
                <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 10, fontWeight: 500, letterSpacing: '0.04em', textTransform: 'uppercase' }}>
                  Or try a benchmark sample
                </div>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap' }}>
                  {samples.map((s) => {
                    const Icon = SAMPLE_ICONS[s.icon] || IconDoc;
                    return (
                      <button key={s.id} className="btn btn-secondary btn-sm" onClick={(e) => { e.stopPropagation(); pickSample(s.id); }}>
                        <Icon size={14} /> {s.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        ) : (
          <>
            <div style={{
              width: 72, height: 72, borderRadius: '50%', marginBottom: 18, animation: 'pulseRing 1.8s infinite',
              background: 'var(--primary-50)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <IconFile size={32} strokeWidth={1.5} />
            </div>
            <div style={{ fontSize: 18, fontWeight: 600 }}>{phase}</div>
            <div style={{ fontSize: 13, color: 'var(--text-2)', marginTop: 6 }}>
              {Math.round(progress)}% — preparing pages for extraction
            </div>
            <div style={{ width: 280, height: 6, background: 'var(--border)', borderRadius: 999, marginTop: 18, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${progress}%`, background: 'var(--primary)', transition: 'width .1s linear' }} />
            </div>
          </>
        )}

        <input
          ref={inputRef} type="file" accept=".pdf,.jpg,.jpeg,.png,.tiff,.tif" hidden
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f); e.target.value = ''; }}
        />
      </div>

      <div style={{ marginTop: 24, display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-3)', fontSize: 13, justifyContent: 'center' }}>
        <IconShield size={14} />
        <span>Files are stored on this machine; only the first page image is sent to the model provider you choose.</span>
      </div>
    </div>
  );
}
