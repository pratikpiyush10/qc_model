"""Parsing helpers for the director's-manual dataset. Pure functions, no invention:
every value returned is a substring/split of the source text, or a clearly derived number."""
from __future__ import annotations
import re, json
from pathlib import Path

CIRCLED = "①②③④⑤⑥⑦⑧⑨"
SECTION_KEYS = {
    1: "s1_theme_emotional_arc",
    2: "s2_visual_style_camera",
    3: "s3_narrative_structure_beats",
    4: "s4_scene_intent",
    5: "s5_sound",
    6: "s6_transitions_continuity",
    7: "s7_derivative_assets",
    8: "s8_extra_execution_or_look",
    9: "s9_extra",
}
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)

# canonical storyboard columns
COLMAP = {
    "shot": "shot", "id": "shot", "#": "shot",
    "title": "title",
    "frame description": "frame_description", "description": "frame_description",
    "scene": "scene",
    "associated asset names": "asset_names", "associateassetsnames": "asset_names", "associated assets": "asset_names", "assets": "asset_names",
    "duration": "duration", "dur": "duration",
    "shot size": "shot_size", "shotsize": "shot_size",
    "camera movement": "camera_movement", "cameramove": "camera_movement",
    "character action": "character_action", "action": "character_action",
    "orientation": "orientation",
    "spatial relationship": "spatial_relationship", "spatialrelation": "spatial_relationship", "spatial relation": "spatial_relationship",
    "emotion": "emotion",
    "dialogue": "dialogue", "lines": "dialogue",
    "sound effects": "sound_effects", "sound": "sound_effects", "sound fx": "sound_effects",
    "associated asset ids": "asset_ids", "associateassetsids": "asset_ids",
    "asset pictures": "asset_pictures",
    "group": "group",
    "shot id": "shot", "associate assets names": "asset_names", "associate assets ids": "asset_ids",
    "shot scale": "shot_size", "sound effect": "sound_effects",
}
CANON_COLS = ["shot", "title", "frame_description", "scene", "asset_names", "duration", "shot_size",
              "camera_movement", "character_action", "orientation", "spatial_relationship", "emotion",
              "dialogue", "sound_effects", "asset_ids", "asset_pictures", "group"]

REVIEW_COLMAP = {
    "#": "n", "severity": "severity", "review item": "item", "item": "item", "audit item": "item",
    "issue": "issue", "finding": "issue", "finding / recommendation": "issue_and_fix",
    "suggested fix": "fix", "suggested resolution": "fix", "recommended solution": "fix", "solution": "fix",
}


def canon_col(name: str) -> str:
    k = name.strip().lower()
    return COLMAP.get(k, re.sub(r"[^a-z0-9]+", "_", k).strip("_"))


def parse_duration(s):
    if s is None:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", str(s))
    return float(m.group(1)) if m else None


def parse_bracket_list(s):
    if not s:
        return []
    t = s.strip()
    if t.startswith("[") and t.endswith("]"):
        inner = t[1:-1].strip()
        if inner.startswith('"'):
            try:
                return json.loads(t)
            except Exception:
                pass
        return [x.strip().strip('"') for x in inner.split(",") if x.strip()]
    return [x.strip() for x in t.split(",") if x.strip()]


def parse_dialogue(s):
    """Derived: split 'Speaker: line' segments. Raw text is kept verbatim elsewhere."""
    if s is None:
        return []
    t = s.strip()
    if t.lower() in ("none", "no dialogue", "—", "-", "", "n/a"):
        return []
    m = re.match(r"^([^:：]{1,60})[:：]\s*(.+)$", t, re.S)
    if m:
        return [{"speaker": m.group(1).strip(), "text": m.group(2).strip()}]
    return [{"speaker": None, "text": t}]


def has_devanagari(s):
    return bool(s and re.search(r"[\u0900-\u097F]", s))


def parse_orientation(s):
    if not s:
        return []
    out = []
    for part in re.split(r";\s*", s):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^(.+?)\s*-\s*(.+)$", part)
        out.append({"character": m.group(1).strip(), "orientation": m.group(2).strip()} if m else {"character": None, "orientation": part})
    return out


