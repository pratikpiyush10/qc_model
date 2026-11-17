"""Load continuity rules from the local dataset."""

from __future__ import annotations

import json

from backend.app.config import settings

PROMPT_CATEGORIES = {
    "costume",
    "identity",
    "eye_glow",
    "position",
    "direction",
    "posture",
    "eyeline",
    "props",
    "inventory",
    "location_plate",
    "damage",
    "lighting",
}
_PROMPT_CHAR_CAP = 2500


def rules_file():
    return settings.root / "continuity_dataset" / "rules.jsonl"


def load_rules() -> list[dict]:
    """Return every rule for the rules page. A bad file yields an empty list."""
    path = rules_file()
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
        if not isinstance(record, dict):
            continue
        rule = record.get("rule")
        if not isinstance(rule, dict):
            continue
        text = str(rule.get("rule_text") or "").strip()
        category = str(rule.get("category") or "").strip()
        if not text or not category:
            continue
        rules.append(
            {
                "id": str(record.get("id") or ""),
                "category": category,
                "rule_text": text,
                "good_example": str(rule.get("good_example") or "").strip(),
                "bad_example": str(rule.get("bad_example") or "").strip(),
            }
        )
    return rules


def prompt_rules_block() -> str:
    """Short visual-rule summary for the Gemini prompt. Examples are omitted."""
    lines: list[str] = []
    used = 0
    for rule in load_rules():
        if rule["category"] not in PROMPT_CATEGORIES:
            continue
        bullet = f"- {rule['rule_text']}"
        extra = len(bullet) + 1
        if lines and used + extra > _PROMPT_CHAR_CAP:
            break
        if not lines and extra > _PROMPT_CHAR_CAP:
            bullet = bullet[: _PROMPT_CHAR_CAP - 1].rstrip() + "…"
            lines.append(bullet)
            break
        lines.append(bullet)
        used += extra
    if not lines:
        return ""
    return (
        "Flag a break of any rule below. Wording that allows a director-approved "
        "exception does not apply here, because that approval is not in the frames:\n"
        + "\n".join(lines)
    )
