"""Load trimmed director's manuals from manual_dataset/episodes.jsonl."""

from __future__ import annotations

import json

from backend.app.config import settings

_SECTIONS = (
    ("s1_theme_emotional_arc", "Core theme / emotional arc", False),
    ("s2_visual_style_camera", "Visual style and camera", False),
    ("s3_narrative_structure_beats", "Pacing", True),
    ("s4_scene_intent", "Scene-by-scene intent", False),
    ("s6_transitions_continuity", "Continuity anchors", False),
)


def episodes_file():
    return settings.root / "manual_dataset" / "episodes.jsonl"


def list_director_episodes() -> list[dict]:
    return [_summary(record) for record in _load_episodes()]


def director_episode(episode_id: str) -> dict | None:
    for record in _load_episodes():
        if record.get("id") == episode_id:
            detail = _summary(record)
            detail["sections"] = _sections(record)
            return detail
    return None


def _load_episodes() -> list[dict]:
    path = episodes_file()
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    records: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict) and record.get("record_type") == "episode":
            if record.get("id"):
                records.append(record)
    return records


def _summary(record: dict) -> dict:
    manual = record.get("manual")
    return {
        "id": str(record.get("id") or ""),
        "show": str(record.get("show") or "").strip(),
        "episode": str(record.get("episode") or "").strip(),
        "title": _blank(record.get("title")),
        "version": _blank(record.get("version")),
        "has_manual": bool(record.get("has_manual")) and isinstance(manual, dict),
    }


def _sections(record: dict) -> list[dict]:
    manual = record.get("manual")
    if not isinstance(manual, dict):
        return []
    raw_sections = manual.get("sections")
    if not isinstance(raw_sections, dict):
        raw_sections = {}
    built: list[dict] = []
    for key, title, include_beats in _SECTIONS:
        raw = raw_sections.get(key)
        if not isinstance(raw, dict):
            raw = {}
        fields = _fields(raw.get("labelled_fields_derived"))
        scenes = _scenes(raw.get("scenes")) if key == "s4_scene_intent" else []
        table = _beat_table(manual.get("beat_table")) if include_beats else None
        text = ""
        if not fields and not scenes:
            text = _as_text(raw.get("text"))
        heading = _blank(raw.get("heading"))
        if not heading and not fields and not text and not scenes and table is None:
            continue
        built.append(
            {
                "key": key,
                "title": title,
                "heading": heading,
                "fields": fields,
                "text": text,
                "scenes": scenes,
                "table": table,
            }
        )
    return built


def _scenes(raw_scenes) -> list[dict]:
    if not isinstance(raw_scenes, list):
        return []
    scenes: list[dict] = []
    for raw in raw_scenes:
        if not isinstance(raw, dict):
            continue
        fields = _fields(raw.get("labelled_fields_derived"))
        shot_range = []
        for item in raw.get("shot_range") or []:
            if isinstance(item, int) and not isinstance(item, bool):
                shot_range.append(item)
        duration = raw.get("stated_duration_s")
        if isinstance(duration, bool) or not isinstance(duration, int):
            duration = None
        scenes.append(
            {
                "heading": _blank(raw.get("heading")),
                "shot_range": shot_range,
                "stated_duration_s": duration,
                "fields": fields,
                "text": "" if fields else _as_text(raw.get("text")),
            }
        )
    return scenes


def _beat_table(raw) -> dict | None:
    if not isinstance(raw, dict):
        return None
    header = [_blank(cell) for cell in raw.get("header") or [] if _blank(cell)]
    rows_in = raw.get("rows")
    if not header or not isinstance(rows_in, list):
        return None
    rows: list[list[str]] = []
    for row in rows_in:
        if isinstance(row, dict):
            rows.append([_as_text(row.get(column)) for column in header])
        elif isinstance(row, list):
            rows.append([_as_text(cell) for cell in row[: len(header)]])
    if not rows:
        return None
    return {"header": header, "rows": rows}


def _fields(raw) -> list[dict]:
    if not isinstance(raw, dict):
        return []
    fields: list[dict] = []
    for label, value in raw.items():
        text = _as_text(value)
        name = _blank(label)
        if name and text:
            fields.append({"label": name, "value": text})
    return fields


def _blank(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [_as_text(item) for item in value]
        return "\n".join(part for part in parts if part)
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            text = _as_text(item)
            if text:
                lines.append(f"{key}: {text}")
        return "\n".join(lines)
    return str(value).strip()
