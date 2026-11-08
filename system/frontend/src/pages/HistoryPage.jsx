import { useEffect, useState } from 'react';
import { api } from '../api.js';
import { formatTime, formatUsd, navigate, PIPELINE_LABEL } from '../utils.js';
import { Header, PageHeading } from '../components/Layout.jsx';
import DocumentPreview from '../components/DocumentPreview.jsx';
import ResultsView from '../components/ResultsView.jsx';
import { IconAlert, IconChevronRight, IconRefresh, IconTrash } from '../components/Icons.jsx';

const PAGE = 20;

const StatusBadge = ({ status }) => {
  const tone = { done: 'success', failed: 'danger', running: 'primary', queued: 'primary' }[status];
  return <span className={`badge badge-${tone}`}>{status}</span>;
};

function JobList() {
  const [data, setData] = useState({ items: [], total: 0 });
  const [offset, setOffset] = useState(0);
  const [error, setError] = useState(null);

  const load = () => api.jobs(PAGE, offset).then(setData).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [offset]); // eslint-disable-line react-hooks/exhaustive-deps

  const remove = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Delete this run and its job folder?')) return;
    try { await api.deleteJob(id); load(); } catch (err) { setError(err.message); }
  };

  return (
    <>
      <PageHeading
        title="Extraction history"
        sub="Every run is stored in system/data/jobs/<id>/ with its prompt, OCR text, raw response and result."
        actions={<button className="btn btn-secondary btn-sm" onClick={load}><IconRefresh size={13} /> Refresh</button>}
      />
      {error && <div className="alert alert-danger" style={{ marginBottom: 12 }}><IconAlert size={15} /> {error}</div>}
      <div className="card" style={{ overflow: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th>Time</th><th>Document</th><th>Schema</th><th>Pipeline</th><th>Model</th>
              <th>Status</th><th style={{ textAlign: 'right' }}>Latency</th><th style={{ textAlign: 'right' }}>Cost</th><th />
            </tr>
          </thead>
          <tbody>
            {data.items.length === 0 && (
              <tr><td colSpan={9} style={{ textAlign: 'center', color: 'var(--text-3)', padding: 40 }}>
                No runs yet. <a href="#/extract">Extract a document</a> to get started.
              </td></tr>
            )}
            {data.items.map((j) => (
              <tr key={j.id} className="clickable" onClick={() => navigate(`/history/${j.id}`)}>
                <td style={{ whiteSpace: 'nowrap', color: 'var(--text-2)' }}>{formatTime(j.created_at)}</td>
                <td style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 500 }} title={j.filename}>
                  {j.filename}
                </td>
                <td className="mono" style={{ fontSize: 12 }}>{j.schema_key || <span style={{ color: 'var(--text-3)' }}>custom</span>}</td>
                <td style={{ whiteSpace: 'nowrap' }}>{PIPELINE_LABEL[j.pipeline]}</td>
                <td className="mono" style={{ fontSize: 12 }}>
                  {j.model_id}{j.ocr_engine_id && <div style={{ color: 'var(--text-3)' }}>{j.ocr_engine_id}</div>}
                </td>
                <td><StatusBadge status={j.status} />{j.edited && <span className="badge badge-primary" style={{ marginLeft: 4 }}>edited</span>}</td>
                <td className="mono" style={{ textAlign: 'right' }}>{j.latency_sec != null ? `${j.latency_sec.toFixed(1)}s` : '—'}</td>
                <td className="mono" style={{ textAlign: 'right' }}>{j.status === 'done' ? formatUsd(j.cost_usd, 5) : '—'}</td>
                <td style={{ whiteSpace: 'nowrap', textAlign: 'right' }}>
                  <button className="btn btn-ghost btn-icon" style={{ width: 30, height: 30 }} title="Delete run" onClick={(e) => remove(e, j.id)}>
                    <IconTrash size={13} />
                  </button>
                  <IconChevronRight size={14} style={{ color: 'var(--text-3)', verticalAlign: 'middle' }} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data.total > PAGE && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12, fontSize: 13, color: 'var(--text-2)' }}>
          <span>{offset + 1}–{Math.min(offset + PAGE, data.total)} of {data.total}</span>
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn btn-secondary btn-sm" disabled={offset === 0} onClick={() => setOffset(offset - PAGE)}>Previous</button>
            <button className="btn btn-secondary btn-sm" disabled={offset + PAGE >= data.total} onClick={() => setOffset(offset + PAGE)}>Next</button>
          </div>
        </div>
      )}
    </>
  );
}

function JobDetail({ id }) {
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let stopped = false;
    const load = async () => {
      try {
        const j = await api.job(id);
        if (stopped) return;
        setJob(j);
        if (j.status === 'queued' || j.status === 'running') setTimeout(load, 1000);
      } catch (e) {
        if (!stopped) setError(e.message);
      }
    };
    load();
    return () => { stopped = true; };
  }, [id]);

  const remove = async () => {
    if (!window.confirm('Delete this run and its job folder?')) return;
    await api.deleteJob(id);
    navigate('/history');
  };

  if (error) return <div className="alert alert-danger"><IconAlert size={15} /> {error}</div>;
  if (!job) return <div style={{ color: 'var(--text-3)' }}>Loading…</div>;

  const doc = { filename: job.filename, pages: 1, preview_url: job.preview_url };
  return (
    <div className="extract-grid">
      <div><DocumentPreview doc={doc} stickyTop={82} /></div>
      <div style={{ minWidth: 0 }}>
        {job.result ? (
          <ResultsView
            job={job}
            onJobUpdate={setJob}
            actions={(
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn btn-danger" onClick={remove}><IconTrash size={14} /> Delete</button>
                <a className="btn btn-secondary" href="#/history">Back to history</a>
              </div>
            )}
          />
        ) : (
          <div className="card" style={{ padding: 24 }}>Job is {job.status}{job.stage ? ` (${job.stage})` : ''}…</div>
        )}
      </div>
    </div>
  );
}

export default function HistoryPage({ jobId }) {
  return (
    <>
      <Header page="history" />
      <main style={{ maxWidth: 1400, margin: '0 auto', padding: '28px 24px 48px' }}>
        {jobId ? <JobDetail id={jobId} /> : <JobList />}
      </main>
    </>
  );
}
