"""Run key-frame extraction, then a vision pass, on a background task.

The vision pass sends key-frame JPEGs to the LiteLLM proxy and stores
continuity and character issues on the job.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
import shutil
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from backend.app.config import frames_path, settings, upload_path
from backend.app.rules import prompt_rules_block
from backend.app.extractor import extract_keyframes
from backend.app.store import store

logger = logging.getLogger("sceneqc")

_tasks: set[asyncio.Task] = set()
_CATEGORIES = {"continuity", "character", "technical"}
_SEVERITIES = {"info", "warning", "error"}
_SEVERITY_ALIASES = {
    "info": "info",
    "low": "info",
    "warning": "warning",
    "medium": "warning",
    "error": "error",
    "high": "error",
}
_DESCRIPTION_LIMIT = 350
_REQUEST_TIMEOUT_SEC = 180

_PROMPT = """You are a continuity supervisor reviewing key frames from one microdrama episode.
The images are in chronological order. Each numbered line names the file and timestamp of the image in that position.

Flag every visible continuity break, including when a cut is nearby:
- costume or hair on the same person changes, swaps, or is cleaned without that change happening on screen
- face, age, build, or identity changes, or the same person appears twice
- screen side, facing, posture, eyeline, or walking direction flips without the person moving there on screen
- a prop appears, disappears, changes hands, or changes condition without being handled on screen
- background, damage, lighting, or set dressing changes while the scene is still the same place

A cut, a new shot, or a camera move is not a reason to ignore those breaks. Do not assume a director approved the change. Report it unless these frames themselves show the action that causes it.

Do not report ordinary movement, or a wholly new location whose people and props are not continuous with the previous scene.
If nothing is wrong, return an empty issues array.

Choose severity from the visible break:
- error: identity change, a second copy of a person, eye glow, or a person missing
- warning: costume or hair change, prop change, screen position or facing, or a background or damage mismatch in the same place
- info: a small lighting or set-dressing difference that does not change the person, costume, or props

