"""Paths and frame-extraction settings for the local Scene QC app."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


# Candidate frames are taken at this rate, then thinned to scene changes and coverage.
SAMPLE_FPS = 2.0
# Histogram correlation below this, versus the previous sample, counts as a new shot.
SCENE_CORR_THRESHOLD = 0.72
MIN_GAP_SEC = 0.25
MAX_GAP_SEC = 3.0
MAX_KEYFRAMES = 80
JPEG_MAX_EDGE = 960
JPEG_QUALITY = 85
MAX_DURATION_SEC = 20 * 60
DEFAULT_LITELLM_MODEL = "google/gemini-3.8-flash"
DEFAULT_SEEDANCE_MODEL = "runwayml/seedance2_5"
DEFAULT_LITELLM_BASE_URL = "https://litellm.kukufm.com"
DEFAULT_ANALYSIS_LEVEL = "high"
# How many frames are sent, how they are grouped, and how small the images are.
# The results page still shows every saved key frame.
ANALYSIS_LEVELS = {
    "low": {"max_frames": 6, "window": 2, "overlap": 0, "image_edge": 384},
    "medium": {"max_frames": 40, "window": 4, "overlap": 1, "image_edge": 768},
    "high": {"max_frames": 80, "window": 4, "overlap": 1, "image_edge": 960},
}


@dataclass(frozen=True)
class Settings:
    root: Path
    data_dir: Path
    upload_dir: Path
    frames_dir: Path
    jobs_dir: Path
    fixes_dir: Path
    frontend_dir: Path
    max_upload_bytes: int
    max_upload_mb: float
    litellm_api_key: str
    litellm_model: str
    seedance_model: str
    litellm_base_url: str
    litellm_window: int
    analysis_level: str
    analysis_max_frames: int
    analysis_overlap: int
    analysis_image_edge: int


def _max_upload_mb() -> float:
    raw = os.environ.get("QC_MAX_UPLOAD_MB", "400")
    try:
        value = float(raw)
    except ValueError:
        return 400.0
    if value <= 0:
        return 400.0
    return value


def _analysis_level() -> str:
    raw = os.environ.get("QC_ANALYSIS_LEVEL", DEFAULT_ANALYSIS_LEVEL).strip().lower()
    if raw not in ANALYSIS_LEVELS:
        return DEFAULT_ANALYSIS_LEVEL
    return raw


def _optional_int(name: str, minimum: int) -> int | None:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    if value < minimum:
        return None
    return value


def _load_dotenv(path: Path) -> None:
    """Fill unset environment variables from a local .env file."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


def load_settings() -> Settings:
    root = Path(__file__).resolve().parents[2]
    _load_dotenv(root / ".env")
    data_dir = Path(os.environ.get("QC_DATA_DIR", root / "data")).expanduser()
    max_mb = _max_upload_mb()
    model = os.environ.get("QC_LITELLM_MODEL", DEFAULT_LITELLM_MODEL).strip()
    seedance = os.environ.get("QC_SEEDANCE_MODEL", DEFAULT_SEEDANCE_MODEL).strip()
    base_url = os.environ.get("QC_LITELLM_BASE_URL", DEFAULT_LITELLM_BASE_URL).strip()
    level = _analysis_level()
    preset = ANALYSIS_LEVELS[level]
    window = _optional_int("QC_LITELLM_WINDOW", 2)
    max_frames = _optional_int("QC_LITELLM_MAX_FRAMES", 2)
    image_edge = _optional_int("QC_LITELLM_IMAGE_EDGE", 128)
    settings = Settings(
        root=root,
        data_dir=data_dir,
        upload_dir=data_dir / "uploads",
        frames_dir=data_dir / "frames",
        jobs_dir=data_dir / "jobs",
        fixes_dir=data_dir / "fixes",
        frontend_dir=root / "frontend",
        max_upload_bytes=int(max_mb * 1024 * 1024),
        max_upload_mb=max_mb,
        litellm_api_key=os.environ.get("LITELLM_API_KEY", "").strip(),
        litellm_model=model or DEFAULT_LITELLM_MODEL,
        seedance_model=seedance or DEFAULT_SEEDANCE_MODEL,
        litellm_base_url=base_url or DEFAULT_LITELLM_BASE_URL,
        litellm_window=window if window is not None else preset["window"],
        analysis_level=level,
        analysis_max_frames=max_frames if max_frames is not None else preset["max_frames"],
        analysis_overlap=preset["overlap"],
        analysis_image_edge=image_edge if image_edge is not None else preset["image_edge"],
    )
    for path in (settings.upload_dir, settings.frames_dir, settings.jobs_dir, settings.fixes_dir):
        path.mkdir(parents=True, exist_ok=True)
    return settings


settings = load_settings()
FIXES_DIR = settings.fixes_dir


def upload_path(job_id: str) -> Path:
    return settings.upload_dir / job_id / "source.mp4"


def frames_path(job_id: str) -> Path:
    return settings.frames_dir / job_id


def fix_dir(fix_id: str) -> Path:
    return settings.fixes_dir / fix_id


def fix_video_path(fix_id: str) -> Path:
    return fix_dir(fix_id) / "fixed.mp4"