def parse_pipe_storyboard(text):
    """Returns (header, rows, review_blocks, warnings). Rows: list of dict raw_col->val."""
    lines = text.split("\n")
    warnings = []
    if text.strip() == "EMPTY":
        return None, [], [], ["EMPTY"]
    header = [h.strip() for h in lines[0].split(" | ")]
    rows, reviews = [], []
    in_review = False
    rev_header = None
    block = -1
    for ln, line in enumerate(lines[1:], 2):
        if not line.strip():
            continue
        if line.strip() == "REVIEW ROWS":
            in_review = True
            continue
        if not in_review:
            # a pipe row starting with a shot number; REVIEW ROWS may be glued after a row w/o newline
            parts = line.split(" | ")
            if len(parts) < len(header) and len(parts) >= 4 and re.search(r"[🔴🟡⚪🟠🟢]|Critical|Moderate|Minor|Medium", parts[1]):
                rec = {"_block": "pre_review_rows", "_line": ln, "_header": ["#", "Severity", "Audit Item", "Issue", "Recommended Solution"][:len(parts)]}
                for i, hh in enumerate(rec["_header"]):
                    rec[hh] = parts[i].strip()
                reviews.append(rec)
                continue
            if len(parts) != len(header):
                warnings.append(f"line {ln}: {len(parts)} cells vs {len(header)} header cols")
                if len(parts) > len(header):
                    # merge overflow into the description column (cell contained ' | ')
                    di = 2 if header[1].lower() == "title" else 1
                    extra = len(parts) - len(header)
                    parts = parts[:di] + [" | ".join(parts[di:di + extra + 1])] + parts[di + extra + 1:]
                else:
                    parts += [""] * (len(header) - len(parts))
            rows.append({"_line": ln, **dict(zip(header, [p.strip() for p in parts]))})
        else:
            if line.startswith("#"):
                rev_header = [h.strip() for h in line.split(" | ")]
                block += 1
                continue
            parts = [p.strip() for p in line.split(" | ")]
            if rev_header is None:
                rev_header = ["#", "Severity", "Item", "Issue", "Suggested fix"]
                block += 1
            if not re.match(r"^\d+$", parts[0]):
                # continuation text of previous review row
                if reviews:
                    reviews[-1]["_continuation"] = (reviews[-1].get("_continuation", "") + "\n" + line).strip()
                continue
            rec = {"_block": block, "_line": ln, "_header": rev_header}
            for i, h in enumerate(rev_header):
                rec[h] = parts[i] if i < len(parts) else None
            if len(parts) > len(rev_header):
                rec["_overflow"] = " | ".join(parts[len(rev_header):])
            reviews.append(rec)
    return header, rows, reviews, warnings


KW_ORDER = [(r"Transition", 6), (r"Deriv", 7), (r"Sound", 5), (r"Theme", 1), (r"Narrative", 3), (r"Scene", 4), (r"Visual", 2)]
def heading_kw(h):
    for rx, n in KW_ORDER:
        if re.search(rx, h, re.I):
            return n
    return None


def split_manual(text):
    """Split manual into preamble + circled sections. Returns dict."""
    lines = text.split("\n")
    sections = {}
    order = []
    cur = "preamble"
    buf = {cur: []}
    anomalies = []
    numbered_fallback = not any(l.strip() and l.strip()[0] in CIRCLED for l in lines)
    for l in lines:
        s = l.strip()
        n = None
        if s and s[0] in CIRCLED:
            n = CIRCLED.index(s[0]) + 1
        elif numbered_fallback:
            m = re.match(r"^(\d)\.\s+[A-Z][A-Z'/&,\- ]+", s)
            if m:
                n = int(m.group(1))
        if n:
            kw = heading_kw(s)
            if kw and kw != n:
                anomalies.append(f"heading {s[:60]!r} numbered {n} but titled as section {kw}; filed as section {kw}")
                n = kw
            cur = f"s{n}"
            if cur in buf:
                cur = cur + "_dup"
            buf[cur] = [l]
            order.append(cur)
        else:
            buf.setdefault(cur, []).append(l)
    out = {k: "\n".join(v).strip("\n") for k, v in buf.items()}
    out["__anomalies__"] = anomalies
    return out, order, numbered_fallback


