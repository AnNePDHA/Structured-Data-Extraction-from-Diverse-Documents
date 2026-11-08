import { useCallback, useEffect, useState } from 'react';
import { api } from '../api.js';
import { configToFields, fieldsToConfig, PIPELINE_LABEL, slugify } from '../utils.js';
import { Header, Stepper } from '../components/Layout.jsx';
import DocumentPreview from '../components/DocumentPreview.jsx';
import ResultsView from '../components/ResultsView.jsx';
import { IconAlert, IconBolt, IconCheck, IconChevronRight, IconInfo, IconRefresh, IconSave } from '../components/Icons.jsx';
import StepUpload from '../extract/StepUpload.jsx';
import SchemaFieldsPanel from '../extract/SchemaFieldsPanel.jsx';
import { ModelSection, PipelineSection } from '../extract/PipelineModel.jsx';
import ProcessingPanel from '../extract/ProcessingPanel.jsx';

const DEFAULT_SCHEMA = { key: null, name: 'Default', builtin: false, dirty: false };

const pickDefault = (list, preferred) => {
  const usable = list.filter((x) => x.available);
  return (usable.find((x) => x.id === preferred) || usable[0])?.id || null;
};

export default function ExtractPage({ active }) {
  const [step, setStep] = useState(1);
  const [completed, setCompleted] = useState(new Set());
  const [doc, setDoc] = useState(null);

  const [schemas, setSchemas] = useState([]);
  const [schema, setSchema] = useState(DEFAULT_SCHEMA);
  const [fields, setFieldsRaw] = useState([]);
  const [toast, setToast] = useState(null);

  const [catalog, setCatalog] = useState({ pipelines: [], models: [], ocrEngines: [], prompts: [] });
  const [pipeline, setPipeline] = useState(null);
  const [config, setConfig] = useState({ model: null, ocr: null, prompt: null });

  const [jobId, setJobId] = useState(null);
  const [job, setJob] = useState(null);
  const [startedAt, setStartedAt] = useState(null);
  const [error, setError] = useState(null);

  const refreshSchemas = useCallback(() => api.schemas().then(setSchemas).catch(() => {}), []);

  // Config files may be edited on the Models/Prompts pages, so reload whenever this page is shown
  useEffect(() => {
    if (!active) return;
    refreshSchemas();
    Promise.all([api.pipelines(), api.models(), api.ocrEngines(), api.prompts()])
      .then(([pipelines, models, ocrEngines, prompts]) => setCatalog({ pipelines, models, ocrEngines, prompts }))
      .catch((e) => setError(`Cannot reach the backend: ${e.message}`));
  }, [active, refreshSchemas]);

  const markCompleted = (n) => setCompleted((prev) => new Set([...prev, n]));
  const uncomplete = (...ns) => setCompleted((prev) => {
    const next = new Set(prev);
    ns.forEach((n) => next.delete(n));
    return next;
  });

  // Editing the schema after step 2 sends the user back to step 2, as in the prototype
  const demote = () => {
    if (step > 2) {
      setStep(2);
      uncomplete(2, 3, 4, 5);
      setJobId(null);
      setJob(null);
    }
  };

  const setFields = (next) => {
    setFieldsRaw(next);
    setSchema((s) => (s.key ? { ...s, dirty: true } : s));
    demote();
  };

  const selectSchema = async (key) => {
    demote();
    setError(null);
    if (!key) {
      setSchema(DEFAULT_SCHEMA);
      setFieldsRaw([]);
      return;
    }
    try {
      const s = await api.schema(key);
      setSchema({ key: s.key, name: s.name, builtin: s.builtin, dirty: false });
      setFieldsRaw(configToFields(s.fields));
    } catch (e) {
      setError(e.message);
    }
  };

  const reset = () => {
    setDoc(null);
    setSchema(DEFAULT_SCHEMA);
    setFieldsRaw([]);
    setPipeline(null);
    setJobId(null);
    setJob(null);
    setError(null);
    setCompleted(new Set());
    setStep(1);
  };

  const handleUploaded = (d) => {
    setDoc(d);
    setPipeline(null);
    setJob(null);
    setJobId(null);
    markCompleted(1);
    setStep(2);
    if (d.suggested_schema) selectSchema(d.suggested_schema);
    else { setSchema(DEFAULT_SCHEMA); setFieldsRaw([]); }
  };

  const showToast = (t) => {
    setToast(t);
    setTimeout(() => setToast(null), 3000);
  };

  const uniqueKey = (name) => {
    const base = slugify(name) || 'my_schema';
    const taken = new Set(schemas.map((s) => s.key));
    let key = base;
    for (let i = 2; taken.has(key); i += 1) key = `${base}_${i}`;
    return key;
  };

  const saveSchema = async () => {
    setError(null);
    try {
      if (schema.key && !schema.builtin) {
        await api.updateSchema(schema.key, fieldsToConfig(fields));
        setSchema({ ...schema, dirty: false });
        showToast({ name: schema.name, kind: `updated in config/fields/${schema.key}.json` });
      } else {
        const name = schema.key ? `${schema.name} custom` : schema.name === 'Default' ? 'My schema' : schema.name;
        const created = await api.createSchema(uniqueKey(name), fieldsToConfig(fields));
        setSchema({ key: created.key, name: created.name, builtin: false, dirty: false });
        showToast({ name: created.name, kind: `saved to config/fields/${created.key}.json` });
      }
      refreshSchemas();
    } catch (e) {
      setError(e.message);
    }
  };

  const renameSchema = async (name) => {
    if (!schema.key) { setSchema({ ...schema, name }); return; }
    // A saved schema's name is its file name, so renaming means writing a new file
    setError(null);
    try {
      const created = await api.createSchema(uniqueKey(name), fieldsToConfig(fields));
      await api.deleteSchema(schema.key);
      setSchema({ key: created.key, name: created.name, builtin: false, dirty: false });
      refreshSchemas();
    } catch (e) {
      setError(e.message);
    }
  };

  const goPipeline = () => {
    if (!fields.length) return;
    markCompleted(2);
    setStep(3);
  };

  const pickPipeline = (p) => {
    const cfg = catalog.pipelines.find((x) => x.id === p) || {};
    const candidates = p === 'vlm_direct' ? catalog.models.filter((m) => m.supports_vision) : catalog.models;
    const keepModel = candidates.some((m) => m.id === config.model && m.available);
    setPipeline(p);
    setConfig({
      model: keepModel ? config.model : pickDefault(candidates, cfg.default_model),
      ocr: p === 'ocr_llm' ? (config.ocr || pickDefault(catalog.ocrEngines, cfg.default_ocr_engine)) : null,
      prompt: cfg.prompt || catalog.prompts[0]?.name,
    });
    markCompleted(3);
    if (step < 4) setStep(4);
  };

  const modelValid = pipeline === 'vlm_direct' ? !!config.model : !!config.model && !!config.ocr;

  const run = async () => {
    setError(null);
    try {
      const res = await api.createJob({
        document_id: doc.id,
        pipeline,
        model_id: config.model,
        ocr_engine_id: pipeline === 'ocr_llm' ? config.ocr : null,
        prompt: config.prompt,
        schema_key: schema.dirty ? null : schema.key,
        fields: fieldsToConfig(fields),
      });
      setJob(null);
      setJobId(res.job_id);
      setStartedAt(Date.now());
      markCompleted(4);
      uncomplete(5);
      setStep(5);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    if (!jobId) return undefined;
    let stopped = false;
    const tick = async () => {
      try {
        const j = await api.job(jobId);
        if (stopped) return;
        setJob(j);
        if (j.status === 'done' || j.status === 'failed') {
          markCompleted(5);
          return;
        }
      } catch (e) {
        if (!stopped) setError(e.message);
      }
      if (!stopped) setTimeout(tick, 600);
    };
    tick();
    return () => { stopped = true; };
  }, [jobId]);

  const tryAnotherModel = () => {
    setJobId(null);
    setJob(null);
    uncomplete(4, 5);
    setStep(4);
  };

  const onStepClick = (n) => {
    if (n === 1) { reset(); return; }
    if (n === 5 || n > step) return;
    if (n < step) {
      uncomplete(...[2, 3, 4, 5].filter((x) => x >= n));
      setJobId(null);
      setJob(null);
    }
    setStep(n);
  };

  const processing = step === 5 && (!job || job.status === 'queued' || job.status === 'running');
  const modelName = catalog.models.find((m) => m.id === config.model)?.display_name || config.model;
  const ocrName = catalog.ocrEngines.find((o) => o.id === config.ocr)?.display_name || config.ocr;

  const errorBox = error && (
    <div className="alert alert-danger" style={{ marginBottom: 12 }}>
      <IconAlert size={15} style={{ flexShrink: 0, marginTop: 1 }} /> <span>{error}</span>
    </div>
  );

  const configView = (
    <div className="fade-in">
      <div style={{ marginBottom: 22 }}>
        <h2 className="page-title">Configure extraction</h2>
        <p className="page-sub">Define the schema first, then choose how to extract it.</p>
      </div>
      {errorBox}

      <SchemaFieldsPanel current={schema} schemas={schemas} fields={fields}
        onSchemaSelect={selectSchema} onRename={renameSchema} setFields={setFields} />

      {step === 2 && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginTop: 4, marginBottom: 8 }}>
          <div style={{ fontSize: 12, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            {fields.length === 0 ? (
              <span style={{ color: 'var(--warning)', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                <IconInfo size={13} /> Add at least one field to continue.
              </span>
            ) : (
              <><IconInfo size={13} /> Configuration can still be used without saving permanently.</>
            )}
            {toast && (
              <span style={{ color: 'var(--success)', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                <IconCheck size={12} strokeWidth={2.5} /> "{toast.name}" {toast.kind}
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary" onClick={saveSchema} disabled={!fields.length || (schema.key && !schema.builtin && !schema.dirty)}>
              <IconSave size={14} /> Save configuration
            </button>
            <button className="btn btn-primary" onClick={goPipeline} disabled={!fields.length}>
              Choose pipeline <IconChevronRight size={14} />
            </button>
          </div>
        </div>
      )}

      {step >= 3 && <PipelineSection pipelines={catalog.pipelines} pipeline={pipeline} setPipeline={pickPipeline} />}

      {step >= 4 && pipeline && (
        <>
          <ModelSection pipeline={pipeline} models={catalog.models} ocrEngines={catalog.ocrEngines}
            prompts={catalog.prompts} config={config} setConfig={setConfig} />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginTop: 8 }}>
            <div style={{ fontSize: 12, color: 'var(--text-3)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <IconInfo size={13} /> Editing schema or fields above will reset pipeline configuration.
            </div>
            <button className="btn btn-primary" onClick={run} disabled={!modelValid}>
              <IconBolt size={14} /> Run extraction
            </button>
          </div>
        </>
      )}
    </div>
  );

  let content;
  if (step === 1) content = <StepUpload onUploaded={handleUploaded} />;
  else if (step <= 4) content = configView;
  else if (processing) {
    content = (
      <div className="fade-in">
        <div style={{ marginBottom: 18 }}>
          <h2 className="page-title">Processing</h2>
          <p className="page-sub">Pipeline: <strong>{PIPELINE_LABEL[pipeline]}</strong> · {modelName}{pipeline === 'ocr_llm' ? ` · ${ocrName}` : ''}</p>
        </div>
        {errorBox}
        <ProcessingPanel pipeline={pipeline} stage={job?.stage} modelName={modelName} ocrName={ocrName} startedAt={startedAt} />
      </div>
    );
  } else {
    content = (
      <ResultsView
        job={job}
        onJobUpdate={setJob}
        actions={(
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary" onClick={tryAnotherModel}><IconBolt size={14} /> Try another model</button>
            <button className="btn btn-primary" onClick={reset}><IconRefresh size={14} /> Extract another document</button>
          </div>
        )}
      />
    );
  }

  return (
    <>
      <Header page="extract" stepper={<Stepper current={step} completed={completed} onStepClick={onStepClick} />} />
      <main style={{ maxWidth: 1400, margin: '0 auto', padding: step === 1 ? '8px 24px 48px' : '28px 24px 48px' }}>
        {step === 1 || !doc ? (
          <>{step === 1 && error && <div style={{ maxWidth: 880, margin: '16px auto 0' }}>{errorBox}</div>}{content}</>
        ) : (
          <div className="extract-grid">
            <div><DocumentPreview doc={doc} scanning={processing} onRemove={reset} /></div>
            <div style={{ minWidth: 0 }}>{content}</div>
          </div>
        )}
      </main>
    </>
  );
}
