"""Read/write the file-based config: config/fields, config/prompts, models.json, ocr_engines.json.

The web app never keeps its own copy of these; every request reads the files,
so edits made by hand or by run_benchmark.py show up immediately.
"""

import json
import os
import re
import threading
from pathlib import Path

from .settings import FIELDS_DIR, PROMPTS_DIR, app_config

from pipelines.model_clients import (
    MODELS_CONFIG_PATH,
    PROVIDERS,
    load_model_registry,
    required_env,
)
from pipelines.ocr_engines import load_ocr_registry
from pipelines.prompt_config import load_field_config

_write_lock = threading.Lock()
KEY_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{0,63}$")
PROMPT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{0,63}\.md$")


class ConfigError(ValueError):
    pass


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with _write_lock:
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)


def _write_json(path: Path, data: dict) -> None:
    _atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Schemas: config/fields/<key>.json
# ---------------------------------------------------------------------------


def _schema_path(key: str) -> Path:
    if not KEY_RE.match(key):
        raise ConfigError(f"Invalid schema key: {key!r}")
    return FIELDS_DIR / f"{key}.json"


def _schema_name(key: str) -> str:
    return key.replace("_", " ").replace("-", " ").title()


def list_schemas() -> list[dict]:
    builtin = set(app_config().get("builtin_schemas", []))
    out = []
    for p in sorted(FIELDS_DIR.glob("*.json")):
        try:
            fields = load_field_config(p)
        except (ValueError, json.JSONDecodeError):
            continue
        out.append(
            {
                "key": p.stem,
                "name": _schema_name(p.stem),
                "field_count": len(fields),
                "builtin": p.stem in builtin,
            }
        )
    return out


def get_schema(key: str) -> dict:
    path = _schema_path(key)
    if not path.exists():
        raise FileNotFoundError(key)
    return {
        "key": key,
        "name": _schema_name(key),
        "builtin": key in app_config().get("builtin_schemas", []),
        "fields": load_field_config(path),
    }


def normalize_fields(fields: dict) -> dict:
    """Keep the benchmark field-config shape: {name: {description, format?}}."""
    if not isinstance(fields, dict) or not fields:
        raise ConfigError("A schema needs at least one field")
    out = {}
    for name, meta in fields.items():
        name = str(name).strip()
        if not KEY_RE.match(name):
            raise ConfigError(f"Invalid field name: {name!r}")
        if isinstance(meta, str):
            meta = {"description": meta}
        meta = {k: str(v).strip() for k, v in (meta or {}).items() if v not in (None, "")}
        out[name] = meta
    return out


def save_schema(key: str, fields: dict, *, create: bool) -> dict:
    path = _schema_path(key)
    if create and path.exists():
        raise ConfigError(f"Schema {key!r} already exists")
    if not create and not path.exists():
        raise FileNotFoundError(key)
    if not create and key in app_config().get("builtin_schemas", []):
        raise ConfigError(f"Schema {key!r} is a benchmark schema and cannot be changed")
    _write_json(path, normalize_fields(fields))
    return get_schema(key)


def delete_schema(key: str) -> None:
    path = _schema_path(key)
    if key in app_config().get("builtin_schemas", []):
        raise ConfigError(f"Schema {key!r} is a benchmark schema and cannot be deleted")
    if not path.exists():
        raise FileNotFoundError(key)
    path.unlink()


# ---------------------------------------------------------------------------
# Prompt templates: config/prompts/<name>.md
# ---------------------------------------------------------------------------


def _prompt_path(name: str) -> Path:
    if not PROMPT_RE.match(name):
        raise ConfigError(f"Invalid prompt name: {name!r}")
    return PROMPTS_DIR / name


def list_prompts() -> list[dict]:
    defaults = {v["prompt"]: k for k, v in app_config()["pipelines"].items()}
    return [
        {"name": p.name, "default_for": defaults.get(p.name), "size": p.stat().st_size}
        for p in sorted(PROMPTS_DIR.glob("*.md"))
    ]


def get_prompt(name: str) -> str:
    path = _prompt_path(name)
    if not path.exists():
        raise FileNotFoundError(name)
    return path.read_text(encoding="utf-8")


def save_prompt(name: str, text: str) -> None:
    if "{{field_names}}" not in text or "{{fields_schema}}" not in text:
        raise ConfigError("Prompt must keep {{fields_schema}} and {{field_names}}")
    _atomic_write(_prompt_path(name), text)


# ---------------------------------------------------------------------------
# Models: config/models.json
# ---------------------------------------------------------------------------


def _env_status(entry: dict) -> dict:
    missing = [n for n in required_env(entry) if not os.getenv(n)]
    return {"available": not missing, "missing_env": missing}


def list_models(pipeline: str | None = None) -> list[dict]:
    out = []
    for model_id, entry in load_model_registry().items():
        if pipeline == "vlm_direct" and not entry.get("supports_vision"):
            continue
        out.append({"id": model_id, **entry, **_env_status(entry)})
    return out


def get_model(model_id: str) -> dict:
    entry = load_model_registry().get(model_id)
    if entry is None:
        raise FileNotFoundError(model_id)
    return {"id": model_id, **entry, **_env_status(entry)}


def _validate_model(entry: dict) -> dict:
    if entry.get("provider") not in PROVIDERS:
        raise ConfigError(f"provider must be one of {', '.join(PROVIDERS)}")
    if not entry.get("key_env"):
        raise ConfigError("key_env is required (name of the env var holding the API key)")
    if entry["provider"] != "gemini" and not (entry.get("endpoint") or entry.get("endpoint_env")):
        raise ConfigError("endpoint or endpoint_env is required")
    if entry["provider"] == "azure_openai" and not entry.get("api_version_env"):
        raise ConfigError("api_version_env is required for azure_openai")
    return {k: v for k, v in entry.items() if v is not None or k == "price_per_1m"}


def save_model(model_id: str, entry: dict, *, create: bool) -> dict:
    model_id = model_id.strip()
    if not model_id:
        raise ConfigError("Model id is required")
    registry = load_model_registry()
    if create and model_id in registry:
        raise ConfigError(f"Model {model_id!r} already exists")
    if not create and model_id not in registry:
        raise FileNotFoundError(model_id)
    registry[model_id] = _validate_model(entry)
    _write_json(MODELS_CONFIG_PATH, registry)
    return get_model(model_id)


def delete_model(model_id: str) -> None:
    registry = load_model_registry()
    if model_id not in registry:
        raise FileNotFoundError(model_id)
    del registry[model_id]
    _write_json(MODELS_CONFIG_PATH, registry)


# ---------------------------------------------------------------------------
# OCR engines: config/ocr_engines.json (read-only from the app)
# ---------------------------------------------------------------------------


def list_ocr_engines() -> list[dict]:
    out = []
    for engine_id, entry in load_ocr_registry().items():
        names = [entry[k] for k in ("endpoint_env", "key_env") if entry.get(k)]
        missing = [n for n in names if not os.getenv(n)]
        out.append({"id": engine_id, **entry, "available": not missing, "missing_env": missing})
    return out
