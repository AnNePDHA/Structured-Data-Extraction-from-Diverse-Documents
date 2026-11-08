"""Paths and app-level config. Everything tunable lives in config/app.json."""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = ROOT / "config"
FIELDS_DIR = CONFIG_DIR / "fields"
PROMPTS_DIR = CONFIG_DIR / "prompts"
APP_CONFIG_PATH = CONFIG_DIR / "app.json"

# pipelines/ is imported as a top-level package, same as scripts/run_benchmark.py
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")


def app_config() -> dict:
    with open(APP_CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


_storage = app_config()["storage"]
DATA_DIR = ROOT / _storage["data_dir"]
UPLOAD_DIR = DATA_DIR / "uploads"
JOBS_DIR = DATA_DIR / "jobs"
DB_PATH = DATA_DIR / "app.db"

for _d in (UPLOAD_DIR, JOBS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
