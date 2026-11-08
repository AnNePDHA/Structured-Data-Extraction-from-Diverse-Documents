"""Schemas, prompt templates, pipelines and OCR engines: all backed by files in config/."""

from fastapi import APIRouter
from pydantic import BaseModel

from .. import config_store
from ..settings import app_config

from pipelines.model_clients import PROVIDERS

router = APIRouter(tags=["config"])


@router.get("/providers")
def list_providers():
    return list(PROVIDERS)


class SchemaIn(BaseModel):
    key: str | None = None
    fields: dict


class PromptIn(BaseModel):
    text: str


@router.get("/pipelines")
def list_pipelines():
    return [{"id": k, **v} for k, v in app_config()["pipelines"].items()]


@router.get("/schemas")
def list_schemas():
    return config_store.list_schemas()


@router.get("/schemas/{key}")
def get_schema(key: str):
    return config_store.get_schema(key)


@router.post("/schemas", status_code=201)
def create_schema(body: SchemaIn):
    if not body.key:
        raise config_store.ConfigError("key is required")
    return config_store.save_schema(body.key, body.fields, create=True)


@router.put("/schemas/{key}")
def update_schema(key: str, body: SchemaIn):
    return config_store.save_schema(key, body.fields, create=False)


@router.delete("/schemas/{key}", status_code=204)
def delete_schema(key: str):
    config_store.delete_schema(key)


@router.get("/prompts")
def list_prompts():
    return config_store.list_prompts()


@router.get("/prompts/{name}")
def get_prompt(name: str):
    return {"name": name, "text": config_store.get_prompt(name)}


@router.put("/prompts/{name}")
def save_prompt(name: str, body: PromptIn):
    config_store.save_prompt(name, body.text)
    return {"name": name, "text": body.text}


@router.get("/ocr-engines")
def list_ocr_engines():
    return config_store.list_ocr_engines()
