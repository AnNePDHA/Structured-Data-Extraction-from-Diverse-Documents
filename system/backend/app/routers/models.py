"""Model management backed by config/models.json. API keys stay in .env; only env var names are stored."""

import time

from fastapi import APIRouter
from pydantic import BaseModel

from .. import config_store

from pipelines.model_clients import build_client, get_model_entry

router = APIRouter(prefix="/models", tags=["models"])


class Price(BaseModel):
    input: float
    output: float


class ModelIn(BaseModel):
    id: str | None = None
    display_name: str
    vendor: str | None = None
    provider: str
    supports_vision: bool = False
    fixed_temperature: bool = False
    price_per_1m: Price | None = None
    endpoint: str | None = None
    endpoint_env: str | None = None
    key_env: str
    api_version_env: str | None = None
    deployment: str | None = None
    min_interval_sec: float | None = None


def _entry(body: ModelIn) -> dict:
    data = body.model_dump(exclude={"id"})
    if not data["fixed_temperature"]:
        data.pop("fixed_temperature")
    return data


@router.get("")
def list_models(pipeline: str | None = None):
    return config_store.list_models(pipeline)


@router.post("", status_code=201)
def create_model(body: ModelIn):
    return config_store.save_model(body.id or "", _entry(body), create=True)


@router.post("/{model_id:path}/test")
def test_model(model_id: str):
    entry = get_model_entry(model_id)
    t0 = time.perf_counter()
    try:
        client = build_client(model_id, entry)
        text, usage = client.generate('Reply with the JSON {"ok": true} and nothing else.')
    except Exception as exc:
        return {"ok": False, "error": str(exc), "latency_sec": round(time.perf_counter() - t0, 3)}
    return {
        "ok": True,
        "response": (text or "")[:300],
        "usage": usage,
        "latency_sec": round(time.perf_counter() - t0, 3),
    }


@router.get("/{model_id:path}")
def get_model(model_id: str):
    return config_store.get_model(model_id)


@router.put("/{model_id:path}")
def update_model(model_id: str, body: ModelIn):
    return config_store.save_model(model_id, _entry(body), create=False)


@router.delete("/{model_id:path}", status_code=204)
def delete_model(model_id: str):
    config_store.delete_model(model_id)
