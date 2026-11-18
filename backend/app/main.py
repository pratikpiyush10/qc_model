"""Scene QC local server: upload an MP4, extract key frames, review them."""

from __future__ import annotations

import asyncio
import re
import shutil
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response

from backend.app.config import (
    MAX_DURATION_SEC,
    fix_dir,
    fix_video_path,
    frames_path,
    settings,
    upload_path,
)
from backend.app.extractor import looks_like_mp4, probe_video
from backend.app.direction import load_direction_rules
from backend.app.director import director_episode, list_director_episodes
from backend.app.fix_pipeline import run_minimal_fix
from backend.app.pipeline import start_extraction
from backend.app.rules import load_rules
from backend.app.schemas import (
    AppConfig,
    DirectionRuleOut,
    DirectorDetail,
    DirectorEpisodeOut,
    FixJobResponse,
    JobOut,
    JobSummary,
    MinimalFixRequest,
    RuleOut,
)
from backend.app.store import new_record, store

_JOB_ID = re.compile(r"^[a-f0-9]{12}$")
_FRAME_NAME = re.compile(r"^frame_\d{4}\.jpg$")
_EPISODE_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_MAX_REFERENCE_BYTES = 20 * 1024 * 1024

router = APIRouter(prefix="/api")


class FreshStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


def _job_id_or_404(job_id: str) -> str:
    if not _JOB_ID.fullmatch(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return job_id


def _job_or_404(job_id: str) -> dict:
    job = store.get(_job_id_or_404(job_id))
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/direction", response_model=list[DirectionRuleOut])
def list_direction() -> list[DirectionRuleOut]:
    return [DirectionRuleOut.model_validate(rule) for rule in load_direction_rules()]


@router.get("/director", response_model=list[DirectorEpisodeOut])
def list_director() -> list[DirectorEpisodeOut]:
    return [DirectorEpisodeOut.model_validate(item) for item in list_director_episodes()]


@router.get("/director/{episode_id}", response_model=DirectorDetail)
def get_director(episode_id: str) -> DirectorDetail:
    if not _EPISODE_ID.fullmatch(episode_id):
        raise HTTPException(status_code=404, detail="Episode not found")
    episode = director_episode(episode_id)
    if episode is None:
        raise HTTPException(status_code=404, detail="Episode not found")
    return DirectorDetail.model_validate(episode)


@router.get("/rules", response_model=list[RuleOut])
def list_rules() -> list[RuleOut]:
    return [RuleOut.model_validate(rule) for rule in load_rules()]


@router.get("/config", response_model=AppConfig)
def app_config() -> AppConfig:
    return AppConfig(
        max_upload_mb=settings.max_upload_mb,
        max_duration_sec=MAX_DURATION_SEC,
        analysis_available=bool(settings.litellm_api_key),
        analysis_level=settings.analysis_level,
        vision_model=settings.litellm_model,
    )


@router.get("/jobs", response_model=list[JobSummary])
def list_jobs() -> list[JobSummary]:
    return [JobSummary.from_record(job) for job in store.list_jobs()]


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str) -> JobOut:
    return JobOut.from_record(_job_or_404(job_id))


def _fix_or_404(fix_id: str) -> dict:
    if not _JOB_ID.fullmatch(fix_id):
        raise HTTPException(status_code=404, detail="Fix not found")
    job = store.get_fix_job(fix_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Fix not found")
    return job


def _fix_response(record: dict) -> FixJobResponse:
    path = fix_video_path(record["id"])
    ready = record.get("status") == "completed" and path.is_file()
    return FixJobResponse.from_record(record, video_ready=ready)


@router.post("/jobs/{job_id}/minimal-fix", response_model=FixJobResponse, status_code=201)
async def create_minimal_fix(
    job_id: str,
    background: BackgroundTasks,
    reference_image: UploadFile = File(...),
    prompt: str = Form(""),
    issue_id: str | None = Form(None),
) -> FixJobResponse:
    job = _job_or_404(job_id)
    if not upload_path(job_id).is_file():
        raise HTTPException(status_code=400, detail="The original video is no longer on disk.")
    cleaned_issue = (issue_id or "").strip() or None
    request = MinimalFixRequest(prompt=prompt.strip(), issue_id=cleaned_issue)
    if request.issue_id:
        known = {str(issue.get("id")) for issue in job.get("issues") or [] if isinstance(issue, dict)}
        if request.issue_id not in known:
            raise HTTPException(status_code=400, detail="That issue is not on this job.")

    fix_id = uuid.uuid4().hex[:12]
    directory = fix_dir(fix_id)
    directory.mkdir(parents=True, exist_ok=True)
    try:
        reference_name = await _save_reference(reference_image, directory)
    except HTTPException:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    except OSError as exc:
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(status_code=400, detail="Could not save the reference image.") from exc

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record = store.create_fix_job(
        {
            "id": fix_id,
            "original_job_id": job_id,
            "status": "queued",
            "prompt": request.prompt,
            "issue_id": request.issue_id,
            "reference_filename": reference_name,
            "output_filename": "fixed.mp4",
            "message": "Waiting to apply the clothing fix",
            "error": None,
            "created_at": now,
            "updated_at": now,
        }
    )
    background.add_task(run_minimal_fix, fix_id)
    return _fix_response(record)


@router.get("/fix-jobs/{fix_id}", response_model=FixJobResponse)
def get_fix_job(fix_id: str) -> FixJobResponse:
    return _fix_response(_fix_or_404(fix_id))


@router.get("/fix-jobs/{fix_id}/video")
def get_fix_video(fix_id: str) -> FileResponse:
    job = _fix_or_404(fix_id)
    path = fix_video_path(fix_id)
    if job.get("status") != "completed" or not path.is_file():
        raise HTTPException(status_code=404, detail="Fix video is not ready.")
    return FileResponse(path, media_type="video/mp4", filename="fixed.mp4")


@router.get("/jobs/{job_id}/fixes", response_model=list[FixJobResponse])
def list_job_fixes(job_id: str) -> list[FixJobResponse]:
    _job_or_404(job_id)
    return [_fix_response(job) for job in store.list_fix_jobs_for_original(job_id)]


@router.get("/jobs/{job_id}/video")
def get_source_video(job_id: str) -> FileResponse:
    job = _job_or_404(job_id)
    path = upload_path(job_id)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=str(job.get("filename") or "source.mp4"),
    )


