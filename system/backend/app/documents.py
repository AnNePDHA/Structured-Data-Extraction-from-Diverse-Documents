"""Store uploads and render the first page to page1.png, the image every pipeline reads."""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from . import db
from .settings import UPLOAD_DIR, app_config

PAGE_IMAGE = "page1.png"


class UploadError(ValueError):
    pass


def _render_pdf(src: Path, dst: Path, dpi: int) -> int:
    import fitz

    with fitz.open(src) as pdf:
        if pdf.page_count == 0:
            raise UploadError("PDF has no pages")
        pdf[0].get_pixmap(dpi=dpi).save(dst)
        return pdf.page_count


def _render_image(src: Path, dst: Path) -> int:
    with Image.open(src) as img:
        pages = getattr(img, "n_frames", 1)
        img.seek(0)
        img.convert("RGB").save(dst, "PNG")
    return pages


def save_upload(filename: str, content: bytes, mime: str | None) -> dict:
    cfg = app_config()["upload"]
    ext = Path(filename).suffix.lower()
    if ext not in cfg["allowed_ext"]:
        raise UploadError(f"Unsupported file type {ext!r}. Allowed: {', '.join(cfg['allowed_ext'])}")
    if len(content) > cfg["max_mb"] * 1024 * 1024:
        raise UploadError(f"File is larger than {cfg['max_mb']} MB")

    doc_id = uuid.uuid4().hex[:12]
    doc_dir = UPLOAD_DIR / doc_id
    doc_dir.mkdir(parents=True)
    src = doc_dir / f"input{ext}"
    src.write_bytes(content)

    try:
        if ext == ".pdf":
            pages = _render_pdf(src, doc_dir / PAGE_IMAGE, cfg["pdf_dpi"])
        else:
            pages = _render_image(src, doc_dir / PAGE_IMAGE)
    except UploadError:
        raise
    except Exception as exc:
        raise UploadError(f"Cannot read document: {exc}") from exc

    row = {
        "id": doc_id,
        "filename": Path(filename).name,
        "mime": mime,
        "size": len(content),
        "pages": pages,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dir": str(doc_dir),
    }
    db.insert("documents", row)
    return to_public(row)


def to_public(row: dict) -> dict:
    return {
        "id": row["id"],
        "filename": row["filename"],
        "mime": row["mime"],
        "size": row["size"],
        "pages": row["pages"],
        "created_at": row["created_at"],
        "preview_url": f"/api/documents/{row['id']}/preview",
    }


def get_document(doc_id: str) -> dict:
    row = db.get("documents", doc_id)
    if row is None:
        raise FileNotFoundError(doc_id)
    return row
