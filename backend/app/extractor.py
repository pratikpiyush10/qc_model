"""Pull a small set of JPEG key frames out of an MP4.

Samples about two frames per second, keeps shot changes, and fills any gap
longer than a few seconds so a static dialogue shot is still represented.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from backend.app.config import (
    JPEG_MAX_EDGE,
    JPEG_QUALITY,
    MAX_DURATION_SEC,
    MAX_GAP_SEC,
    MAX_KEYFRAMES,
    MIN_GAP_SEC,
    SAMPLE_FPS,
    SCENE_CORR_THRESHOLD,
)

ProgressCallback = Callable[[float, str], None]

_REASON_RANK = {
    "interval": 1,
    "ending": 2,
    "opening": 3,
    "scene_change": 4,
}


@dataclass(frozen=True)
class VideoInfo:
    fps: float
    width: int
    height: int
    frame_count: int


@dataclass(frozen=True)
class Sample:
    frame_number: int
    timestamp_sec: float
    correlation: float | None


@dataclass
class ExtractionResult:
    fps: float
    width: int
    height: int
    duration_sec: float
    decoded_frames: int
    truncated: bool
    limit_note: str | None
    keyframes: list[dict]

    def as_job_fields(self) -> dict:
        return {
            "fps": self.fps,
            "width": self.width,
            "height": self.height,
            "duration_sec": self.duration_sec,
            "decoded_frames": self.decoded_frames,
            "truncated": self.truncated,
            "limit_note": self.limit_note,
            "keyframes": self.keyframes,
            "issues": [],
            "analysis_status": "not_configured",
            "error": None,
        }


def looks_like_mp4(path: Path) -> bool:
    with path.open("rb") as handle:
        header = handle.read(4096)
    return b"ftyp" in header


def probe_video(path: Path) -> VideoInfo:
    with _capture(path) as capture:
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        ok, frame = capture.read()
        if not ok or frame is None:
            raise RuntimeError("The file opened, but no video frames could be read.")
        if width <= 0 or height <= 0:
            height, width = frame.shape[:2]
        if width <= 0 or height <= 0:
            raise RuntimeError("The file opened, but no video frames could be read.")
        if fps < 1 or fps > 240:
            fps = 24.0
        return VideoInfo(
            fps=fps,
            width=width,
            height=height,
            frame_count=max(0, frame_count),
        )


def extract_keyframes(
    video_path: Path,
    output_dir: Path,
    on_progress: ProgressCallback | None = None,
) -> ExtractionResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    for old in output_dir.glob("frame_*.jpg"):
        old.unlink()

    with _capture(video_path) as capture:
        samples, meta = _scan_samples(capture, on_progress)

    selected, thinned = _select_keyframes(samples)
    keyframes = _write_selected(video_path, output_dir, samples, selected, on_progress)
    if not keyframes:
        raise RuntimeError("The video decoded, but no key frames could be saved.")

    notes: list[str] = []
    if meta["hit_duration"]:
        notes.append(f"Scanned the first {MAX_DURATION_SEC // 60} minutes.")
    if thinned:
        notes.append(f"Kept {len(keyframes)} key frames spread across the episode.")

    return ExtractionResult(
        fps=round(meta["fps"], 3),
        width=meta["width"],
        height=meta["height"],
        duration_sec=meta["duration_sec"],
        decoded_frames=meta["decoded_frames"],
        truncated=bool(notes),
        limit_note=" ".join(notes) or None,
        keyframes=keyframes,
    )


def _scan_samples(capture: cv2.VideoCapture, on_progress: ProgressCallback | None):
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
    if fps < 1 or fps > 240:
        fps = 24.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    sample_every = max(1, int(round(fps / SAMPLE_FPS)))
    max_to_read = max(1, int(math.ceil(fps * MAX_DURATION_SEC)))
    denom = min(frame_count, max_to_read) if frame_count > 0 else max_to_read

    samples: list[Sample] = []
    previous = None
    frame_number = 0
    hit_duration = False

    while True:
        if frame_number >= max_to_read:
            hit_duration = True
            break
        ok, frame = capture.read()
        if not ok or frame is None:
            break
        if width <= 0 or height <= 0:
            height, width = frame.shape[:2]
        if frame_number % sample_every == 0:
            histogram = _histogram(frame)
            correlation = None if previous is None else _correlate(previous, histogram)
            samples.append(
                Sample(
                    frame_number=frame_number,
                    timestamp_sec=round(frame_number / fps, 3),
                    correlation=correlation,
                )
            )
            previous = histogram
        frame_number += 1
        if on_progress is not None and frame_number % sample_every == 0:
            fraction = 0.7 * min(1.0, frame_number / max(denom, 1))
            on_progress(fraction, f"Reading frames · {len(samples)} samples")

    if frame_number == 0 or not samples:
        raise RuntimeError("The file opened, but no video frames could be read.")

    if hit_duration and not (frame_count == 0 or frame_count > frame_number):
        hit_duration = False

    if hit_duration and frame_count > frame_number:
        duration_sec = round(frame_count / fps, 3)
    elif frame_count > 0 and abs(frame_count - frame_number) <= max(5, int(0.02 * max(frame_number, 1))):
        duration_sec = round(frame_count / fps, 3)
    else:
        duration_sec = round(frame_number / fps, 3)

    meta = {
        "fps": fps,
        "width": width,
        "height": height,
        "duration_sec": duration_sec,
        "decoded_frames": frame_number,
        "hit_duration": hit_duration,
    }
    return samples, meta


def _select_keyframes(samples: list[Sample]) -> tuple[list[tuple[int, str]], bool]:
    if not samples:
        return [], False

    reasons: dict[int, str] = {0: "opening"}

    def consider(index: int, reason: str) -> None:
        current = reasons.get(index)
        if current is None or _REASON_RANK[reason] > _REASON_RANK[current]:
            reasons[index] = reason

    last_cut = samples[0].timestamp_sec
    for index, sample in enumerate(samples):
        if index == 0 or sample.correlation is None:
            continue
        if (
            sample.correlation < SCENE_CORR_THRESHOLD
            and sample.timestamp_sec - last_cut >= MIN_GAP_SEC
        ):
            consider(index, "scene_change")
            last_cut = sample.timestamp_sec

    consider(len(samples) - 1, "ending")
    _fill_intervals(samples, reasons)

    thinned = False
    if len(reasons) > MAX_KEYFRAMES:
        reasons = _thin(samples, reasons, MAX_KEYFRAMES)
        thinned = True

    ordered = sorted(reasons, key=lambda index: samples[index].timestamp_sec)
    return [(index, reasons[index]) for index in ordered], thinned


def _fill_intervals(samples: list[Sample], reasons: dict[int, str]) -> None:
    for _ in range(len(samples)):
        ordered = sorted(reasons)
        inserted = False
        for left, right in zip(ordered, ordered[1:]):
            start = samples[left].timestamp_sec
            end = samples[right].timestamp_sec
            if end - start <= MAX_GAP_SEC:
                continue
            target = start + MAX_GAP_SEC
            choice = None
            for index in range(left + 1, right):
                if index in reasons:
                    continue
                stamp = samples[index].timestamp_sec
                if stamp < target - 1e-6:
                    continue
                if stamp - start < MIN_GAP_SEC or end - stamp < MIN_GAP_SEC:
                    continue
                choice = index
                break
            if choice is None:
                continue
            reasons[choice] = "interval"
            inserted = True
            break
        if not inserted:
            return


def _thin(samples: list[Sample], reasons: dict[int, str], limit: int) -> dict[int, str]:
    first = 0
    last = len(samples) - 1
    keep: dict[int, str] = {first: "opening"}
    if last != first:
        keep[last] = reasons.get(last, "ending")

    budget = limit - len(keep)
    scenes = [
        index
        for index, reason in sorted(reasons.items())
        if reason == "scene_change" and index not in keep
    ]
    intervals = [
        index
        for index, reason in sorted(reasons.items())
        if reason == "interval" and index not in keep
    ]
    if len(scenes) > budget:
        chosen_scenes = _evenly(scenes, budget)
        chosen_intervals: list[int] = []
    else:
        chosen_scenes = scenes
        chosen_intervals = _evenly(intervals, budget - len(scenes))

    for index in chosen_scenes:
        keep[index] = "scene_change"
    for index in chosen_intervals:
        keep[index] = "interval"
    return keep


def _evenly(items: list[int], count: int) -> list[int]:
    if count <= 0 or not items:
        return []
    if len(items) <= count:
        return list(items)
    if count == 1:
        return [items[len(items) // 2]]
    picked: list[int] = []
    last_index = len(items) - 1
    for step in range(count):
        choice = items[round(step * last_index / (count - 1))]
        if choice not in picked:
            picked.append(choice)
    return picked


def _write_selected(
    video_path: Path,
    output_dir: Path,
    samples: list[Sample],
    selected: list[tuple[int, str]],
    on_progress: ProgressCallback | None,
) -> list[dict]:
    wanted: dict[int, tuple[Sample, str]] = {}
    for sample_index, reason in selected:
        sample = samples[sample_index]
        wanted[sample.frame_number] = (sample, reason)
    if not wanted:
        return []

    last_needed = max(wanted)
    saved: list[dict] = []
    frame_number = 0

    with _capture(video_path) as capture:
        while frame_number <= last_needed:
            ok, frame = capture.read()
            if not ok or frame is None:
                break
            chosen = wanted.get(frame_number)
            if chosen is not None:
                sample, reason = chosen
                filename = f"frame_{len(saved):04d}.jpg"
                _write_jpeg(output_dir / filename, frame)
                saved.append(
                    {
                        "index": len(saved),
                        "frame_number": sample.frame_number,
                        "timestamp_sec": sample.timestamp_sec,
                        "filename": filename,
                        "reason": reason,
                        "correlation": sample.correlation,
                    }
                )
                if on_progress is not None:
                    fraction = 0.7 + 0.29 * (len(saved) / len(wanted))
                    on_progress(fraction, f"Saving key frame {len(saved)} of {len(wanted)}")
            frame_number += 1

    return saved


def _histogram(frame: np.ndarray) -> np.ndarray:
    height, width = frame.shape[:2]
    scale = 160 / max(height, width)
    size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    small = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
    cv2.normalize(hist, hist, alpha=1.0, beta=0.0, norm_type=cv2.NORM_L1)
    return hist


def _correlate(previous: np.ndarray, current: np.ndarray) -> float:
    value = float(cv2.compareHist(previous, current, cv2.HISTCMP_CORREL))
    if value != value:
        return 0.0
    return round(max(-1.0, min(1.0, value)), 4)


def _fit(frame: np.ndarray, max_edge: int) -> np.ndarray:
    height, width = frame.shape[:2]
    long_edge = max(height, width)
    if long_edge <= max_edge:
        return frame
    scale = max_edge / long_edge
    size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    return cv2.resize(frame, size, interpolation=cv2.INTER_AREA)


def _write_jpeg(path: Path, frame: np.ndarray) -> None:
    fitted = _fit(frame, JPEG_MAX_EDGE)
    ok, encoded = cv2.imencode(
        ".jpg",
        fitted,
        [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY],
    )
    if not ok:
        raise RuntimeError("Could not encode a key frame.")
    path.write_bytes(encoded.tobytes())


@contextmanager
def _capture(path: Path):
    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise RuntimeError(
                "Could not open this MP4. Use an H.264 video in an .mp4 file."
            )
        yield capture
    finally:
        capture.release()
