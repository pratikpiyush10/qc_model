#!/usr/bin/env python3
"""Convert continuity dataset records into chat fine-tuning JSONL.

Usage:
  python3 convert_to_chat.py
  python3 convert_to_chat.py --in-dir /workspace/continuity_dataset --out train_chat.jsonl

Reads uw_continuity.jsonl, rules.jsonl, and template_new_show.jsonl in --in-dir.
Skips records with is_example_template=true (templates are for authors, not training).
Writes one {"messages":[system, user, assistant]} object per remaining record.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SYSTEM = (
    "You are a video-continuity specialist for AI-generated episodic video. "
    "Dialogue must be copied verbatim. Do not change shot types, shot order, or framing unless the user asks. "
    "On-screen written text must be in the script's required script (for Hindi shows, visible text is Hindi Devanagari only). "
    "Lock every character's position, facing, posture and movement in every shot, carrying the previous track's end state forward. "
    "The location must match the named reference asset used as the background plate; do not mix conflicting location refs. "
    "Characters keep their established walking direction (no unexplained U-turns). "
    "Damaged locations, costumes and props stay damaged until a later approved beat changes them. "
    "No eye glow (natural eyes with real catchlights only, unless a source explicitly records an approved exception). "
    "Put continuity changes inside the shot text itself, not as override notes appended at the end. "
    "QC every generation. If a fact is unknown, say null; never invent."
)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"Invalid JSONL in {path} line {line_no}: {e}") from e
    return rows


def dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def from_continuity_state(rec: dict) -> tuple[str, str]:
    user = (
        "Produce a structured end-of-track (or requested-moment) continuity state "
        "from the following production notes. Use only these facts. Unknown fields must be null.\n\n"
        f"Show: {rec.get('show')}\n"
        f"Episode: {rec.get('episode')}\n"
        f"Track: {rec.get('track')}\n"
        f"Version: {rec.get('version')}\n"
        f"Verification: {rec.get('verification')}\n"
        f"Notes: {rec.get('notes')}\n"
        f"Sources: {', '.join(rec.get('source_paths') or [])}\n\n"
        "Return JSON with location (name, view, plate_asset, condition, damage, layout_notes), "
        "lighting, time_of_day, characters (position, facing, gaze, posture, costume, props, injuries, state), "
        "props, environment_damage, locks_in_force, and end_of_track_state."
    )
    assistant = dumps(rec.get("continuity_state") or {})
    return user, assistant


def from_prompt_pair(rec: dict) -> tuple[str, str]:
    pp = rec.get("prompt_pair") or {}
    inp = pp.get("input") or {}
    out = pp.get("output") or {}
    user = (
        "Write a continuity-locked shot prompt for the next track. "
        "Keep dialogue verbatim. Keep shot types, order and framing unless the change request says otherwise. "
        "Carry positions, facing, costume, props, injuries, damage and location plate forward from the previous end state. "
        "Put every change inside the shot text, not as a note at the end.\n\n"
        f"Show: {rec.get('show')}\n"
        f"Episode: {rec.get('episode')}\n"
        f"Track: {rec.get('track')}\n"
        f"Version: {rec.get('version')}\n"
        f"Previous track: {inp.get('previous_track')}\n"
        f"Change request: {inp.get('change_request')}\n\n"
        "Previous end state:\n"
        f"{dumps(inp.get('previous_end_state') or {})}\n\n"
        "Script beat:\n"
        f"{dumps(inp.get('script_beat') or {})}\n\n"
        "Assets:\n"
        f"{dumps(inp.get('assets') or [])}\n\n"
        "Locks:\n"
        f"{dumps(inp.get('locks') or [])}"
    )
    assistant = dumps(out)
    return user, assistant


def from_qc_example(rec: dict) -> tuple[str, str]:
    qc = rec.get("qc_example") or {}
    user = (
        "QC this generation for continuity. List every continuity error with a category, "
        "and say pass or fail (or the recorded verdict). Propose a fix that goes inside the shot text. "
        "Do not invent errors that are not described.\n\n"
        f"Show: {rec.get('show')}\n"
        f"Episode: {rec.get('episode')}\n"
        f"Track: {rec.get('track')}\n"
        f"Version: {rec.get('version')}\n"
        f"Prompt path: {qc.get('prompt_path')}\n"
        f"Render path: {qc.get('render_path')}\n\n"
        "Prompt / intent:\n"
        f"{qc.get('prompt_summary')}\n\n"
        "Observed video:\n"
        f"{qc.get('observed_video')}"
    )
    assistant = dumps(
        {
            "verdict": qc.get("verdict"),
            "passes": qc.get("passes") or [],
            "errors": qc.get("errors") or [],
            "fix": qc.get("fix"),
        }
    )
    return user, assistant


def from_rule(rec: dict) -> tuple[str, str]:
    rule = rec.get("rule") or {}
    user = (
        "State the continuity rule that applies, explain it briefly, and give one good and one bad example.\n\n"
        f"Category: {rule.get('category')}\n"
        f"Applies to: {rule.get('applies_to')}\n"
        f"Context: {rec.get('notes') or 'general video continuity'}"
    )
    assistant = dumps(rule)
    return user, assistant


CONVERTERS = {
    "continuity_state": from_continuity_state,
    "prompt_pair": from_prompt_pair,
    "qc_example": from_qc_example,
    "rule": from_rule,
}


def convert_record(rec: dict) -> dict | None:
    if rec.get("is_example_template"):
        return None
    rtype = rec.get("record_type")
    fn = CONVERTERS.get(rtype)
    if not fn:
        return None
    user, assistant = fn(rec)
    return {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
        "meta": {
            "id": rec.get("id"),
            "record_type": rtype,
            "show": rec.get("show"),
            "episode": rec.get("episode"),
            "track": rec.get("track"),
        },
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Convert continuity records to chat fine-tuning JSONL.")
    p.add_argument("--in-dir", type=Path, default=Path(__file__).resolve().parent)
    p.add_argument("--out", type=Path, default=None)
    p.add_argument("--drop-meta", action="store_true", help="Write only {messages} (no meta key).")
    args = p.parse_args()
    in_dir = args.in_dir
    out_path = args.out or (in_dir / "train_chat.jsonl")
    files = ["uw_continuity.jsonl", "rules.jsonl", "template_new_show.jsonl"]
    written = 0
    skipped = 0
    counts: dict[str, int] = {}
    with out_path.open("w", encoding="utf-8") as out:
        for name in files:
            path = in_dir / name
            if not path.exists():
                raise SystemExit(f"Missing {path}")
            for rec in load_jsonl(path):
                row = convert_record(rec)
                if row is None:
                    skipped += 1
                    continue
                if args.drop_meta:
                    row = {"messages": row["messages"]}
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                written += 1
                rtype = rec.get("record_type") or "unknown"
                counts[rtype] = counts.get(rtype, 0) + 1
    print(f"Wrote {written} chat examples to {out_path}")
    print("By type:", counts)
    print(f"Skipped (templates or unknown type): {skipped}")


if __name__ == "__main__":
    main()
