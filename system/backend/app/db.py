"""SQLite index for documents and jobs. Job artifacts themselves live on disk."""

import sqlite3
import threading
from contextlib import contextmanager

from .settings import DB_PATH

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    mime TEXT,
    size INTEGER,
    pages INTEGER,
    created_at TEXT NOT NULL,
    dir TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    created_at TEXT NOT NULL,
    schema_key TEXT,
    pipeline TEXT NOT NULL,
    model_id TEXT NOT NULL,
    ocr_engine_id TEXT,
    status TEXT NOT NULL,
    stage TEXT,
    latency_sec REAL,
    cost_usd REAL,
    error TEXT,
    edited INTEGER NOT NULL DEFAULT 0,
    job_dir TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        with _lock:
            yield conn
            conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        # Jobs cut off by a server restart can never finish
        conn.execute(
            "UPDATE jobs SET status='failed', error='Server restarted while the job was running' "
            "WHERE status IN ('queued', 'running')"
        )


def insert(table: str, row: dict) -> None:
    cols = ", ".join(row)
    marks = ", ".join("?" for _ in row)
    with connect() as conn:
        conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({marks})", tuple(row.values()))


def update(table: str, row_id: str, **values) -> None:
    sets = ", ".join(f"{k}=?" for k in values)
    with connect() as conn:
        conn.execute(f"UPDATE {table} SET {sets} WHERE id=?", (*values.values(), row_id))


def get(table: str, row_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (row_id,)).fetchone()
    return dict(row) if row else None


def delete(table: str, row_id: str) -> None:
    with connect() as conn:
        conn.execute(f"DELETE FROM {table} WHERE id=?", (row_id,))


def list_jobs(limit: int, offset: int) -> tuple[list[dict], int]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    return [dict(r) for r in rows], total
