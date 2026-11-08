from fastapi import APIRouter
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from .. import runner
from ..documents import PAGE_IMAGE

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobIn(BaseModel):
    document_id: str
    pipeline: str
    model_id: str
    schema_key: str | None = None
    fields: dict | None = None
    ocr_engine_id: str | None = None
    prompt: str | None = None


class FieldsIn(BaseModel):
    fields: dict


@router.post("", status_code=202)
def create_job(body: JobIn):
    return runner.create_job(body.model_dump())


@router.get("")
def list_jobs(limit: int = 20, offset: int = 0):
    return runner.list_jobs(min(limit, 200), offset)


@router.get("/{job_id}")
def get_job(job_id: str):
    return runner.get_job(job_id)


@router.get("/{job_id}/preview")
def preview(job_id: str):
    return FileResponse(runner.job_file(job_id, PAGE_IMAGE), media_type="image/png")


@router.get("/{job_id}/files/{name}")
def artifact(job_id: str, name: str):
    if name not in runner.TEXT_ARTIFACTS:
        raise FileNotFoundError(name)
    path = runner.job_file(job_id, name)
    if not path.exists():
        raise FileNotFoundError(name)
    return Response(path.read_text(encoding="utf-8"), media_type="text/plain; charset=utf-8")


@router.patch("/{job_id}/fields")
def save_fields(job_id: str, body: FieldsIn):
    return runner.save_edits(job_id, body.fields)


@router.get("/{job_id}/export")
def export(job_id: str, format: str = "json"):
    if format == "csv":
        return Response(
            runner.export_csv(job_id),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{job_id}.csv"'},
        )
    return Response(
        runner.export_json(job_id),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{job_id}.json"'},
    )


@router.get("/{job_id}/bundle")
def bundle(job_id: str):
    return Response(
        runner.export_bundle(job_id),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="job_{job_id}.zip"'},
    )


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str):
    runner.delete_job(job_id)