def extract_tables(section_text):
    """Tab-separated tables -> list of {header, rows}. Header = first tabbed line of a block."""
    tables = []
    cur = None
    for l in section_text.split("\n"):
        if "\t" in l and len(l.split("\t")) >= 3:
            cells = [c.strip() for c in l.split("\t")]
            if cur is None:
                cur = {"header": cells, "rows": []}
            else:
                row = dict(zip(cur["header"], cells + [""] * (len(cur["header"]) - len(cells))))
                if len(cells) > len(cur["header"]):
                    row["_overflow"] = cells[len(cur["header"]):]
                cur["rows"].append(row)
        elif "\t" in l and len(l.split("\t")) == 2 and cur is not None:
            cells = [c.strip() for c in l.split("\t")]
            cur["rows"].append(dict(zip(cur["header"], cells)))
        else:
            if cur is not None and l.strip() == "":
                continue  # blank lines inside a table block are tolerated
            if cur is not None:
                tables.append(cur)
                cur = None
    if cur is not None:
        tables.append(cur)
    return tables


def extract_tables_loose(section_text):
    """Also capture 2-column tab tables (e.g. section 7 lists with 3 cols are caught above)."""
    return extract_tables(section_text)


SCENE_HEAD_RE = re.compile(r"^(?:Scene|Sc)\s*(\d+(?:[-.]\d+)?)\s*[:–\-—]\s*(.*)$")
SHOT_RANGE_RE = re.compile(r"Shots?\s+(\d+)(?:\s*[–\-—]\s*(\d+))?")


def split_scenes(sec4_text):
    blocks = []
    intro = {"scene_no": None, "heading": "(section intro)", "lines": []}
    cur = None
    for l in sec4_text.split("\n")[1:]:
        s = l.strip()
        m = SCENE_HEAD_RE.match(s)
        if m and not re.match(r"^Scene\s+(Number|Emotion)", s):
            if cur:
                blocks.append(cur)
            cur = {"scene_no": int(re.match(r"\d+", m.group(1)).group(0)), "scene_label": m.group(1), "heading": s, "lines": []}
            r = SHOT_RANGE_RE.search(s)
            if r:
                a = int(r.group(1)); b = int(r.group(2) or r.group(1))
                cur["shot_range"] = [a, b]
            dm = re.search(r"/\s*(\d+)s\)", s)
            if dm:
                cur["stated_duration_s"] = int(dm.group(1))
        elif cur is not None:
            cur["lines"].append(l)
        else:
            intro["lines"].append(l)
    if cur:
        blocks.append(cur)
    if "".join(intro["lines"]).strip():
        blocks.insert(0, intro)
    out = []
    for b in blocks:
        body = "\n".join(b.pop("lines")).strip()
        b["text"] = body
        # derived key:value fields
        kv = {}
        for l in body.split("\n"):
            mm = re.match(r"^([A-Z][A-Za-z /&()\-’']{2,60}):\s*(.+)$", l.strip())
            if mm:
                kv.setdefault(mm.group(1).strip(), []).append(mm.group(2).strip())
        b["labelled_fields_derived"] = {k: (v[0] if len(v) == 1 else v) for k, v in kv.items()}
        out.append(b)
    return out


def kv_fields(text):
    kv = {}
    for l in text.split("\n")[1:]:
        mm = re.match(r"^([A-Z][A-Za-z0-9 /&()\-’',.]{2,70}):\s*(.+)$", l.strip())
        if mm:
            kv.setdefault(mm.group(1).strip(), []).append(mm.group(2).strip())
    return {k: (v[0] if len(v) == 1 else v) for k, v in kv.items()}
