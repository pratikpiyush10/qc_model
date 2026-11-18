"""API shapes for jobs, key frames, vision-analysis issues, and minimal fixes."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class FixStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class MinimalFixRequest(BaseModel):
    """Optional fields sent with the clothing reference image."""

    prompt: str = ""
    issue_id: str | None = None


class FixJob(BaseModel):
    id: str
    original_job_id: str
    status: FixStatus
    prompt: str = ""
    issue_id: str | None = None
    reference_filename: str = ""
    output_filename: str = "fixed.mp4"
    message: str = ""
    error: str | None = None
    created_at: str
    updated_at: str


class FixJobResponse(BaseModel):
    id: str
    original_job_id: str
    status: FixStatus
    prompt: str = ""
    issue_id: str | None = None
    message: str = ""
    error: str | None = None
    created_at: str
    updated_at: str
    video_ready: bool = False

    @classmethod
    def from_record(cls, record: dict, *, video_ready: bool = False) -> "FixJobResponse":
        data = dict(record)
        data["video_ready"] = video_ready
        return cls.model_validate(data)


class KeyframeOut(BaseModel):
    index: int
    frame_number: int
    timestamp_sec: float
    filename: str
    reason: str
    correlation: float | None = None


class IssueOut(BaseModel):
    id: str
    timestamp_sec: float
    timestamp_end_sec: float | None = None
    severity: str = Field(description="info, warning, or error")
    category: str = Field(description="continuity, character, or technical")
    description: str
    frame_filenames: list[str] = []


class JobOut(BaseModel):
    id: str
    filename: str
    status: str
    progress: float | None = None
    message: str
    error: str | None = None
    created_at: str
    duration_sec: float | None = None
    fps: float | None = None
    width: int | None = None
    height: int | None = None
    decoded_frames: int | None = None
    keyframe_count: int = 0
    truncated: bool = False
    limit_note: str | None = None
    analysis_status: str = "not_configured"
    keyframes: list[KeyframeOut] = []
    issues: list[IssueOut] = []

    @classmethod
    def from_record(cls, record: dict) -> "JobOut":
        data = dict(record)
        data["keyframe_count"] = len(record.get("keyframes") or [])
        return cls.model_validate(data)


class JobSummary(BaseModel):
    id: str
    filename: str
    status: str
    message: str
    created_at: str
    duration_sec: float | None = None
    keyframe_count: int = 0
    analysis_status: str = "not_configured"

    @classmethod
    def from_record(cls, record: dict) -> "JobSummary":
        return cls(
            id=record["id"],
            filename=record["filename"],
            status=record["status"],
            message=record.get("message") or "",
            created_at=record["created_at"],
            duration_sec=record.get("duration_sec"),
            keyframe_count=len(record.get("keyframes") or []),
            analysis_status=record.get("analysis_status") or "not_configured",
        )


class DirectionEvidence(BaseModel):
    show: str = ""
    episode: str = ""
    quote: str = ""


class DirectionRuleOut(BaseModel):
    id: str
    category: str
    applies_to: str = ""
    rule_text: str
    notes: str = ""
    evidence: list[DirectionEvidence] = []


class RuleOut(BaseModel):
    id: str
    category: str
    rule_text: str
    good_example: str = ""
    bad_example: str = ""


class DirectorEpisodeOut(BaseModel):
    id: str
    show: str = ""
    episode: str = ""
    title: str = ""
    version: str = ""
    has_manual: bool = False


class DirectorField(BaseModel):
    label: str
    value: str


class DirectorTable(BaseModel):
    header: list[str]
    rows: list[list[str]]


class DirectorScene(BaseModel):
    heading: str = ""
    shot_range: list[int] = []
    stated_duration_s: int | None = None
    fields: list[DirectorField] = []
    text: str = ""


class DirectorSection(BaseModel):
    key: str
    title: str
    heading: str = ""
    fields: list[DirectorField] = []
    text: str = ""
    scenes: list[DirectorScene] = []
    table: DirectorTable | None = None


class DirectorDetail(DirectorEpisodeOut):
    sections: list[DirectorSection] = []


class AppConfig(BaseModel):
    max_upload_mb: float
    max_duration_sec: int
    analysis_available: bool = False
    analysis_level: str = "high"
    vision_model: str = "google/gemini-3.8-flash"
