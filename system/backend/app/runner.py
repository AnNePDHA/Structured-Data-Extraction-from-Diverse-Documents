"""Run one extraction job and write its artifacts, mirroring run_benchmark.py's result records.

Job folder (system/data/jobs/<job_id>/):
    input.<ext>, page1.png, request.json, fields.json, prompt.txt,
    ocr_text.txt (OCR-LLM only), raw_response.txt, result.json, edited.json (after edits)
"""

import csv
import io
import json
import logging
import shutil
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from . import config_store, db
from .documents import PAGE_IMAGE, get_document
from .settings import JOBS_DIR, PROMPTS_DIR, app_config

from pipelines.model_clients import build_client, get_model_entry
from pipelines.ocr_engines import OCREngine, build_ocr_engine, load_ocr_registry
from pipelines.ocr_llm import OCRLLMPipeline
from pipelines.prompt_config import load_prompt_template
from pipelines.vlm_direct import VLMDirectPipeline

logger = logging.getLogger(__name__)

PIPELINES = ("vlm_direct", "ocr_llm")
TEXT_ARTIFACTS = ("prompt.txt", "ocr_text.txt", "raw_response.txt", "request.json", "fields.json")
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="job")
# EasyOCR loads its model for several seconds, so engines are reused across jobs
_ocr_cache: dict[str, OCREngine] = {}
_ocr_lock = threading.Lock()


class JobError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _get_ocr_engine(engine_id: str) -> OCREngine:
    with _ocr_lock:
        if engine_id not in _ocr_cache:
            _ocr_cache[engine_id] = build_ocr_engine(engine_id)
        return _ocr_cache[engine_id]


def compute_cost(model_entry: dict, usage: dict | None, ocr_entry: dict | None) -> dict:
    """USD cost from config prices: tokens × price_per_1m, plus OCR price_per_page × 1 page.

    Thinking tokens (Gemini 2.5) are billed at the output price.
    """
    price = model_entry.get("price_per_1m")
    llm = None
    if price and usage:
        prompt = usage.get("prompt_tokens") or 0
        completion = usage.get("completion_tokens") or 0
        thinking = usage.get("thinking_tokens")
        # Gemini may leave thinking_tokens empty while total_tokens still counts them
        if thinking is None and usage.get("total_tokens"):
            thinking = max(0, usage["total_tokens"] - prompt - completion)
        llm = (prompt * price["input"] + (completion + (thinking or 0)) * price["output"]) / 1e6
    ocr = ocr_entry.get("price_per_page", 0) if ocr_entry else 0.0
    total = None if llm is None else llm + ocr
    return {
        "llm_usd": None if llm is None else round(llm, 6),
        "ocr_usd": round(ocr, 6),
        "total_usd": None if total is None else round(total, 6),
    }


def create_job(req: dict) -> dict:
    """Validate the request, snapshot inputs into the job folder and queue the run."""
    pipeline = req["pipeline"]
    if pipeline not in PIPELINES:
        raise JobError(f"pipeline must be one of {PIPELINES}")
    doc = get_document(req["document_id"])

    model_entry = get_model_entry(req["model_id"])
    if pipeline == "vlm_direct" and not model_entry.get("supports_vision"):
        raise JobError(f"Model {req['model_id']!r} has no vision support; use ocr_llm")

    pipe_cfg = app_config()["pipelines"][pipeline]
    ocr_engine_id = None
    if pipeline == "ocr_llm":
        ocr_engine_id = req.get("ocr_engine_id") or pipe_cfg.get("default_ocr_engine")
        if ocr_engine_id not in load_ocr_registry():
            raise JobError(f"Unknown OCR engine {ocr_engine_id!r}")

    if req.get("fields"):
        fields = config_store.normalize_fields(req["fields"])
    elif req.get("schema_key"):
        fields = config_store.get_schema(req["schema_key"])["fields"]
    else:
        raise JobError("Provide schema_key or fields")

    prompt_name = req.get("prompt") or pipe_cfg["prompt"]
    config_store.get_prompt(prompt_name)

    job_id = uuid.uuid4().hex[:12]
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True)
    src_dir = Path(doc["dir"])
    for p in src_dir.iterdir():
        shutil.copy2(p, job_dir / p.name)

    request = {
        "job_id": job_id,
        "document_id": doc["id"],
        "filename": doc["filename"],
        "schema_key": req.get("schema_key"),
        "pipeline": pipeline,
        "model_id": req["model_id"],
        "ocr_engine_id": ocr_engine_id,
        "prompt": prompt_name,
        "created_at": _now(),
    }
    _write_json(job_dir / "request.json", request)
    _write_json(job_dir / "fields.json", fields)

    db.insert(
        "jobs",
        {
            "id": job_id,
            "document_id": doc["id"],
            "filename": doc["filename"],
            "created_at": request["created_at"],
            "schema_key": req.get("schema_key"),
            "pipeline": pipeline,
            "model_id": req["model_id"],
            "ocr_engine_id": ocr_engine_id,
            "status": "queued",
            "stage": None,
            "job_dir": str(job_dir),
        },
    )
    _executor.submit(_run_job, job_id)
    return {"job_id": job_id, "status": "queued"}


