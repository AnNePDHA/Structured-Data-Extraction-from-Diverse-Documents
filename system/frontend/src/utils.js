import { useEffect, useState } from 'react';

export const formatBytes = (b) => {
  if (!b) return '';
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / 1024 / 1024).toFixed(2)} MB`;
};

export const formatUsd = (v, digits = 4) => (v === null || v === undefined ? 'n/a' : `$${Number(v).toFixed(digits)}`);

const usd2 = (v) => `$${Number(v).toFixed(2)}`;

export const formatPrice = (price) => {
  if (!price) return 'Price not set';
  return `${usd2(price.input)} in · ${usd2(price.output)} out / 1M tokens`;
};

export const formatOcrPrice = (perPage) =>
  perPage ? `$${(perPage * 1000).toFixed(2)} / 1,000 pages` : 'Free · runs locally';

export const formatTime = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleString(undefined, { year: 'numeric', month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};

export const slugify = (s) =>
  s.trim().toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd')
    .replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 60);

export const fieldKey = (s) => s.trim().toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');

export const PIPELINE_LABEL = { vlm_direct: 'VLM Direct', ocr_llm: 'OCR → LLM' };

// Field list (UI) <-> field config object (config/fields/*.json)
export const fieldsToConfig = (fields) =>
  Object.fromEntries(fields.map((f) => [
    f.name,
    Object.fromEntries(Object.entries({ description: f.description, format: f.format }).filter(([, v]) => v)),
  ]));

export const configToFields = (config) =>
  Object.entries(config || {}).map(([name, meta]) => {
    const m = typeof meta === 'string' ? { description: meta } : meta || {};
    return { name, description: m.description || '', format: m.format || m.unit || '' };
  });

export function useClickOutside(ref, onOutside) {
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) onOutside(); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [ref, onOutside]);
}

export function useHashRoute() {
  const read = () => window.location.hash.replace(/^#\/?/, '').split('/').filter(Boolean);
  const [parts, setParts] = useState(read);
  useEffect(() => {
    const onChange = () => setParts(read());
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);
  return parts;
}

export const navigate = (path) => { window.location.hash = path; };
