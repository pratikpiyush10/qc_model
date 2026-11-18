"""Background worker that asks Seedance, through LiteLLM, for a clothing fix.

The proxy video API is POST {base}/v1/videos. Seedance 2.5 video-to-video keeps
the uploaded clip when the body includes promptVideo. The clothing still goes in
references. LiteLLM drops promptImage once promptVideo selects video-to-video,
so the reference image is not sent as input_reference.
"""

from __future__ import annotations

import base64
import json
import logging
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from backend.app.config import fix_dir, fix_video_path, settings, upload_path
from backend.app.store import store

logger = logging.getLogger("sceneqc.fix")

_MAX_CLIP_SEC = 30.0
_MIN_SECONDS = 4
_MAX_SECONDS = 30
_MAX_SOURCE_BYTES = 80 * 1024 * 1024
_MAX_OUTPUT_BYTES = 150 * 1024 * 1024
_PROMPT_LIMIT = 15000
_POLL_INTERVAL_SEC = 8.0
_POLL_DEADLINE_SEC = 10 * 60
_CREATE_TIMEOUT_SEC = 300
_POLL_TIMEOUT_SEC = 60
_CONTENT_TIMEOUT_SEC = 180
_DEFAULT_PROMPT = (
    "Keep the motion, face, camera, and background. "
    "Change only the clothing to match the reference image."
)
_DONE = {"completed", "succeeded", "success"}
_FAILED = {"failed", "cancelled", "canceled", "error", "expired"}
_RETRYABLE = {429, 500, 502, 503, 504}


class FixError(Exception):
    """A clothing fix that should be stored as a short job error."""


def run_minimal_fix(fix_id: str) -> None:
    """Generate a fixed MP4 and mark the fix job completed or failed."""
    record = store.get_fix_job(fix_id)
    if record is None or record.get("status") not in {"queued", "running"}:
        return
    try:
        store.update_fix_job(
            fix_id,
            status="running",
            message="Preparing the clothing fix.",
            error=None,
        )
    except KeyError:
        logger.error("Fix job %s disappeared before it could run", fix_id)
        return

    try:
        _generate(fix_id)
    except FixError as exc:
        _fail(fix_id, str(exc))
    except Exception:
        logger.exception("Clothing fix %s failed", fix_id)
        _fail(fix_id, "The clothing fix failed.")


def videos_url(base_url: str) -> str:
    root = base_url.strip().rstrip("/")
    if root.endswith("/videos"):
        return root
    if root.endswith("/v1"):
        return root + "/videos"
    return root + "/v1/videos"


def build_seedance_body(
    *,
    model: str,
    prompt: str,
    video_path: Path,
    image_path: Path,
    seconds: int,
    size: str,
) -> dict:
    """JSON body for LiteLLM POST /v1/videos."""
    text = (prompt or "").strip() or _DEFAULT_PROMPT
    return {
        "model": model,
        "prompt": text[:_PROMPT_LIMIT],
        "promptVideo": _data_uri(video_path, "video/mp4"),
        "references": [_data_uri(image_path, _image_mime(image_path))],
        "mode": "edit",
        "seconds": seconds,
        "size": size,
    }


def _generate(fix_id: str) -> None:
    record = store.get_fix_job(fix_id)
    if record is None:
        return
    if not settings.litellm_api_key:
        raise FixError("Set LITELLM_API_KEY to run the clothing fix.")

    source = upload_path(str(record.get("original_job_id") or ""))
    reference_name = str(record.get("reference_filename") or "")
    reference = fix_dir(fix_id) / reference_name if reference_name else None
    if not source.is_file():
        raise FixError("The original video is no longer on disk.")
    if reference is None or not reference.is_file():
        raise FixError("The reference image is no longer on disk.")
    if not _looks_like_mp4(source):
        raise FixError("The original video is not a readable MP4.")

    original = store.get(str(record.get("original_job_id") or "")) or {}
    duration = _duration_sec(original, source)
    if duration is not None and duration > _MAX_CLIP_SEC:
        raise FixError("Seedance accepts clips up to 30 seconds.")
    if source.stat().st_size > _MAX_SOURCE_BYTES:
        raise FixError("The clip is too large to send to Seedance.")
    if source.stat().st_size <= 0:
        raise FixError("The original video is not a readable MP4.")

    seconds = _output_seconds(duration)
    size = _output_size(original, source)
    body = build_seedance_body(
        model=settings.seedance_model,
        prompt=str(record.get("prompt") or ""),
        video_path=source,
        image_path=reference,
        seconds=seconds,
        size=size,
    )
    store.update_fix_job(fix_id, message="Sending the clip to Seedance.")
    created = _create_video(body)
    video_id = _video_id(created)
    if not video_id:
        raise FixError("Seedance did not return a video id.")

    store.update_fix_job(fix_id, message="Seedance is generating the fixed video.")
    finished = _wait_for_video(video_id)
    video = _download_video(video_id, finished)
    if not video:
        raise FixError("Seedance did not return a video.")
    _write_video(fix_id, video)

    current = store.get_fix_job(fix_id)
    if current is None or current.get("status") == "failed":
        return
    store.update_fix_job(
        fix_id,
        status="completed",
        message="Clothing fix is ready.",
        error=None,
    )