Return JSON with an "issues" array. Each issue has timestamp_sec, timestamp_end_sec, severity (info, warning, or error), category (continuity, character, or technical), description, and frame_filenames. Keep each description under 350 characters. Use only the filenames listed below.
"""


def vision_prompt() -> str:
    """Base instructions plus a short visual-rule summary."""
    block = prompt_rules_block()
    if not block:
        return _PROMPT + "\nFrames:\n"
    return _PROMPT + "\n" + block + "\n\nFrames:\n"

class AnalysisError(Exception):
    """The vision pass could not produce an issue list."""


class TransientAnalysisError(AnalysisError):
    """A network failure that is worth one retry."""


class _HttpFailure(Exception):
    def __init__(self, code: int, body: str) -> None:
        super().__init__(f"HTTP {code}")
        self.code = code
        self.body = body


def start_extraction(job_id: str) -> None:
    task = asyncio.create_task(run_extraction(job_id))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def run_extraction(job_id: str) -> None:
    store.update(job_id, status="extracting", progress=0, message="Reading video")
    video = upload_path(job_id)
    output = frames_path(job_id)
    state = {"at": 0.0, "message": ""}

    def on_progress(fraction: float, message: str) -> None:
        now = time.monotonic()
        if message == state["message"] and now - state["at"] < 0.25:
            return
        state["at"] = now
        state["message"] = message
        store.update(
            job_id,
            status="extracting",
            progress=round(min(99.0, max(0.0, fraction * 100)), 1),
            message=message,
        )

    try:
        result = await asyncio.to_thread(extract_keyframes, video, output, on_progress)
    except Exception as exc:
        logger.exception("Keyframe extraction failed for %s", job_id)
        shutil.rmtree(output, ignore_errors=True)
        store.update(
            job_id,
            status="failed",
            message="Extraction failed",
            error=_short(exc, "Extraction failed"),
        )
        return

    fields = result.as_job_fields()
    fields["analysis_status"] = "running"
    fields["issues"] = []
    fields["error"] = None
    store.update(
        job_id,
        status="analyzing",
        progress=0,
        message="Reviewing frames",
        **fields,
    )
    logger.info("Job %s saved %s key frames", job_id, len(result.keyframes))

    def on_analysis(fraction: float, message: str) -> None:
        store.update(
            job_id,
            status="analyzing",
            analysis_status="running",
            progress=round(min(99.0, max(0.0, fraction * 100)), 1),
            message=message,
        )

    try:
        issues = await asyncio.to_thread(
            analyze_keyframes,
            output,
            result.keyframes,
            api_key=settings.litellm_api_key,
            model=settings.litellm_model,
            base_url=settings.litellm_base_url,
            window=settings.litellm_window,
            overlap=settings.analysis_overlap,
            max_frames=settings.analysis_max_frames,
            image_edge=settings.analysis_image_edge,
            on_progress=on_analysis,
        )
    except AnalysisError as exc:
        logger.warning("Vision analysis failed for %s: %s", job_id, exc)
        store.update(
            job_id,
            status="ready",
            progress=100,
            message="Analysis failed",
            analysis_status="failed",
            issues=[],
            error=_short(exc, "Analysis failed"),
        )
        return
    except Exception as exc:
        logger.exception("Vision analysis failed for %s", job_id)
        store.update(
            job_id,
            status="ready",
            progress=100,
            message="Analysis failed",
            analysis_status="failed",
            issues=[],
            error=_short(exc, "Analysis failed"),
        )
        return

    sent = review_frame_count(
        result.keyframes,
        window=settings.litellm_window,
        overlap=settings.analysis_overlap,
        max_frames=settings.analysis_max_frames,
    )
    review_note = _review_note(len(result.keyframes), sent)
    limit_note = result.limit_note
    if review_note:
        limit_note = f"{limit_note} {review_note}".strip() if limit_note else review_note
    store.update(
        job_id,
        status="ready",
        progress=100,
        message="Analysis complete" if not review_note else f"Analysis complete. {review_note}",
        analysis_status="complete",
        issues=issues,
        error=None,
        limit_note=limit_note,
    )
    logger.info("Job %s analysis recorded %s issues", job_id, len(issues))


def analyze_keyframes(
    frames_dir: Path,
    keyframes: list[dict],
    *,
    api_key: str,
    model: str,
    base_url: str,
    window: int,
    overlap: int = 1,
    max_frames: int | None = None,
    image_edge: int = 960,
    on_progress: Callable[[float, str], None] | None = None,
) -> list[dict]:
    """Compare key frames through LiteLLM and return issues."""
    if not api_key.strip():
        raise AnalysisError("Set LITELLM_API_KEY to run vision analysis.")

    ordered = sorted(keyframes, key=lambda frame: float(frame["timestamp_sec"]))
    # Issues are checked against every saved frame, including ones that were not sent.
    catalog = ordered
    groups = select_review_groups(ordered, window, overlap, max_frames)
    if not groups:
        return []

    url = chat_url(base_url)
    found: list[dict] = []
    total = len(groups)
    for index, group in enumerate(groups):
        if on_progress is not None:
            on_progress(index / total, _window_message(ordered, group))
        found.extend(
            _review_window(
                frames_dir,
                catalog,
                group,
                api_key=api_key,
                model=model,
                url=url,
                image_edge=image_edge,
            )
        )
        if on_progress is not None:
            on_progress((index + 1) / total, _window_message(ordered, group))
    return finalize_issues(found)


def select_review_groups(
    frames: list[dict],
    window: int,
    overlap: int,
    max_frames: int | None,
) -> list[list[dict]]:
    """Short groups around scene changes, capped by the analysis budget."""
    ordered = list(frames)
    if len(ordered) < 2:
        return []
    scene_indexes = [
        index for index, frame in enumerate(ordered) if frame.get("reason") == "scene_change"
    ]
    if not scene_indexes:
        selected = select_analysis_frames(ordered, max_frames)
        return frame_windows(selected, window, overlap)

    size = max(2, window)
    groups: list[list[dict]] = []
    seen: set[tuple[str, ...]] = set()
    for index in scene_indexes:
        group = _centered_group(ordered, index, size)
        if len(group) < 2:
            continue
        key = tuple(str(frame["filename"]) for frame in group)
        if key in seen:
            continue
        seen.add(key)
        groups.append(group)
    if not groups:
        selected = select_analysis_frames(ordered, max_frames)
        return frame_windows(selected, window, overlap)
    return _limit_groups(groups, max_frames)


def review_frame_count(
    keyframes: list[dict],
    *,
    window: int,
    overlap: int,
    max_frames: int | None,
) -> int:
    ordered = sorted(keyframes, key=lambda frame: float(frame["timestamp_sec"]))
    return len(_unique_frames(select_review_groups(ordered, window, overlap, max_frames)))


def _centered_group(frames: list[dict], index: int, size: int) -> list[dict]:
    before = (size - 1) // 2
    start = index - before
    end = start + size
    if start < 0:
        end -= start
        start = 0
    if end > len(frames):
        start -= end - len(frames)
        end = len(frames)
    start = max(0, start)
    return list(frames[start:end])


def _unique_frames(groups: list[list[dict]]) -> list[dict]:
    frames: list[dict] = []
    names: set[str] = set()
    for group in groups:
        for frame in group:
            name = str(frame["filename"])
            if name not in names:
                names.add(name)
                frames.append(frame)
    return frames


def _limit_groups(groups: list[list[dict]], max_frames: int | None) -> list[list[dict]]:
    if max_frames is None or max_frames <= 0 or len(_unique_frames(groups)) <= max_frames:
        return groups
    if len(groups) == 1:
        return _trim_groups_to_budget(groups, max_frames)
    take = max(2, max_frames // max(2, len(groups[0])))
    picked = _spread_indexes(len(groups), take)
    last = len(groups) - 1
    if 0 not in picked:
        picked.insert(0, 0)
    if last not in picked:
        picked.append(last)
    chosen = [groups[index] for index in sorted(set(picked))]
    while len(chosen) > 2 and len(_unique_frames(chosen)) > max_frames:
        best_index = 1
        best_count: int | None = None
        for index in range(1, len(chosen) - 1):
            trial = chosen[:index] + chosen[index + 1 :]
            count = len(_unique_frames(trial))
            if best_count is None or count < best_count:
                best_count = count
                best_index = index
        chosen.pop(best_index)
    if len(_unique_frames(chosen)) <= max_frames:
        return chosen
    return _trim_groups_to_budget(chosen[:1] + chosen[-1:], max_frames)


def _spread_indexes(count: int, take: int) -> list[int]:
    if take >= count:
        return list(range(count))
    if take <= 1:
        return [0]
    indexes: list[int] = []
    last = count - 1
    for step in range(take):
        index = round(step * last / (take - 1))
        if index not in indexes:
            indexes.append(index)
    return indexes


def _trim_groups_to_budget(groups: list[list[dict]], max_frames: int) -> list[list[dict]]:
    priority: list[dict] = []
    rest: list[dict] = []
    seen: set[str] = set()
    for group in groups:
        for frame in group:
            name = str(frame["filename"])
            if name in seen:
                continue
            seen.add(name)
            if frame.get("reason") == "scene_change":
                priority.append(frame)
            else:
                rest.append(frame)
    kept_names = {str(frame["filename"]) for frame in (priority + rest)[:max_frames]}
    trimmed: list[list[dict]] = []
    for group in groups:
        group = [frame for frame in group if str(frame["filename"]) in kept_names]
        if len(group) >= 2:
            trimmed.append(group)
    if trimmed:
        return trimmed
    frames = [frame for frame in priority + rest if str(frame["filename"]) in kept_names]
    if len(frames) >= 2:
        return [frames[:max_frames]]
    return []


def select_analysis_frames(frames: list[dict], max_frames: int | None) -> list[dict]:
    """Keep a time-spread sample so the vision call stays within a token budget."""
    if max_frames is None or max_frames <= 0 or len(frames) <= max_frames:
        return list(frames)
    if max_frames == 1:
        return [frames[0]]
    chosen: list[int] = []
    last = len(frames) - 1
    for step in range(max_frames):
        index = round(step * last / (max_frames - 1))
        if index not in chosen:
            chosen.append(index)
    return [frames[index] for index in chosen]


def frame_windows(frames: list[dict], size: int, overlap: int = 1) -> list[list[dict]]:
    """Groups of frames. Overlap keeps a shared frame between neighboring groups."""
    if len(frames) < 2:
        return []
    size = max(2, size)
    if len(frames) <= size:
        return [list(frames)]
    step = max(1, size - max(0, overlap))
    windows: list[list[dict]] = []
    start = 0
    while start < len(frames):
        group = frames[start : start + size]
        if len(group) < 2:
            break
        windows.append(group)
        if start + size >= len(frames):
            break
        start += step
    return windows


def finalize_issues(issues: list[dict]) -> list[dict]:
    unique: list[dict] = []
    seen: set[tuple] = set()
    for issue in issues:
        key = (
            issue["category"],
            tuple(sorted(issue["frame_filenames"])),
            issue["description"].strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(dict(issue))
    unique.sort(key=lambda issue: (issue["timestamp_sec"], issue["description"]))
    for index, issue in enumerate(unique, start=1):
        issue["id"] = f"issue-{index}"
    return unique


def parse_model_issues(payload: dict, keyframes: list[dict]) -> list[dict]:
    """Keep model findings that match the job's issue shape."""
    by_name = {frame["filename"]: frame for frame in keyframes}
    raw_issues = payload.get("issues") if isinstance(payload, dict) else None
    if not isinstance(raw_issues, list):
        return []

    kept: list[dict] = []
    for item in raw_issues:
        parsed = _parse_issue(item, by_name)
        if parsed is not None:
            kept.append(parsed)
    return finalize_issues(kept)


