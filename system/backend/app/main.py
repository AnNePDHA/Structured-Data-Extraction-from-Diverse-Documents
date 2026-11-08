"""DocuExtract API. Run from the repo root: uvicorn system.backend.app.main:app --reload"""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .settings import ROOT
from . import db
from .config_store import ConfigError
from .documents import UploadError
from .routers import config, documents, jobs, models
from .runner import JobError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="DocuExtract API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(FileNotFoundError)
def not_found(_: Request, exc: FileNotFoundError):
    return JSONResponse(status_code=404, content={"detail": f"Not found: {exc}"})


@app.exception_handler(ConfigError)
@app.exception_handler(UploadError)
@app.exception_handler(JobError)
@app.exception_handler(ValueError)
@app.exception_handler(json.JSONDecodeError)
def bad_request(_: Request, exc: Exception):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


for r in (documents.router, config.router, models.router, jobs.router):
    app.include_router(r, prefix="/api")


@app.get("/api/health")
def health():
    return {"ok": True}


# Built frontend (npm run build) is served from the same port, so one process is enough for the demo
_dist = ROOT / "system" / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
