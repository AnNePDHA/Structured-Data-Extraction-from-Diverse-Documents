import mimetypes
from pathlib import Path

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse

from .. import documents
from ..settings import ROOT, app_config

router = APIRouter(prefix="/documents", tags=["documents"])


def _samples() -> list[dict]:
    return [s for s in app_config().get("samples", []) if (ROOT / s["path"]).exists()]


@router.get("/samples")
def list_samples():
    return [{k: v for k, v in s.items() if k != "path"} for s in _samples()]


@router.post("/samples/{sample_id}")
def use_sample(sample_id: str):
    sample = next((s for s in _samples() if s["id"] == sample_id), None)
    if sample is None:
        raise FileNotFoundError(sample_id)
    path = ROOT / sample["path"]
    doc = documents.save_upload(path.name, path.read_bytes(), mimetypes.guess_type(path.name)[0])
    return {**doc, "suggested_schema": sample.get("schema")}


@router.post("")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    return documents.save_upload(file.filename or "document", content, file.content_type)


@router.get("/{doc_id}")
def get_document(doc_id: str):
    return documents.to_public(documents.get_document(doc_id))


@router.get("/{doc_id}/preview")
def preview(doc_id: str):
    row = documents.get_document(doc_id)
    return FileResponse(Path(row["dir"]) / documents.PAGE_IMAGE, media_type="image/png")