def chat_url(base_url: str) -> str:
    root = base_url.strip().rstrip("/")
    if root.endswith("/chat/completions"):
        return root
    if root.endswith("/v1"):
        return root + "/chat/completions"
    return root + "/v1/chat/completions"


def unreachable_message(_base_url: str = "") -> str:
    return "Could not reach the LiteLLM endpoint."


def _review_window(
    frames_dir: Path,
    all_frames: list[dict],
    window: list[dict],
    *,
    api_key: str,
    model: str,
    url: str,
    image_edge: int,
) -> list[dict]:
    prompt = vision_prompt() + "\n".join(
        f"{position}. {frame['filename']} at {_stamp(float(frame['timestamp_sec']))}"
        for position, frame in enumerate(window, start=1)
    )
    images = [_encode_frame(frames_dir / frame["filename"], image_edge) for frame in window]
    parts: list[dict] = [{"type": "text", "text": prompt}]
    for image in images:
        parts.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image}"},
            }
        )

    def body(mode: str) -> dict:
        payload = {
            "model": model,
            "stream": False,
            "messages": [{"role": "user", "content": parts}],
        }
        if mode == "json":
            payload["response_format"] = {"type": "json_object"}
        return payload

    try:
        content = _request_content(url, body("json"), api_key)
        return _issues_from_content(content, all_frames)
    except _HttpFailure as exc:
        if exc.code != 400:
            raise AnalysisError(_http_message(exc)) from exc
        logger.info("LiteLLM rejected JSON mode; retrying without response_format")
    except AnalysisError as exc:
        if "did not return JSON" not in str(exc):
            raise
        logger.info("JSON mode response was not usable; retrying without response_format")

    try:
        content = _request_content(url, body("plain"), api_key)
    except _HttpFailure as exc:
        raise AnalysisError(_http_message(exc)) from exc
    return _issues_from_content(content, all_frames)


