"""Small JSON job store. One file per job, safe to read from the extractor thread."""

from __future__ import annotations

import copy
import json
import threading
from datetime import datetime, timezone
from typing import Any

from backend.app.config import settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_record(
    job_id: str,
    filename: str,
    *,
    fps: float,
    width: int,
    height: int,
    duration_sec: float | None,
) -> dict[str, Any]:
    return {
        "id": job_id,
        "filename": filename,
        "status": "queued",
        "progress": 0,
        "message": "Waiting to read frames",
        "error": None,
        "created_at": _now(),
        "duration_sec": duration_sec,
        "fps": fps,
        "width": width,
        "height": height,
        "decoded_frames": None,
        "truncated": False,
        "limit_note": None,
        "analysis_status": "not_configured",
        "keyframes": [],
        "issues": [],
    }


class JobStore:
    def __init__(self) -> None:
        self._dir = settings.jobs_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._load()

    def _path(self, job_id: str):
        return self._dir / f"{job_id}.json"

    def _load(self) -> None:
        for path in self._dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and isinstance(data.get("id"), str):
                self._jobs[data["id"]] = data

    def _write(self, job: dict[str, Any]) -> None:
        path = self._path(job["id"])
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(job, indent=2), encoding="utf-8")
        temporary.replace(path)

    def create(self, record: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._jobs[record["id"]] = record
            self._write(record)
            return copy.deepcopy(record)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return None if job is None else copy.deepcopy(job)

    def update(self, job_id: str, **fields: Any) -> dict[str, Any]:
        with self._lock:
            job = self._jobs[job_id]
            job.update(fields)
            self._write(job)
            return copy.deepcopy(job)

    def list_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            jobs = [copy.deepcopy(job) for job in self._jobs.values()]
        jobs.sort(key=lambda job: job.get("created_at") or "", reverse=True)
        return jobs[:limit]

    def mark_interrupted(self) -> None:
        with self._lock:
            for job in self._jobs.values():
                status = job.get("status")
                if status not in {"queued", "extracting", "analyzing"}:
                    continue
                job["status"] = "failed"
                if status == "analyzing":
                    job["analysis_status"] = "failed"
                    job["message"] = "Analysis interrupted"
                    job["error"] = (
                        "Analysis stopped because the server restarted. Upload the video again."
                    )
                else:
                    job["message"] = "Extraction interrupted"
                    job["error"] = (
                        "Extraction stopped because the server restarted. Upload the video again."
                    )
                self._write(job)


store = JobStore()
