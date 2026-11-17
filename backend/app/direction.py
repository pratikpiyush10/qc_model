"""Load director's-manual rules from manual_dataset."""

from __future__ import annotations

import json

from backend.app.config import settings

_QUOTE_LIMIT = 220


def direction_file():
    return settings.root / "manual_dataset" / "rules.jsonl"


def load_direction_rules() -> list[dict]:
    """Return the 45 direction rules with two short evidence quotes each."""
    path = direction_file()
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    rules: list[dict] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict) or record.get("record_type") != "rule":
            continue
        text = str(record.get("rule_text") or "").strip()
        category = str(record.get("category") or "").strip()
        if not text or not category:
            continue
        evidence = []
        raw_evidence = record.get("evidence")
        if isinstance(raw_evidence, list):
            for item in raw_evidence:
                if not isinstance(item, dict):
                    continue
                quote = _clip(str(item.get("quote") or ""))
                if not quote:
                    continue
                evidence.append(
                    {
                        "show": str(item.get("show") or "").strip(),
                        "episode": str(item.get("episode") or "").strip(),
                        "quote": quote,
                    }
                )
                if len(evidence) == 2:
                    break
        notes = record.get("notes")
        rules.append(
            {
                "id": str(record.get("id") or ""),
                "category": category,
                "applies_to": str(record.get("applies_to") or "").strip(),
                "rule_text": text,
                "notes": "" if notes is None else str(notes).strip(),
                "evidence": evidence,
            }
        )
    return rules


def _clip(text: str, limit: int = _QUOTE_LIMIT) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    room = limit - 3
    clipped = compact[:room].rstrip()
    space = clipped.rfind(" ")
    if space >= room - 40:
        clipped = clipped[:space].rstrip()
    return clipped + "..."