def _issues_from_content(content: str | dict, keyframes: list[dict]) -> list[dict]:
    if isinstance(content, dict):
        payload = content
    else:
        payload = _load_json(content)
    if not isinstance(payload.get("issues"), list):
        raise AnalysisError("LiteLLM did not return JSON.")
    return parse_model_issues(payload, keyframes)


def _request_content(url: str, body: dict, api_key: str) -> str | dict:
    last: Exception | None = None
    for attempt in range(2):
        try:
            return _post_once(url, body, api_key)
        except _HttpFailure as exc:
            logger.warning("LiteLLM HTTP %s: %s", exc.code, exc.body[:200])
            if exc.code == 400:
                raise
            last = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 1:
                raise AnalysisError(_http_message(exc)) from exc
        except TransientAnalysisError as exc:
            last = exc
            if attempt == 1:
                raise
    raise AnalysisError(unreachable_message()) from last


def _post_once(url: str, body: dict, api_key: str) -> str | dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT_SEC) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise _HttpFailure(exc.code, detail) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TransientAnalysisError(unreachable_message()) from exc

    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise AnalysisError("LiteLLM returned a response that was not JSON.") from exc
    if not isinstance(payload, dict):
        raise AnalysisError("LiteLLM returned an empty response.")
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise AnalysisError("LiteLLM returned an empty response.")
    message = choices[0].get("message")
    if not isinstance(message, dict):
        raise AnalysisError("LiteLLM returned an empty response.")
    content = _message_text(message.get("content"))
    if isinstance(content, dict):
        return content
    if isinstance(content, str) and content.strip():
        return content
    raise AnalysisError("LiteLLM returned an empty response.")