def _fail(fix_id: str, message: str) -> None:
    text = _clean_message(message) or "The clothing fix failed."
    try:
        current = store.get_fix_job(fix_id)
    except Exception:
        logger.exception("Could not read fix job %s", fix_id)
        return
    if current is None or current.get("status") not in {"queued", "running"}:
        return
    store.update_fix_job(fix_id, status="failed", message="Fix failed", error=text)


def _duration_sec(original: dict, source: Path) -> float | None:
    raw = original.get("duration_sec")
    if isinstance(raw, (int, float)) and raw > 0:
        return float(raw)
    return _probe_duration(source)


def _probe_duration(source: Path) -> float | None:
    try:
        import cv2
    except ImportError:
        return None
    capture = cv2.VideoCapture(str(source))
    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
        frames = float(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    finally:
        capture.release()
    if fps > 0 and frames > 0:
        return frames / fps
    return None


def _output_seconds(duration: float | None) -> int:
    if duration is None:
        return 5
    return max(_MIN_SECONDS, min(_MAX_SECONDS, int(round(duration))))


def _output_size(original: dict, source: Path) -> str:
    width = original.get("width")
    height = original.get("height")
    if not isinstance(width, int) or not isinstance(height, int) or width <= 0 or height <= 0:
        probed = _probe_size(source)
        width, height = probed if probed is not None else (1280, 720)
    if height > width:
        return "720x1280"
    return "1280x720"


def _probe_size(source: Path) -> tuple[int, int] | None:
    try:
        import cv2
    except ImportError:
        return None
    capture = cv2.VideoCapture(str(source))
    try:
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    finally:
        capture.release()
    if width > 0 and height > 0:
        return width, height
    return None


def _create_video(body: dict) -> dict:
    url = videos_url(settings.litellm_base_url)
    last: Exception | None = None
    for attempt in range(2):
        try:
            return _request_json("POST", url, body, _CREATE_TIMEOUT_SEC)
        except _HttpFailure as exc:
            logger.warning("Seedance create HTTP %s", exc.code)
            if exc.code not in _RETRYABLE or attempt == 1:
                raise FixError(_http_message(exc)) from exc
            last = exc
        except _TransportError as exc:
            last = exc
            if attempt == 1:
                raise FixError("Could not reach the LiteLLM endpoint.") from exc
    raise FixError("Could not reach the LiteLLM endpoint.") from last


def _wait_for_video(video_id: str) -> dict:
    url = f"{videos_url(settings.litellm_base_url)}/{_quote(video_id)}"
    deadline = time.monotonic() + _POLL_DEADLINE_SEC
    transport_failures = 0
    while True:
        try:
            payload = _request_json("GET", url, None, _POLL_TIMEOUT_SEC)
            transport_failures = 0
        except _HttpFailure as exc:
            raise FixError(_http_message(exc)) from exc
        except _TransportError as exc:
            transport_failures += 1
            if transport_failures >= 3:
                raise FixError("Could not reach the LiteLLM endpoint.") from exc
            payload = {}
        status = _status(payload)
        if status in _DONE:
            return payload
        if status in _FAILED:
            raise FixError(_provider_error(payload) or "Seedance did not return a video.")
        if time.monotonic() >= deadline:
            raise FixError("Seedance did not finish in time.")
        time.sleep(_POLL_INTERVAL_SEC)


def _download_video(video_id: str, finished: dict) -> bytes:
    url = f"{videos_url(settings.litellm_base_url)}/{_quote(video_id)}/content"
    try:
        kind, payload = _request_bytes("GET", url, _CONTENT_TIMEOUT_SEC)
    except _HttpFailure as exc:
        if exc.code == 404:
            kind, payload = "json", finished
        else:
            raise FixError(_http_message(exc)) from exc
    except _TransportError as exc:
        raise FixError("Could not reach the LiteLLM endpoint.") from exc

    if kind == "video":
        return payload if isinstance(payload, bytes) else b""
    if isinstance(payload, dict):
        for remote in _output_urls(payload):
            try:
                remote_kind, remote_payload = _request_bytes("GET", remote, _CONTENT_TIMEOUT_SEC, auth=False)
            except (_HttpFailure, _TransportError) as exc:
                logger.warning("Could not download Seedance output: %s", type(exc).__name__)
                continue
            if remote_kind == "video" and isinstance(remote_payload, bytes):
                return remote_payload
    return b""


def _write_video(fix_id: str, video: bytes) -> None:
    if not video or b"ftyp" not in video[:64]:
        raise FixError("Seedance did not return a video.")
    if len(video) > _MAX_OUTPUT_BYTES:
        raise FixError("The generated video is too large to save.")
    target = fix_video_path(fix_id)
    partial = target.with_name("fixed.mp4.part")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        partial.write_bytes(video)
        partial.replace(target)
    except OSError as exc:
        logger.exception("Could not write the fixed video for %s", fix_id)
        raise FixError("Could not write the fixed video.") from exc
    if not target.is_file() or target.stat().st_size <= 0:
        raise FixError("Could not write the fixed video.")


def _request_json(method: str, url: str, body: dict | None, timeout: float) -> dict:
    kind, payload = _request_bytes(method, url, timeout, body=body)
    if kind != "json" or not isinstance(payload, dict):
        raise FixError("LiteLLM returned a response that was not JSON.")
    return payload


def _request_bytes(
    method: str,
    url: str,
    timeout: float,
    body: dict | None = None,
    *,
    auth: bool = True,
):
    headers = {"Accept": "application/json, video/mp4"}
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if auth:
        headers["Authorization"] = f"Bearer {settings.litellm_api_key}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(_MAX_OUTPUT_BYTES + 1)
            content_type = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        detail = exc.read(8000).decode("utf-8", errors="replace")
        raise _HttpFailure(exc.code, detail) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise _TransportError("Could not reach the LiteLLM endpoint.") from exc

    if len(raw) > _MAX_OUTPUT_BYTES:
        raise FixError("The generated video is too large to save.")
    return _interpret(raw, content_type)


def _interpret(raw: bytes, content_type: str):
    lowered = content_type.lower()
    if "video/" in lowered or "octet-stream" in lowered or b"ftyp" in raw[:64]:
        return "video", raw
    if "json" in lowered or raw[:1] in {b"{", b"["}:
        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise FixError("LiteLLM returned a response that was not JSON.") from exc
        if isinstance(payload, dict):
            return "json", payload
        raise FixError("LiteLLM returned a response that was not JSON.")
    if raw:
        return "video", raw
    return "video", b""


def _http_message(exc: "_HttpFailure") -> str:
    if exc.code in {401, 403}:
        return "LiteLLM rejected the API key."
    text = _error_text(exc.body)
    if text:
        return text
    if exc.code == 400:
        return "Seedance rejected the clothing fix request."
    return "The clothing fix request failed."


def _error_text(body: str) -> str:
    stripped = body.strip()
    if not stripped or "<html" in stripped.lower() or stripped.startswith("<"):
        return ""
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        return _provider_error(payload)
    return _clean_message(stripped)


def _provider_error(payload: dict) -> str:
    found = _dig_error(payload.get("error"))
    if not found:
        found = _dig_error(payload.get("failure") or payload.get("failure_reason") or payload.get("message"))
    return _clean_message(found)


def _dig_error(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("message", "detail", "error", "failure"):
            text = _dig_error(value.get(key))
            if text:
                return text
    if isinstance(value, list):
        parts = [_dig_error(item) for item in value]
        return " ".join(part for part in parts if part)
    return ""


def _clean_message(value: str) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if not text or "<html" in text.lower():
        return ""
    if len(text) > 180:
        text = text[:177].rstrip() + "..."
    return text


def _status(payload: dict) -> str:
    raw = payload.get("status")
    if not isinstance(raw, str):
        data = payload.get("data")
        if isinstance(data, dict) and isinstance(data.get("status"), str):
            raw = data["status"]
        else:
            return ""
    return raw.strip().lower().replace("-", "_")


def _video_id(payload: dict) -> str:
    for key in ("id", "video_id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("video", "data"):
        nested = payload.get(key)
        if isinstance(nested, dict):
            found = _video_id(nested)
            if found:
                return found
    return ""


def _output_urls(payload: dict) -> list[str]:
    urls: list[str] = []
    for key in ("output", "output_url", "url", "video_url"):
        _collect_urls(payload.get(key), urls)
    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("output", "output_url", "url", "video_url"):
            _collect_urls(data.get(key), urls)
    return urls


def _collect_urls(value: object, urls: list[str]) -> None:
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        urls.append(value)
    elif isinstance(value, list):
        for item in value:
            _collect_urls(item, urls)
    elif isinstance(value, dict):
        for key in ("url", "output", "output_url"):
            _collect_urls(value.get(key), urls)


def _quote(video_id: str) -> str:
    from urllib.parse import quote

    return quote(video_id, safe="")


def _data_uri(path: Path, mime: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _image_mime(path: Path) -> str:
    with path.open("rb") as handle:
        header = handle.read(16)
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp"
    raise FixError("The reference image is not a JPEG, PNG, or WebP file.")


def _looks_like_mp4(path: Path) -> bool:
    with path.open("rb") as handle:
        return b"ftyp" in handle.read(32)


class _HttpFailure(Exception):
    def __init__(self, code: int, body: str):
        super().__init__(code)
        self.code = code
        self.body = body


class _TransportError(Exception):
    pass