@router.get("/jobs/{job_id}/frames/{filename}")
def get_frame(job_id: str, filename: str) -> FileResponse:
    _job_or_404(job_id)
    if not _FRAME_NAME.fullmatch(filename):
        raise HTTPException(status_code=404, detail="Frame not found")
    path = frames_path(job_id) / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(
        path,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.post("/jobs", response_model=JobOut, status_code=201)
async def create_job(file: UploadFile = File(...)) -> JobOut:
    filename = Path(file.filename or "").name
    if not filename or Path(filename).suffix.lower() != ".mp4":
        raise HTTPException(status_code=400, detail="Choose an .mp4 video.")

    job_id = uuid.uuid4().hex[:12]
    destination = upload_path(job_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        size = await _save_upload(file, destination)
        if size == 0 or not looks_like_mp4(destination):
            raise HTTPException(status_code=400, detail="That file is not a readable MP4 video.")
        info = await asyncio.to_thread(probe_video, destination)
    except HTTPException:
        shutil.rmtree(destination.parent, ignore_errors=True)
        raise
    except RuntimeError as exc:
        shutil.rmtree(destination.parent, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        shutil.rmtree(destination.parent, ignore_errors=True)
        raise HTTPException(
            status_code=400,
            detail="Could not save the video. Check that the disk has free space.",
        ) from exc

    duration = round(info.frame_count / info.fps, 3) if info.frame_count else None
    record = new_record(
        job_id,
        filename,
        fps=round(info.fps, 3),
        width=info.width,
        height=info.height,
        duration_sec=duration,
    )
    store.create(record)
    return JobOut.from_record(store.get(job_id) or record)


@router.post("/jobs/{job_id}/start", response_model=JobOut)
def start_job(job_id: str) -> JobOut:
    """Start key-frame extraction and the vision pass. A saved job stays queued until this."""
    _job_or_404(job_id)
    if store.claim_for_extraction(job_id):
        start_extraction(job_id)
    return JobOut.from_record(store.get(job_id) or _job_or_404(job_id))


def _reference_suffix(header: bytes) -> str | None:
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if len(header) >= 12 and header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return ".webp"
    return None


async def _save_reference(file: UploadFile, directory: Path) -> str:
    size = 0
    chunks: list[bytes] = []
    try:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > _MAX_REFERENCE_BYTES:
                raise HTTPException(status_code=413, detail="Reference image is larger than 20 MB.")
            chunks.append(chunk)
    finally:
        await file.close()
    data = b"".join(chunks)
    suffix = _reference_suffix(data[:16])
    if not data or suffix is None:
        raise HTTPException(status_code=400, detail="Choose a JPEG, PNG, or WebP reference image.")
    name = f"reference{suffix}"
    (directory / name).write_bytes(data)
    return name


async def _save_upload(file: UploadFile, destination: Path) -> int:
    size = 0
    try:
        with destination.open("wb") as handle:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Video is larger than {settings.max_upload_mb:g} MB.",
                    )
                handle.write(chunk)
    finally:
        await file.close()
    return size


@asynccontextmanager
async def _lifespan(app: FastAPI):
    store.mark_interrupted()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Scene QC", version="0.1.0", lifespan=_lifespan)
    app.include_router(router)

    @app.middleware("http")
    async def nosniff(request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    app.mount(
        "/",
        FreshStaticFiles(directory=str(settings.frontend_dir), html=True),
        name="frontend",
    )
    return app


app = create_app()
