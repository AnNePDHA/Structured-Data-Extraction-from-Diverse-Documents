"""Benchmark runner for invoice extraction pipelines.

Supports multiple model backends (auto-detected from --model):
    Gemini        : gemini-2.5-flash, gemini-2.5-pro, ...
    Azure OpenAI  : gpt-4o, gpt-5-chat, gpt-5.2-chat
    Azure Foundry : Phi-4-multimodal-instruct, Llama-4-Maverick-17B-128E-Instruct-FP8

Usage:
    python scripts/run_benchmark.py \\
        --dataset data-processed/EN/Typed-Invoice \\
        --pipeline both \\
        --model gpt-4o \\
        --output results/

    # OCR-LLM with Azure Document Intelligence
    python scripts/run_benchmark.py \\
        --pipeline ocr_llm --model gpt-4o --ocr-engine azure_di --limit 1

    # Dry-run with 1 sample on Gemini
    python scripts/run_benchmark.py \\
        --dataset data-processed/EN/Typed-Invoice \\
        --pipeline vlm_direct --model gemini-2.5-flash --limit 1
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Allow running from project root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.metrics import aggregate, exact_match, token_f1
from pipelines.model_clients import build_client
from pipelines.ocr_engines import build_engine
from pipelines.ocr_llm import OCRLLMPipeline
from pipelines.prompt_config import (
    field_names,
    load_field_config,
    load_prompt_template,
)
from pipelines.vlm_direct import VLMDirectPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
# Silence verbose HTTP request/response logging from SDKs. Azure's
# http_logging_policy and httpx log every call (incl. Document Intelligence
# upload + polling) at INFO, which floods the OCR-LLM run output.
for _noisy in ("azure", "azure.core", "httpx", "urllib3", "openai"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_ground_truth(dataset_dir: Path) -> list[dict]:
    """Load all ground truth JSON files from <dataset_dir>/ground_truth/."""
    gt_dir = dataset_dir / "ground_truth"
    if not gt_dir.exists():
        raise FileNotFoundError(f"Ground truth directory not found: {gt_dir}")
    records = []
    for p in sorted(gt_dir.glob("*.json")):
        with open(p, encoding="utf-8") as f:
            records.append(json.load(f))
    return records


def resolve_image_path(gt_record: dict, dataset_dir: Path) -> Path:
    """Resolve image path relative to dataset_dir/img/."""
    image_path = gt_record.get("image_path", "")
    # image_path may be "img/X51005361900.jpg" — use filename only
    img_name = Path(image_path).name
    candidate = dataset_dir / "img" / img_name
    if candidate.exists():
        return candidate
    raise FileNotFoundError(
        f"Image not found for {gt_record['doc_name']}: expected {candidate}"
    )


def make_run_dir(
    output_dir: Path, gt_records: list[dict], pipeline_name: str, model: str
) -> Path:
    """Create and return a timestamped run directory.

    Layout:
        results/{pipeline}_{model}_{timestamp}/
            {doc_name}.json   ← one file per invoice
            summary.jsonl     ← all records concatenated for aggregate analysis
    """
    first = gt_records[0]
    lang = first.get("lang", "XX")
    subtype = first.get("subtype", "unknown")
    doc_type = first.get("doc_type", "unknown")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_name = f"{lang}_{subtype}-{doc_type}_{pipeline_name}_{model}_{ts}"
    run_dir = output_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _usage_stats(results: list[dict]) -> dict:
    """Aggregate usage tokens across successful records."""
    rows = [r["usage"] for r in results if r.get("usage")]
    if not rows:
        return {}
    n = len(rows)
    return {
        "n_with_usage": n,
        "avg_prompt_tokens": sum(r.get("prompt_tokens") or 0 for r in rows) / n,
        "avg_completion_tokens": sum(r.get("completion_tokens") or 0 for r in rows) / n,
        "avg_thinking_tokens": sum(r.get("thinking_tokens") or 0 for r in rows) / n,
        "avg_total_tokens": sum(r.get("total_tokens") or 0 for r in rows) / n,
        "sum_total_tokens": sum(r.get("total_tokens") or 0 for r in rows),
    }


def print_summary(agg: dict, pipeline_name: str, usage_stats: dict) -> None:
    """Print a formatted summary table."""
    fields = list(agg["exact_match"].keys())
    sep = "-" * 60
    print(f"\n{'='*60}")
    print(f"  Pipeline: {pipeline_name}  |  N={agg['n']}")
    print(sep)
    print(f"  {'Field':<12} {'Exact Match':>12} {'Token F1':>10}")
    print(sep)
    for f in fields:
        em = agg["exact_match"][f]
        f1 = agg["token_f1"][f]
        print(f"  {f:<12} {em:>11.1%} {f1:>10.3f}")
    print(sep)
    print(
        f"  {'OVERALL':<12} {agg['overall_exact_match']:>11.1%} "
        f"{agg['overall_token_f1']:>10.3f}"
    )
    if usage_stats:
        print(sep)
        avg_think = usage_stats["avg_thinking_tokens"]
        think_part = f"  think: {avg_think:>6.1f}" if avg_think else ""
        print(
            f"  Avg tokens — in: {usage_stats['avg_prompt_tokens']:>7.1f}  "
            f"out: {usage_stats['avg_completion_tokens']:>6.1f}"
            f"{think_part}  "
            f"total: {usage_stats['avg_total_tokens']:>7.1f}"
        )
        print(f"  Cumulative total tokens: {usage_stats['sum_total_tokens']:,}")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Per-pipeline runner
# ---------------------------------------------------------------------------


def run_pipeline(
    pipeline,
    pipeline_name: str,
    gt_records: list[dict],
    dataset_dir: Path,
    run_dir: Path,
    limit: int | None,
    fields: list[str],
) -> list[dict]:
    """Run pipeline over all ground truth records and write results incrementally.

    Output layout inside run_dir:
        {doc_name}.json   ← one JSON file per invoice (written immediately after each call)
        summary.jsonl     ← all records appended line-by-line (for aggregate analysis)
    """
    records_to_run = gt_records[:limit] if limit else gt_records
    total = len(records_to_run)
    results = []
    summary_path = run_dir / "summary.jsonl"

    logger.info(
        "Starting %s pipeline on %d records → %s",
        pipeline_name,
        total,
        run_dir,
    )

    with open(summary_path, "a", encoding="utf-8") as summary_f:
        for idx, gt in enumerate(records_to_run, start=1):
            doc_name = gt["doc_name"]
            gold_fields = gt.get("fields", {})

            try:
                image_path = resolve_image_path(gt, dataset_dir)
            except FileNotFoundError as exc:
                logger.error("Skipping %s: %s", doc_name, exc)
                continue

            t0 = time.perf_counter()
            error_msg = None
            predicted = {f: None for f in fields}
            usage = None
            pipeline_meta = {}

            try:
                result = pipeline.extract(image_path)
                predicted = result.fields
                usage = result.usage
                pipeline_meta = result.meta
            except Exception as exc:
                error_msg = str(exc)
                logger.error("Error processing %s: %s", doc_name, exc)

            latency = round(time.perf_counter() - t0, 3)

            em = exact_match(predicted, gold_fields, fields)
            f1 = token_f1(predicted, gold_fields, fields)
            overall_em = sum(em.values()) / len(em) if em else 0.0
            overall_f1 = sum(f1.values()) / len(f1) if f1 else 0.0

            record = {
                "doc_name": doc_name,
                "pipeline": pipeline_name,
                "model": pipeline.model,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "predicted": predicted,
                "ground_truth": gold_fields,
                "exact_match": em,
                "token_f1": {k: round(v, 4) for k, v in f1.items()},
                "overall_exact_match": round(overall_em, 4),
                "overall_token_f1": round(overall_f1, 4),
                "latency_sec": latency,
                "usage": usage,
                "meta": pipeline_meta,
                "error": error_msg,
            }

            # Write individual JSON file for this invoice (immediately, no buffering)
            doc_json_path = run_dir / f"{doc_name}.json"
            with open(doc_json_path, "w", encoding="utf-8") as doc_f:
                json.dump(record, doc_f, ensure_ascii=False, indent=2)

            # Append to summary JSONL for aggregate analysis
            summary_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            summary_f.flush()

            results.append(record)
            if usage:
                thk = usage.get("thinking_tokens")
                tok_str = (
                    f" | in={usage['prompt_tokens']} "
                    f"out={usage['completion_tokens']}"
                    + (f" think={thk}" if thk else "")
                )
            else:
                tok_str = ""
            print(
                f"[{idx:>3}/{total}] {doc_name} | "
                f"EM={overall_em:.0%} | F1={overall_f1:.3f} | {latency:.1f}s"
                + tok_str
                + (f" | ERROR: {error_msg[:60]}" if error_msg else "")
            )

    return results


# ---------------------------------------------------------------------------
# Dataset discovery + field-config resolution
# ---------------------------------------------------------------------------


def discover_datasets(root: Path) -> list[Path]:
    """Find every dataset dir under root that has both ground_truth/ and img/.

    Returns the sorted list of dataset directories.
    """
    found = []
    for gt_dir in sorted(root.rglob("ground_truth")):
        ds = gt_dir.parent
        if (ds / "img").is_dir():
            found.append(ds)
    return found


def resolve_fields_config(dataset_dir: Path, fields_dir: Path) -> Path | None:
    """Map a dataset's doc_type to config/fields/<doc_type>.json.

    Reads doc_type from the first ground-truth record. Returns None if no
    matching field config exists (caller should skip the dataset).
    """
    records = load_ground_truth(dataset_dir)
    if not records:
        return None
    doc_type = records[0].get("doc_type")
    if not doc_type:
        return None
    candidate = fields_dir / f"{doc_type}.json"
    return candidate if candidate.exists() else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Invoice extraction benchmark runner")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("data-processed/EN/Typed-Invoice"),
        help="Path to one processed dataset directory (contains ground_truth/ and img/). "
        "Ignored if --dataset-root is given.",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=None,
        help="Run EVERY dataset under this root (e.g. data-processed): auto-discovers "
        "subdirs containing ground_truth/ + img/ and picks each one's field config "
        "by doc_type. Overrides --dataset.",
    )
    parser.add_argument(
        "--pipeline",
        choices=["vlm_direct", "ocr_llm", "both"],
        default="both",
        help="Which pipeline(s) to run",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Model name. Gemini: gemini-2.5-flash (free tier 5 RPM/20 RPD), "
        "gemini-2.5-pro, etc. Azure OpenAI: gpt-4o, gpt-5-chat, gpt-5.2-chat. "
        "Azure Foundry: Phi-4-multimodal-instruct, "
        "Llama-4-Maverick-17B-128E-Instruct-FP8, DeepSeek-V4-Flash (text-only → "
        "ocr_llm pipeline only).",
    )
    parser.add_argument(
        "--ocr-engine",
        choices=["easyocr", "azure_di"],
        default="easyocr",
        help="OCR engine for the ocr_llm pipeline (default: easyocr). "
        "'azure_di' = Azure Document Intelligence (prebuilt-read).",
    )
    parser.add_argument(
        "--ocr-lang",
        default="en",
        help="Language code(s) for EasyOCR, e.g. 'en' or 'en,vi' (ignored by azure_di).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results"),
        help="Output directory for .jsonl result files",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of samples (for testing)",
    )
    parser.add_argument(
        "--fields-config",
        type=Path,
        default=None,
        help="Path to the field-config JSON. If omitted, it is auto-derived from each "
        "dataset's doc_type → config/fields/<doc_type>.json.",
    )
    parser.add_argument(
        "--fields-dir",
        type=Path,
        default=Path("config/fields"),
        help="Directory holding per-doc_type field configs (default: config/fields).",
    )
    parser.add_argument(
        "--prompts-dir",
        type=Path,
        default=Path("config/prompts"),
        help="Directory holding vlm_direct.md and ocr_llm.md prompt templates",
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()

    # Resolve the model backend (Gemini or Azure). build_client validates that
    # the required env vars for the chosen provider are present.
    try:
        client = build_client(args.model)
    except (ValueError, RuntimeError) as exc:
        sys.exit(f"ERROR: {exc}")
    logger.info("Model %s → provider %s", client.name, client.provider)

    # Build the list of datasets to run, each paired with its field config.
    # --dataset-root → scan & auto-map by doc_type; otherwise the single --dataset.
    jobs: list[tuple[Path, Path]] = []  # (dataset_dir, fields_config)
    if args.dataset_root is not None:
        datasets = discover_datasets(args.dataset_root)
        if not datasets:
            sys.exit(f"ERROR: no datasets (ground_truth/ + img/) found under {args.dataset_root}")
        logger.info("Discovered %d datasets under %s", len(datasets), args.dataset_root)
        for ds in datasets:
            fc = resolve_fields_config(ds, args.fields_dir)
            if fc is None:
                logger.warning("Skipping %s — no field config for its doc_type", ds)
                continue
            jobs.append((ds, fc))
    else:
        # Single dataset: explicit --fields-config, else auto-derive from doc_type.
        fc = args.fields_config or resolve_fields_config(args.dataset, args.fields_dir)
        if fc is None:
            sys.exit(
                f"ERROR: could not resolve a field config for {args.dataset}. "
                "Pass --fields-config explicitly."
            )
        jobs.append((args.dataset, fc))

    if not jobs:
        sys.exit("ERROR: no runnable datasets (all skipped for missing field config).")

    # Prompt templates + OCR engine are shared across all datasets.
    vlm_template = ocr_template = ocr_engine = None
    if args.pipeline in ("vlm_direct", "both"):
        vlm_template = load_prompt_template(args.prompts_dir / "vlm_direct.md")
    if args.pipeline in ("ocr_llm", "both"):
        ocr_template = load_prompt_template(args.prompts_dir / "ocr_llm.md")
        ocr_engine = build_engine(args.ocr_engine, lang=args.ocr_lang)
        logger.info("OCR engine: %s", ocr_engine.name)

    for dataset_dir, fields_config_path in jobs:
        gt_records = load_ground_truth(dataset_dir)
        field_config = load_field_config(fields_config_path)
        fields = field_names(field_config)
        logger.info(
            "=== %s (%d records) | fields[%d]: %s ===",
            dataset_dir,
            len(gt_records),
            len(fields),
            ", ".join(fields),
        )

        # Field config differs per dataset, so pipelines are rebuilt each time.
        pipelines_to_run = []
        if args.pipeline in ("vlm_direct", "both"):
            pipelines_to_run.append(
                (
                    "vlm_direct",
                    VLMDirectPipeline(
                        client=client,
                        prompt_template=vlm_template,
                        field_config=field_config,
                    ),
                )
            )
        if args.pipeline in ("ocr_llm", "both"):
            pipelines_to_run.append(
                (
                    "ocr_llm",
                    OCRLLMPipeline(
                        client=client,
                        prompt_template=ocr_template,
                        field_config=field_config,
                        ocr_engine=ocr_engine,
                    ),
                )
            )

        for pipeline_name, pipeline in pipelines_to_run:
            run_dir = make_run_dir(args.output, gt_records, pipeline_name, args.model)
            results = run_pipeline(
                pipeline=pipeline,
                pipeline_name=pipeline_name,
                gt_records=gt_records,
                dataset_dir=dataset_dir,
                run_dir=run_dir,
                limit=args.limit,
                fields=fields,
            )
            if results:
                agg = aggregate(results, fields)
                usage_stats = _usage_stats(results)
                print_summary(agg, pipeline_name, usage_stats)
                logger.info("Results saved to %s", run_dir)


if __name__ == "__main__":
    main()