def _message_text(content: object) -> str | dict | None:
    if isinstance(content, dict):
        return content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                text = part.get("text") or part.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(part for part in parts if part.strip())
    return None


def _load_json(content: str) -> dict:
    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            raise AnalysisError("LiteLLM did not return JSON.")
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise AnalysisError("LiteLLM did not return JSON.") from exc
    if isinstance(data, list):
        return {"issues": data}
    if not isinstance(data, dict):
        raise AnalysisError("LiteLLM did not return JSON.")
    return data


def _parse_issue(item: object, by_name: dict[str, dict]) -> dict | None:
    if not isinstance(item, dict):
        return None
    description = str(item.get("description") or "").strip()
    category = str(item.get("category") or "").strip().lower()
    severity = _SEVERITY_ALIASES.get(str(item.get("severity") or "").strip().lower())
    if not description or category not in _CATEGORIES or severity is None:
        return None
    description = _limit_description(description)

    names: list[str] = []
    raw_names = item.get("frame_filenames")
    if not isinstance(raw_names, list):
        return None
    for name in raw_names:
        if isinstance(name, str) and name in by_name and name not in names:
            names.append(name)
    if not names:
        return None

    timestamp = _number(item.get("timestamp_sec"))
    if timestamp is None:
        timestamp = float(by_name[names[0]]["timestamp_sec"])
    end = _number(item.get("timestamp_end_sec"))
    if end is None and len(names) > 1:
        end = max(float(by_name[name]["timestamp_sec"]) for name in names)
    if end is not None and end < timestamp:
        timestamp, end = end, timestamp
    return {
        "timestamp_sec": round(timestamp, 3),
        "timestamp_end_sec": None if end is None else round(end, 3),
        "severity": severity,
        "category": category,
        "description": description,
        "frame_filenames": names,
    }


def _limit_description(description: str) -> str:
    if len(description) <= _DESCRIPTION_LIMIT:
        return description
    room = _DESCRIPTION_LIMIT - 3
    clipped = description[:room].rstrip()
    space = clipped.rfind(" ")
    if space >= room - 40:
        clipped = clipped[:space].rstrip()
    return clipped + "..."


def _encode_frame(path: Path, max_edge: int = 960) -> str:
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise AnalysisError("A key frame file is missing.") from exc
    if not payload:
        raise AnalysisError("A key frame file is missing.")
    payload = _shrink_jpeg(payload, max_edge)
    return base64.b64encode(payload).decode("ascii")


def _shrink_jpeg(payload: bytes, max_edge: int) -> bytes:
    if max_edge <= 0:
        return payload
    import cv2
    import numpy as np

    image = cv2.imdecode(np.frombuffer(payload, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return payload
    height, width = image.shape[:2]
    long_edge = max(height, width)
    if long_edge <= max_edge:
        return payload
    scale = max_edge / long_edge
    size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    fitted = cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    ok, encoded = cv2.imencode(".jpg", fitted, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok:
        return payload
    return encoded.tobytes()


def _review_note(saved_count: int, sent_count: int) -> str | None:
    if sent_count <= 0 or saved_count <= sent_count:
        return None
    return f"Vision review used {sent_count} of {saved_count} key frames."


def _window_message(frames: list[dict], window: list[dict]) -> str:
    start = frames.index(window[0]) + 1
    end = frames.index(window[-1]) + 1
    return f"Reviewing frames {start}–{end} of {len(frames)}"


def _stamp(seconds: float) -> str:
    total = int(round(max(0.0, seconds) * 100))
    minutes, remainder = divmod(total, 6000)
    whole, fraction = divmod(remainder, 100)
    return f"{minutes:02d}:{whole:02d}.{fraction:02d}"


def _number(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if number != number:
            return None
        return number
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _http_message(exc: _HttpFailure) -> str:
    if exc.code in {401, 403}:
        return "LiteLLM rejected the API key."
    if exc.code == 429:
        return "LiteLLM is rate limiting requests. Try this episode again later."
    if exc.code == 400:
        return "LiteLLM rejected the analysis request."
    return f"LiteLLM returned HTTP {exc.code}."


def _short(exc: Exception, fallback: str) -> str:
    detail = str(exc).strip() or fallback
    if len(detail) > 400:
        return detail[:400] + "…"
    return detail