def _run_job(job_id: str) -> None:
    job_dir = JOBS_DIR / job_id
    request = json.loads((job_dir / "request.json").read_text(encoding="utf-8"))
    fields = json.loads((job_dir / "fields.json").read_text(encoding="utf-8"))
    pipeline_name = request["pipeline"]

    def on_stage(stage: str) -> None:
        db.update("jobs", job_id, stage=stage)

    db.update("jobs", job_id, status="running", stage="prepare")
    t0 = time.perf_counter()
    result = None
    error = None
    model_entry: dict = {}
    ocr_entry = None
    try:
        model_entry = get_model_entry(request["model_id"])
        client = build_client(request["model_id"], model_entry)
        template = load_prompt_template(PROMPTS_DIR / request["prompt"])
        if pipeline_name == "vlm_direct":
            pipeline = VLMDirectPipeline(client, template, fields)
        else:
            ocr_entry = load_ocr_registry()[request["ocr_engine_id"]]
            pipeline = OCRLLMPipeline(
                client, template, fields, ocr_engine=_get_ocr_engine(request["ocr_engine_id"])
            )
        result = pipeline.extract(job_dir / PAGE_IMAGE, on_stage=on_stage)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        error = str(exc)
    latency = round(time.perf_counter() - t0, 3)

    meta = dict(result.meta) if result else {}
    for key, fname in (
        ("prompt", "prompt.txt"),
        ("ocr_text", "ocr_text.txt"),
        ("raw_response", "raw_response.txt"),
    ):
        value = meta.pop(key, None)
        if value is not None:
            (job_dir / fname).write_text(value, encoding="utf-8")

    usage = result.usage if result else None
    cost = compute_cost(model_entry, usage, ocr_entry)
    record = {
        "job_id": job_id,
        "doc_name": request["filename"],
        "pipeline": pipeline_name,
        "model": request["model_id"],
        "model_display_name": model_entry.get("display_name", request["model_id"]),
        "ocr_engine": request["ocr_engine_id"],
        "ocr_engine_display_name": (ocr_entry or {}).get("display_name"),
        "schema_key": request["schema_key"],
        "prompt": request["prompt"],
        "timestamp": _now(),
        "predicted": result.fields if result else {f: None for f in fields},
        "usage": usage,
        "latency_sec": latency,
        "stage_sec": meta.pop("stage_sec", {}),
        "cost": cost,
        "meta": meta,
        "error": error,
    }
    _write_json(job_dir / "result.json", record)
    db.update(
        "jobs",
        job_id,
        status="failed" if error else "done",
        stage=None,
        latency_sec=latency,
        cost_usd=cost["total_usd"],
        error=error,
    )


# ---------------------------------------------------------------------------
# Reading, editing, exporting
# ---------------------------------------------------------------------------


def _job_row(job_id: str) -> dict:
    row = db.get("jobs", job_id)
    if row is None:
        raise FileNotFoundError(job_id)
    return row


def get_job(job_id: str) -> dict:
    row = _job_row(job_id)
    job_dir = Path(row["job_dir"])
    out = {k: v for k, v in row.items() if k != "job_dir"}
    out["edited"] = bool(row["edited"])
    out["preview_url"] = f"/api/jobs/{job_id}/preview"
    out["artifacts"] = [n for n in TEXT_ARTIFACTS if (job_dir / n).exists()]
    out["fields_config"] = json.loads((job_dir / "fields.json").read_text(encoding="utf-8"))
    result_path = job_dir / "result.json"
    out["result"] = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else None
    edited_path = job_dir / "edited.json"
    out["edited_fields"] = (
        json.loads(edited_path.read_text(encoding="utf-8"))["fields"] if edited_path.exists() else None
    )
    return out


def job_file(job_id: str, name: str) -> Path:
    return Path(_job_row(job_id)["job_dir"]) / name


def save_edits(job_id: str, fields: dict) -> dict:
    row = _job_row(job_id)
    if row["status"] != "done":
        raise JobError("Only finished jobs can be edited")
    job_dir = Path(row["job_dir"])
    _write_json(job_dir / "edited.json", {"fields": fields, "edited_at": _now()})
    db.update("jobs", job_id, edited=1)
    return get_job(job_id)


def _final_fields(job: dict) -> dict:
    if job["edited_fields"] is not None:
        return job["edited_fields"]
    return (job["result"] or {}).get("predicted", {})


def export_json(job_id: str) -> str:
    job = get_job(job_id)
    r = job["result"] or {}
    data = {
        "fields": _final_fields(job),
        "metadata": {
            "document": job["filename"],
            "schema": job["schema_key"],
            "pipeline": job["pipeline"],
            "model": job["model_id"],
            "ocr_engine": job["ocr_engine_id"],
            "edited": job["edited"],
            "usage": r.get("usage"),
            "latency_sec": r.get("latency_sec"),
            "cost": r.get("cost"),
            "timestamp": r.get("timestamp"),
        },
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def export_csv(job_id: str) -> str:
    job = get_job(job_id)
    fields = _final_fields(job)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["field", "value"])
    for name, value in fields.items():
        writer.writerow([name, "" if value is None else value])
    # BOM so Excel opens Vietnamese text correctly
    return "﻿" + buf.getvalue()


def export_bundle(job_id: str) -> bytes:
    job_dir = Path(_job_row(job_id)["job_dir"])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(job_dir.iterdir()):
            zf.write(p, f"{job_id}/{p.name}")
    return buf.getvalue()


def list_jobs(limit: int, offset: int) -> dict:
    rows, total = db.list_jobs(limit, offset)
    items = [{k: v for k, v in r.items() if k != "job_dir"} for r in rows]
    for item in items:
        item["edited"] = bool(item["edited"])
    return {"items": items, "total": total}


def delete_job(job_id: str) -> None:
    row = _job_row(job_id)
    if row["status"] in ("queued", "running"):
        raise JobError("Job is still running")
    shutil.rmtree(row["job_dir"], ignore_errors=True)
    db.delete("jobs", job_id)
