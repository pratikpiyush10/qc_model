#!/usr/bin/env python3
"""Build the director's-manual dataset from verbatim sources. Re-runnable.
python3 tools/build.py   (from /workspace/manual_dataset)
Nothing is invented: raw text is copied; parsed/derived fields are labelled *_derived or listed in schema.json."""
from __future__ import annotations
import json, re, glob, os, sys, hashlib
from collections import Counter, OrderedDict
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
from parse_lib import *

ROOT = Path("/workspace/manual_dataset")
RAW = ROOT / "raw"
PAIRS = ROOT / "pairs"
PAIRS.mkdir(exist_ok=True)

UW_SHOW = "Ultimate Warrior"
UW_PROJECT = "e3f21c53-5527-4cd0-93e4-6abdfffbf370"
DUR_SHOW = "Maharishi Durvasa 2"
KRON_EP_IDS = {  # from /workspace/manual_dataset/extraction_log.md
    "Ep1": "3f2a38b5 (prefix only in log)", "Ep2": "e251484c-be6d-4fbb-9ad7-d1573210c6de", "Ep3": "8a8ce8fa-a61e-4d3a-a5f0-cce8d2c473ce",
    "Ep4": "a9082495-a03c-487a-ae47-c9ddae8f708b", "Ep5": "4940e659-7183-45d6-84a3-37f84c4640c2", "Ep6": "eed310bb-83a7-4ef2-b4bd-4f14882e7d62",
    "Ep7": "b59505b3-3735-46e9-ab3a-390fb76a4138", "Ep8": "95944ae5-40b3-464a-9a57-1114a69ceb5c", "Ep9": "a411de43-866b-4b5e-91a4-29d4c4bfe15d",
    "Ep10": "de7dff12-b54a-4379-8844-ec862ccbeb39", "Ep11": "3b816fd5-4555-40ca-90d7-298e810b7427", "Ep12": "55904fb3-ba4c-4ce1-ad53-ab5b5246c8b5",
    "Ep14": "24ec4a07-1bd3-42be-aa0f-2c33913d6dd6", "Ep14.2": "7fd0110c-3f9d-4aea-966e-1d24eaaa44f5", "Ep15": "443cc07d-7b6a-492a-ac16-1e4274a6ca5a",
    "Ep16": "54c345dc-9aa3-4500-9eca-01736c7be942", "ioc1": "218ea466-ecb1-43a7-be90-6b01ccc87efe", "ioc2": "ee79b06e-a7b2-44a5-a3d3-4ad41b168d98",
    "ioc3": "e99d2cfd-9029-462a-9cfe-6e317aa6024c", "ioc4": "707b8a4b-33a2-4719-a326-c80a521b235b", "ioc5": "e65f96fe-437d-40d4-8216-3f22d9d751bf",
    "IOCSCRIPT1_V1": "212fed11-7df1-43e7-bd0b-9c39cc89f8a3", "IOCSCRIPT1_V2": "b3e4823e-15b9-4728-af19-bdd993dd3cb0",
}
VAL_EPISODES = {("Ultimate Warrior", "Ep3"), ("Ultimate Warrior", "Ep9"), ("Ultimate Warrior", "ioc4"), ("Maharishi Durvasa 2", "EP12"), ("Maharishi Durvasa", "EP3")}

def ep_sort_key(e):
    m = re.match(r"^Ep(\d+)(?:\.(\d+))?$", e)
    if m: return (0, int(m.group(1)), int(m.group(2) or 0), e)
    m = re.match(r"^ioc(\d+)$", e)
    if m: return (1, int(m.group(1)), 0, e)
    return (2, 0, 0, e)

def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def size_bucket(s):
    """Derived coarse bucket from the raw Shot Size text (first size named)."""
    if not s: return None
    t = s.lower()
    order = [("extreme close", "ECU"), ("macro", "ECU"), ("insert", "INSERT"), ("medium close", "MCU"),
             ("close", "CU"), ("medium wide", "MWS"), ("medium long", "MWS"), ("cowboy", "MWS"), ("medium full", "MWS"), ("full shot", "FS"), ("full", "FS"),
             ("medium", "MS"), ("two-shot", "MS"), ("two shot", "MS"), ("over-the-shoulder", "OTS"), ("over the shoulder", "OTS"), ("ots", "OTS"),
             ("extreme wide", "EWS"), ("extreme long", "EWS"), ("establishing", "EWS"), ("aerial", "EWS"), ("wide", "WS"), ("long", "WS"), ("pov", "POV")]
    best = None
    for k, b in order:
        i = t.find(k)
        if i >= 0 and (best is None or i < best[0]):
            best = (i, b)
    return best[1] if best else "OTHER"

def move_buckets(s):
    if not s: return []
    t = s.lower()
    rules = [("static", r"static|locked|lock-off|locked-off|tripod|still frame|holds?\b|fixed"), ("push_in", r"push[- ]?in|dolly in|creep|push toward|moves in|punch[- ]in"),
             ("pull_back", r"pull[- ]?(back|out)|dolly (out|back)|tracks? out|retreat"), ("track_dolly", r"track|dolly|glide|follow|lateral|truck"),
             ("pan", r"\bpan"), ("tilt", r"tilt"), ("crane_jib_pedestal", r"crane|jib|pedestal|boom|rise|descend"), ("arc_orbit", r"\barc|orbit|circl"),
             ("handheld", r"handheld|hand-held|shake"), ("whip", r"whip"), ("zoom", r"zoom"), ("aerial_drone", r"aerial|drone|flyover|bird"),
             ("rack_focus", r"rack focus|focus pull|pulls? focus|\brack\b"), ("speed_ramp", r"speed[- ]ramp|bullet time|slow motion|slow-motion")]
    out = [b for b, rx in rules if re.search(rx, t)]
    return out or ["other"]

def severity_level(s):
    if not s: return None
    t = s.lower()
    if "🔴" in s or "critical" in t or "high" in t: return "critical"
    if "🟠" in s or "major" in t: return "major"
    if "🟡" in s or "moderate" in t or "medium" in t: return "moderate"
    if "⚪" in s or "minor" in t or "low" in t: return "minor"
    if "🟢" in s: return "info"
    return None

def shot_refs(text):
    refs = set()
    for m in re.finditer(r"Shots?\s+((?:\d+(?:\s*[–\-—&]\s*\d+)?(?:\s*,\s*|\s+(?:and|&)\s+)?)+)", text or ""):
        chunk = m.group(1)
        for a, b in re.findall(r"(\d+)(?:\s*[–\-—]\s*(\d+))?", chunk):
            a = int(a); b = int(b) if b else a
            if 0 < a <= b and b - a <= 120:
                refs.update(range(a, b + 1))
    return sorted(refs)

COMPACT_COLS = ["shot", "title", "scene", "duration", "shot_size", "camera_movement", "frame_description", "character_action",
                "orientation", "spatial_relationship", "emotion", "dialogue", "sound_effects", "asset_names"]
def compact(shot, cols=COMPACT_COLS):
    return OrderedDict((c, shot["columns"].get(c)) for c in cols if shot["columns"].get(c) not in (None, ""))

# ----------------------------------------------------------------- UW
episodes, shots_all, reviews_all, skipped = [], [], [], []
shots_by_ep, eps_by_key = {}, {}

def build_storyboard(show, ep, header, rows, src, show_code):
    cc = [canon_col(h) for h in header]
    out = []
    t = 0.0
    run_idx, prev_scene = -1, object()
    for i, r in enumerate(rows):
        cols = OrderedDict()
        for h, c in zip(header, cc):
            cols[c] = r.get(h, "")
        if cols.get("scene") != prev_scene:
            run_idx += 1; prev_scene = cols.get("scene")
        d = parse_duration(cols.get("duration"))
        sn = cols.get("shot")
        sid = f"{show_code}_{ep}_s{int(sn):03d}" if str(sn).isdigit() else f"{show_code}_{ep}_r{i+1:03d}"
        rec = OrderedDict(
            id=sid, record_type="shot", show=show, episode=ep, shot=int(sn) if str(sn).isdigit() else sn, row_index=i + 1,
            source_paths=[src], source_line=r.get("_line"), columns=cols,
            parsed_derived=OrderedDict(
                duration_s=d, start_s=t if d is not None else None, end_s=(t + d) if d is not None else None,
                asset_names_list=parse_bracket_list(cols.get("asset_names")),
                asset_ids_list=parse_bracket_list(cols.get("asset_ids")),
                asset_uuids=UUID_RE.findall(cols.get("asset_ids") or ""),
                dialogue_segments=parse_dialogue(cols.get("dialogue")),
                has_dialogue=bool(parse_dialogue(cols.get("dialogue"))),
                dialogue_has_devanagari=has_devanagari(cols.get("dialogue")),
                orientation_list=parse_orientation(cols.get("orientation")),
                shot_size_bucket=size_bucket(cols.get("shot_size")),
                camera_move_buckets=move_buckets(cols.get("camera_movement")),
                scene_run_index=run_idx,
            ))
        if d is not None: t += d
        out.append(rec)
    for i, rec in enumerate(out):
        rec["prev_shot_id"] = out[i - 1]["id"] if i else None
        rec["next_shot_id"] = out[i + 1]["id"] if i + 1 < len(out) else None
    return out

def build_reviews(show, ep, revs, src, show_code, shots_index):
    out = []
    for k, r in enumerate(revs):
        hdr = r["_header"]
        def get(*names):
            for h in hdr:
                if REVIEW_COLMAP.get(h.strip().lower()) in names:
                    return r.get(h)
            return None
        issue = get("issue"); fix = get("fix"); both = get("issue_and_fix")
        if both and not issue: issue = both
        cont = r.get("_continuation")
        refs = shot_refs(" ".join(x for x in [get("item"), issue, fix] if x))
        out.append(OrderedDict(
            id=f"{show_code}_{ep}_rev{k+1:02d}", record_type="review", show=show, episode=ep,
            review_block=r["_block"], review_no=get("n"), source_paths=[src], source_line=r["_line"],
            raw_header=hdr, severity_raw=get("severity"), severity_level_derived=severity_level(get("severity")),
            item=get("item"), issue=issue, suggested_fix=fix, continuation_text=cont, overflow_text=r.get("_overflow"),
            referenced_shots_derived=refs, referenced_shot_ids_derived=[shots_index[n] for n in refs if n in shots_index],
            review_kind="kronicle_storyboard_or_plan_audit"))
    return out

def parse_title(text):
    """Derived: episode title cut out of the manual's first line(s). Null when the manual names none."""
    lines = [l.strip().lstrip("#").strip() for l in text.split("\n") if l.strip()][:4]
    first = lines[0] if lines else ""
    def clean(t):
        t = re.sub(r"\s*[—–-]\s*(?:\d+-Shot\s+)?Director.*$", "", t).strip()
        t = t.strip(' "“”()')
        return t or None
    for l in lines[:3]:
        if l.startswith(("①", "1.")):
            break
        m = re.search(r"(?:Episode|EP)\s*[\d.]+\s*[:—\-–·]\s*(.+)$", l, re.I)
        if m:
            t = m.group(1)
            m2 = re.search(r"\(\s*[\"“](.+?)[\"”]\s*\)", l)
            return (m2.group(1) if m2 else clean(t)), first
        m = re.search(r"Episode\s*[\d.]+\s*\(\s*[\"“]?(.+?)[\"”]?\s*\)", l)
        if m:
            return m.group(1), first
        m = re.match(r"^Director (?:Creative|Shooting|Production) Plan\s*:\s*(.+)$", l)
        if m:
            return clean(m.group(1)), first
        m = re.search(r"\(([^)]+)\)", l)
        if m and "DIRECTOR" in l.upper():
            return m.group(1).strip(), first
    return None, first

def stated_counts(sec3):
    head = sec3.split("\n")[0] if sec3 else ""
    m = re.search(r"\((\d+)\s*Shots\s*/\s*(\d+)\s*Sec", head)
    if m: return int(m.group(1)), int(m.group(2))
    m = re.search(r"(\d+)\s+(?:planned\s+)?shots.{0,40}?(\d+)\s*s(?:ec|\b)", sec3 or "", re.I)
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)

def build_manual(text):
    """Return manual dict + appended blocks. The chat block (Ep2) and appended production notes are split off."""
    appended = OrderedDict()
    body = text
    mchat = re.search(r"(?m)^Chat · Ep", body)
    if mchat:
        appended["kronicle_chat_block"] = body[mchat.start():].strip()
        body = body[:mchat.start()].rstrip()
    mvw = re.search(r"(?m)^\**Video Workspace:?\**:?.*$", body)
    if mvw:
        appended["appended_production_note"] = body[mvw.start():].strip()
        body = body[:mvw.start()].rstrip()
    secs, order, fallback = split_manual(body)
    sections = OrderedDict()
    for key in order:
        if key == "__anomalies__": continue
        n = int(re.match(r"s(\d)", key).group(1))
        txt = secs[key]
        name = SECTION_KEYS.get(n, key) + ("_dup" if key.endswith("_dup") else "")
        sec = OrderedDict(heading=txt.split("\n")[0].strip(), text=txt,
                          labelled_fields_derived=kv_fields(txt), tables=extract_tables(txt))
        if n == 4:
            sec["scenes"] = split_scenes(txt)
        sections[name] = sec
    s3 = sections.get("s3_narrative_structure_beats")
    beat_table = s3["tables"][0] if s3 and s3["tables"] else None
    track_table = s3["tables"][1] if s3 and len(s3["tables"]) > 1 else None
    s7 = sections.get("s7_derivative_assets")
    deriv = s7["tables"][0] if s7 and s7["tables"] else None
    sh, du = stated_counts(s3["text"] if s3 else "")
    return OrderedDict(
        preamble=secs.get("preamble", "").strip() or None, section_order=list(sections.keys()),
        heading_anomalies_derived=secs.get("__anomalies__") or [],
        numbered_headings_instead_of_circled=fallback, sections=sections,
        beat_table=beat_table, track_table=track_table, derivative_asset_table=deriv,
        stated_shot_count=sh, stated_duration_s=du, manual_text_clean=body.strip()), appended

def stats_for(shots, revs):
    durs = [s["parsed_derived"]["duration_s"] for s in shots if s["parsed_derived"]["duration_s"] is not None]
    sizes = Counter(s["columns"].get("shot_size") for s in shots)
    moves = Counter(s["columns"].get("camera_movement") for s in shots)
    speakers = Counter(seg["speaker"] for s in shots for seg in s["parsed_derived"]["dialogue_segments"] if seg["speaker"])
    scenes = []
    for s in shots:
        sc = s["columns"].get("scene")
        if not scenes or scenes[-1]["scene"] != sc:
            scenes.append({"scene": sc, "first_shot": s["shot"], "last_shot": s["shot"], "shots": 0, "duration_s": 0})
        scenes[-1]["last_shot"] = s["shot"]; scenes[-1]["shots"] += 1; scenes[-1]["duration_s"] += s["parsed_derived"]["duration_s"] or 0
    return OrderedDict(
        shot_count=len(shots), total_duration_s=sum(durs), avg_shot_s=round(sum(durs) / len(durs), 2) if durs else None,
        min_shot_s=min(durs) if durs else None, max_shot_s=max(durs) if durs else None,
        dialogue_shot_count=sum(1 for s in shots if s["parsed_derived"]["has_dialogue"]),
        shot_size_distribution_raw=dict(sizes.most_common()),
        shot_size_bucket_distribution_derived=dict(Counter(s["parsed_derived"]["shot_size_bucket"] for s in shots).most_common()),
        camera_move_distribution_raw=dict(moves.most_common()),
        camera_move_bucket_distribution_derived=dict(Counter(b for s in shots for b in s["parsed_derived"]["camera_move_buckets"]).most_common()),
        speaker_line_counts_derived=dict(speakers.most_common()),
        scene_runs_derived=scenes, distinct_scene_values=len(set(s["columns"].get("scene") for s in shots)),
        review_count=len(revs), review_severity_derived=dict(Counter(r["severity_level_derived"] for r in revs).most_common()))

# script matching (dialogue 3-gram overlap with storyboard dialogue) ----------------------------------
def toks(t): return re.findall(r"[a-z\u0900-\u097f]+", (t or "").lower())
def grams(t, n=3):
    w = toks(t); return set(tuple(w[i:i + n]) for i in range(len(w) - n + 1))

SCRIPT_CANDIDATES = []
for p in sorted(glob.glob("/workspace/uw2/scripts/*.txt")) + sorted(glob.glob("/workspace/uw/scripts/*.txt")) + ["/workspace/uw_ep5/script.txt", "/workspace/uw_ioc/IOC1_script.txt", "/workspace/uw_ioc/IOC2_script.txt"]:
    SCRIPT_CANDIDATES.append((p, open(p, encoding="utf-8").read()))
_doc = open("/workspace/uw_ioc/ioc_doc.txt", encoding="utf-8").read()
_parts = re.split(r"(?m)^\s*(\d)-\s*$", _doc)
IOC_DOC_SECTIONS = {}
for i in range(1, len(_parts), 2):
    IOC_DOC_SECTIONS[_parts[i]] = _parts[i + 1].strip("\n")
    SCRIPT_CANDIDATES.append((f"/workspace/uw_ioc/ioc_doc.txt#section{_parts[i]}", _parts[i + 1].strip("\n")))

uw_eps = sorted(set(re.sub(r"^uw_(.+)_(manual|storyboard)\.txt$", r"\1", os.path.basename(f)) for f in glob.glob(str(RAW / "uw_*.txt"))), key=ep_sort_key)
script_matches = {}
for ep in uw_eps:
    sbtxt = (RAW / f"uw_{ep}_storyboard.txt").read_text(encoding="utf-8")
    if sbtxt.strip() == "EMPTY":
        continue
    h, rows, _, _ = parse_pipe_storyboard(sbtxt)
    dcol = h[[canon_col(x) for x in h].index("dialogue")]
    g = grams(" ".join(r[dcol] for r in rows))
    ms = []
    for p, txt in SCRIPT_CANDIDATES:
        sc = len(grams(txt) & g) / max(1, len(g))
        if sc >= 0.3:
            ms.append({"script_path": p, "dialogue_trigram_overlap_derived": round(sc, 3)})
    script_matches[ep] = sorted(ms, key=lambda x: -x["dialogue_trigram_overlap_derived"])
script_text = {p: t for p, t in SCRIPT_CANDIDATES}
unmatched_scripts = [p for p, _ in SCRIPT_CANDIDATES if not any(p == m["script_path"] for v in script_matches.values() for m in v)]

for ep in uw_eps:
    mpath, spath = RAW / f"uw_{ep}_manual.txt", RAW / f"uw_{ep}_storyboard.txt"
    mtxt, stxt = mpath.read_text(encoding="utf-8"), spath.read_text(encoding="utf-8")
    if mtxt.strip() == "EMPTY" and stxt.strip() == "EMPTY":
        skipped.append({"show": UW_SHOW, "episode": ep, "reason": "manual and storyboard are blank in Kronicle (file content 'EMPTY')", "paths": [str(mpath), str(spath)]})
        continue
    header, rows, revs, warns = parse_pipe_storyboard(stxt)
    shots = build_storyboard(UW_SHOW, ep, header, rows, str(spath), "uw")
    idx = {s["shot"]: s["id"] for s in shots}
    rv = build_reviews(UW_SHOW, ep, revs, str(spath), "uw", idx)
    manual, appended = build_manual(mtxt)
    title, title_line = parse_title(mtxt)
    st = stats_for(shots, rv)
    ms = script_matches.get(ep, [])
    rec = OrderedDict(
        id=f"uw_{ep}", record_type="episode", show=UW_SHOW, show_project_id=UW_PROJECT, episode=ep, episode_base=ep, version=None,
        kronicle_episode_id=KRON_EP_IDS.get(ep), title=title, title_line=title_line,
        source_kind="kronicle_extraction_verbatim", source_paths=[str(mpath), str(spath)],
        has_manual=mtxt.strip() != "EMPTY", has_storyboard=bool(shots),
        manual=manual, appended_blocks=appended or None,
        storyboard_header_raw=header, storyboard_parse_warnings=warns,
        scripts_matched_derived=ms, primary_script_path=ms[0]["script_path"] if ms else None,
        stats=st,
        stats_vs_manual_derived=OrderedDict(stated_shot_count=manual["stated_shot_count"], stated_duration_s=manual["stated_duration_s"],
                                            storyboard_shot_count=st["shot_count"], storyboard_duration_s=st["total_duration_s"]),
        manual_raw=mtxt, split="val" if (UW_SHOW, ep) in VAL_EPISODES else "train",
        notes=None)
    if ep == "Ep1":
        rec["notes"] = ("Manual on disk (~12.7 KB) used. The fuller Ep1 report transcript (agent sand-subagent-d8e094c0-...) was not readable "
                        "from this builder, so completeness against it could not be checked. Ep1 REVIEW ROWS block is empty on disk.")
    if ep in ("Ep4", "Ep5"):
        rec["notes"] = "Manual text as saved from Kronicle carries a version preamble (built from an approved storyboard JSON) and an appended Video Workspace note; both kept as separate fields."
    if ep == "Ep2":
        rec["notes"] = "Manual text as saved ends with the Kronicle chat (producer audit + asset analysis). Kept separately in appended_blocks.kronicle_chat_block; excluded from manual_text_clean. Two audit rows appeared above REVIEW ROWS in the storyboard file; parsed as reviews (block 'pre_review_rows')."
    if ep == "ioc2":
        rec["notes"] = "Manual uses numbered headings (1.-8.) instead of circled ①-⑧; section 8 holds Ninni's director rules."
    episodes.append(rec); shots_all += shots; reviews_all += rv
    shots_by_ep[(UW_SHOW, ep)] = shots; eps_by_key[(UW_SHOW, ep)] = rec

# ----------------------------------------------------------------- Kronicle Durvasa (project 02a204b6...) - picked up automatically
# if raw/durvasa_<ep>_manual.txt / durvasa_<ep>_storyboard.txt exist (same pipe format as UW). None exist at build time (see README).
DK_SHOW = "Maharishi Durvasa"
DK_SCRIPTS = [(p, open(p, encoding="utf-8").read()) for p in ["/workspace/kronicle/script_EP12.md", "/workspace/kronicle/script_EP14.md", "/workspace/ep13_1/script.md"]]
for mp in sorted(glob.glob(str(RAW / "durvasa_*_manual.txt"))):
    ep = re.sub(r"^durvasa_(.+)_manual\.txt$", r"\1", os.path.basename(mp))
    mver = re.match(r"^(EP\d+)(V\d+)?$", ep)
    ep_base, version = (mver.group(1), mver.group(2)) if mver else (ep, None)
    sp = RAW / f"durvasa_{ep}_storyboard.txt"
    mtxt = open(mp, encoding="utf-8").read(); stxt = sp.read_text(encoding="utf-8") if sp.exists() else "EMPTY"
    if mtxt.strip() == "EMPTY" and stxt.strip() == "EMPTY":
        skipped.append({"show": DK_SHOW, "episode": ep, "reason": "blank", "paths": [mp, str(sp)]}); continue
    header, rows, revs, warns = parse_pipe_storyboard(stxt)
    shots = build_storyboard(DK_SHOW, ep, header, rows, str(sp), "durk") if header else []
    rv = build_reviews(DK_SHOW, ep, revs, str(sp), "durk", {s["shot"]: s["id"] for s in shots})
    has_m = mtxt.strip() != "EMPTY"
    manual, appended = build_manual(mtxt) if has_m else (None, {})
    title, title_line = parse_title(mtxt) if has_m else (None, None)
    st = stats_for(shots, rv)
    dcol = [c for c in shots[0]["columns"]] if shots else []
    g = grams(" ".join(x["columns"].get("dialogue") or "" for x in shots))
    ms = [{"script_path": p, "dialogue_trigram_overlap_derived": round(len(grams(t) & g) / max(1, len(g)), 3)} for p, t in DK_SCRIPTS]
    ms = [m for m in ms if m["dialogue_trigram_overlap_derived"] >= 0.3]
    notes = "Transcribed verbatim from Kronicle (Durvasa project 02a204b6...) by a computerUse agent; no review rows in Kronicle."
    if ep == "EP4V1": notes += " EP4 V1: no manual in Kronicle (file 'EMPTY'); storyboard has 24 rows that differ from V2."
    if manual and manual["heading_anomalies_derived"]: notes += " Heading anomaly: " + "; ".join(manual["heading_anomalies_derived"])
    rec = OrderedDict(id=f"durk_{ep}", record_type="episode", show=DK_SHOW, show_project_id="02a204b6-b20d-48e7-aed4-3cbd2abb0edf", episode=ep,
        episode_base=ep_base, version=version,
        kronicle_episode_id=None, title=title, title_line=title_line, source_kind="agent_report_transcription", source_paths=[mp, str(sp)],
        has_manual=manual is not None, has_storyboard=bool(shots), manual=manual, appended_blocks=appended or None, storyboard_header_raw=header,
        storyboard_parse_warnings=warns, scripts_matched_derived=ms, primary_script_path=ms[0]["script_path"] if ms else None, stats=st,
        stats_vs_manual_derived=(OrderedDict(stated_shot_count=manual["stated_shot_count"], stated_duration_s=manual["stated_duration_s"],
            storyboard_shot_count=st["shot_count"], storyboard_duration_s=st["total_duration_s"]) if manual else None),
        manual_raw=mtxt if manual else None, split="val" if (DK_SHOW, ep_base) in VAL_EPISODES else "train", notes=notes)
    episodes.append(rec); shots_all += shots; reviews_all += rv
    shots_by_ep[(DK_SHOW, ep)] = shots; eps_by_key[(DK_SHOW, ep)] = rec

# ----------------------------------------------------------------- Durvasa (local files; no manual)
def md_table_rows(text):
    lines = [l for l in text.split("\n") if l.startswith("|")]
    hdr = [c.strip() for c in lines[0].strip("|").split("|")]
    rows = []
    for ln, l in enumerate(text.split("\n"), 1):
        if l.startswith("|") and not l.startswith("| ---") and not l.startswith("|---") and l != lines[0]:
            cells = [c.strip() for c in l.strip().strip("|").split(" | ")]
            if len(cells) != len(hdr):
                cells = [c.strip() for c in l.strip().strip("|").split("|")]
            row = dict(zip(hdr, cells)); row["_line"] = ln
            rows.append(row)
    return hdr, rows

def tsv_rows(text):
    ls = text.split("\n")
    i = next(k for k, l in enumerate(ls) if l.count("\t") >= 10)
    hdr = [c.strip() for c in ls[i].split("\t")]
    rows = []
    for ln, l in enumerate(ls[i + 1:], i + 2):
        if l.count("\t") >= len(hdr) - 2:
            cells = [c.strip() for c in l.split("\t")]
            row = dict(zip(hdr, cells)); row["_line"] = ln
            rows.append(row)
    return hdr, rows

def bullet_rows(text):
    rows, cur = [], None
    for ln, l in enumerate(text.split("\n"), 1):
        m = re.match(r"^## Shot (\d+)", l)
        if m:
            if cur: rows.append(cur)
            cur = {"Shot": m.group(1), "_line": ln}
            continue
        m = re.match(r"^- \*\*(.+?)\*\*:\s?(.*)$", l)
        if m and cur is not None:
            cur[m.group(1)] = m.group(2)
    if cur: rows.append(cur)
    hdr = ["Shot", "Description", "Scene", "Associated Asset Names", "Duration", "Shot Size", "Camera Movement", "Character Action",
           "Orientation", "Spatial Relationship", "Emotion", "Dialogue", "Sound FX", "Associated Asset IDs"]
    return hdr, rows

def ep131_rows(text):
    hdr, rows = md_table_rows(text)
    out_hdr = ["Shot", "Scene", "Duration", "Shot / Camera", "Associated Asset Names", "Description", "Dialogue"]
    out = []
    for r in rows:
        out.append({"Shot": r.get("#"), "Scene": r.get("Scene"), "Duration": r.get("Dur"), "Shot / Camera": r.get("Shot / Camera"),
                    "Associated Asset Names": r.get("Assets"), "Description": r.get("Description"), "Dialogue": r.get("Dialogue"), "_line": r["_line"]})
    return out_hdr, out

DUR_SOURCES = [
    ("EP11", "/workspace/kronicle/storyboard_EP11.md", md_table_rows, None, "Full 14 columns (markdown table)."),
    ("EP12", "/workspace/kronicle/storyboard_EP12.md", tsv_rows, "/workspace/kronicle/script_EP12.md", "Full columns plus a Group column (tab-separated DOM text)."),
    ("EP13.1", "/workspace/ep13_1/storyboard.md", ep131_rows, "/workspace/ep13_1/script.md", "PARTIAL: file kept only Shot, Scene, Dur, Shot size/camera (merged), Assets, Description, Dialogue. Character Action, Orientation, Spatial, Emotion, SFX and Asset IDs were not reproduced in the source file."),
    ("EP14", "/workspace/kronicle/storyboard_EP14.md", bullet_rows, "/workspace/kronicle/script_EP14.md", "Full 14 columns (per-shot bullet lists)."),
]
for ep, path, fn, script, note in DUR_SOURCES:
    text = open(path, encoding="utf-8").read()
    hdr, rows = fn(text)
    if ep == "EP13.1":
        # shot size/camera merged in source; keep merged raw string under shot_size, camera_movement=None
        for r in rows:
            r["Shot Size"] = r.pop("Shot / Camera")
        hdr = ["Shot", "Scene", "Duration", "Shot Size", "Associated Asset Names", "Description", "Dialogue"]
    shots = build_storyboard(DUR_SHOW, ep, hdr, rows, path, "dur")
    if ep == "EP13.1":
        for s in shots:
            s["columns"]["shot_size_and_camera_merged_raw"] = s["columns"].pop("shot_size")
            s["parsed_derived"]["shot_size_bucket"] = size_bucket(s["columns"]["shot_size_and_camera_merged_raw"].split(";")[0])
            s["parsed_derived"]["camera_move_buckets"] = move_buckets(";".join(s["columns"]["shot_size_and_camera_merged_raw"].split(";")[1:]))
    st = stats_for(shots, [])
    rec = OrderedDict(
        id=f"dur_{ep}", record_type="episode", show=DUR_SHOW, show_project_id=None, episode=ep, episode_base=ep, version=None, kronicle_episode_id=None,
        title=None, title_line=text.split("\n")[0].lstrip("# ").strip(), source_kind="local_file_transcription",
        source_paths=[path] + ([script] if script else []), has_manual=False, has_storyboard=True,
        manual=None, appended_blocks=None, storyboard_header_raw=hdr, storyboard_parse_warnings=[],
        scripts_matched_derived=[{"script_path": script, "dialogue_trigram_overlap_derived": None}] if script else [],
        primary_script_path=script, stats=st, stats_vs_manual_derived=None, manual_raw=None,
        split="val" if (DUR_SHOW, ep) in VAL_EPISODES else "train",
        notes=f"Maharishi Durvasa 2 local file (a different project from the Kronicle Durvasa project 02a204b6...). No director's manual on disk. {note}")
    episodes.append(rec); shots_all += shots
    shots_by_ep[(DUR_SHOW, ep)] = shots; eps_by_key[(DUR_SHOW, ep)] = rec

# Durvasa EP12 prompt QC (local) as reviews
qc = open("/workspace/kronicle/qc_EP12.md", encoding="utf-8").read()
qn = 0
for ln, l in enumerate(qc.split("\n"), 1):
    m = re.match(r"^- \*\*(C\d+)\s*\(([^)]*)\):\*\*\s*(.+)$", l)
    g = re.match(r"^- (.+)$", l)
    if m:
        qn += 1
        reviews_all.append(OrderedDict(id=f"dur_EP12_qc{qn:02d}", record_type="review", show=DUR_SHOW, episode="EP12", review_block="prompt_qc_per_clip",
            review_no=str(qn), source_paths=["/workspace/kronicle/qc_EP12.md"], source_line=ln, raw_header=None, severity_raw=None, severity_level_derived=None,
            item=f"{m.group(1)} ({m.group(2)})", issue=m.group(3), suggested_fix=None, continuation_text=None, overflow_text=None,
            referenced_shots_derived=[], referenced_shot_ids_derived=[], review_kind="video_prompt_qc_orig_vs_v2"))
    elif g and qn == 0:
        reviews_all.append(OrderedDict(id=f"dur_EP12_qcg{ln:03d}", record_type="review", show=DUR_SHOW, episode="EP12", review_block="prompt_qc_global",
            review_no=None, source_paths=["/workspace/kronicle/qc_EP12.md"], source_line=ln, raw_header=None, severity_raw=None, severity_level_derived=None,
            item=None, issue=g.group(1), suggested_fix=None, continuation_text=None, overflow_text=None,
            referenced_shots_derived=[], referenced_shot_ids_derived=[], review_kind="video_prompt_qc_orig_vs_v2"))

# ----------------------------------------------------------------- write core files
episodes.sort(key=lambda r: (r["show"], ep_sort_key(r["episode"])))
write_jsonl(ROOT / "episodes.jsonl", episodes)
write_jsonl(ROOT / "shots.jsonl", shots_all)
write_jsonl(ROOT / "reviews.jsonl", reviews_all)
json.dump({"skipped": skipped, "unmatched_scripts": unmatched_scripts, "script_matches": script_matches}, open(ROOT / "build_report.json", "w"), ensure_ascii=False, indent=1)

# ----------------------------------------------------------------- pairs
def pair(pid, ptype, ep_rec, inp, out, src, extra=None):
    d = OrderedDict(id=pid, record_type="pair", pair_type=ptype, show=ep_rec["show"], episode=ep_rec["episode"], episode_base=ep_rec.get("episode_base"),
                    split=ep_rec["split"], source_paths=src, input=inp, output=out)
    if extra: d.update(extra)
    return d

P = {k: [] for k in ["script_to_manual", "script_to_storyboard", "manual_to_storyboard", "section_to_section", "scene_intent_to_shots", "row_to_critique", "beat_to_shot_plan", "storyboard_revision"]}
CHUNK = 8

def ep_header(rec):
    return OrderedDict(show=rec["show"], episode=rec["episode"], title=rec["title"])

for rec in episodes:
    key = (rec["show"], rec["episode"]); shots = shots_by_ep.get(key, [])
    man = rec["manual"]
    secs = man["sections"] if man else {}
    # 1 script -> manual
    if man and rec["primary_script_path"]:
        sp = rec["primary_script_path"]
        P["script_to_manual"].append(pair(f"{rec['id']}__script2manual", "script_to_manual", rec,
            OrderedDict(**ep_header(rec), script_path=sp, script_text=script_text[sp]),
            OrderedDict(manual_text=man["manual_text_clean"]), [sp] + rec["source_paths"][:1],
            {"pairing_method_derived": "dialogue 3-gram overlap with the episode storyboard", "pairing_score_derived": rec["scripts_matched_derived"][0]["dialogue_trigram_overlap_derived"]}))
        # per-section script -> each of ①-⑦ (shorter targets)
        for name, sec in secs.items():
            P["script_to_manual"].append(pair(f"{rec['id']}__script2{name}", "script_to_manual_section", rec,
                OrderedDict(**ep_header(rec), script_path=sp, script_text=script_text[sp], target_section=name, target_heading=sec["heading"]),
                OrderedDict(section_text=sec["text"]), [sp] + rec["source_paths"][:1]))
    # Durvasa script -> storyboard (chunked)
    if not man and rec["primary_script_path"] and shots:
        sp = rec["primary_script_path"]
        for i in range(0, len(shots), CHUNK):
            ch = shots[i:i + CHUNK]
            P["script_to_storyboard"].append(pair(f"{rec['id']}__script2sb_{ch[0]['shot']}-{ch[-1]['shot']}", "script_to_storyboard", rec,
                OrderedDict(**ep_header(rec), script_path=sp, script_text=script_text.get(sp) or open(sp, encoding="utf-8").read(),
                            target_shots=[ch[0]["shot"], ch[-1]["shot"]], total_shots=len(shots),
                            previous_shot=compact(shots[i - 1]) if i else None, columns_available=rec["storyboard_header_raw"]),
                OrderedDict(rows=[compact(s) for s in ch]), [sp, rec["source_paths"][0]]))
    if not man:
        continue
    # 2 section -> section
    order = [("s1_theme_emotional_arc",), ("s2_visual_style_camera",), ("s3_narrative_structure_beats",), ("s4_scene_intent",), ("s5_sound",), ("s6_transitions_continuity",), ("s7_derivative_assets",)]
    plan = [(["s1_theme_emotional_arc"], "s2_visual_style_camera"), (["s1_theme_emotional_arc", "s2_visual_style_camera"], "s3_narrative_structure_beats"),
            (["s1_theme_emotional_arc", "s3_narrative_structure_beats"], "s4_scene_intent"), (["s4_scene_intent"], "s5_sound"),
            (["s3_narrative_structure_beats", "s4_scene_intent"], "s6_transitions_continuity"), (["s4_scene_intent", "s6_transitions_continuity"], "s7_derivative_assets")]
    for srcs, tgt in plan:
        if tgt in secs and all(s in secs for s in srcs):
            P["section_to_section"].append(pair(f"{rec['id']}__{'+'.join(x[:2] for x in srcs)}2{tgt[:2]}", "section_to_section", rec,
                OrderedDict(**ep_header(rec), given_sections=OrderedDict((s, secs[s]["text"]) for s in srcs), target_section=tgt, target_heading=secs[tgt]["heading"]),
                OrderedDict(section_text=secs[tgt]["text"]), rec["source_paths"][:1]))
    if not shots:
        continue
    by_no = {s["shot"]: s for s in shots}
    # scene links
    scenes = [b for b in secs.get("s4_scene_intent", {}).get("scenes", []) if b["scene_no"] is not None]
    runs = rec["stats"]["scene_runs_derived"]
    links = []
    if scenes and all("shot_range" in b for b in scenes):
        for b in scenes:
            links.append((b, [by_no[n] for n in range(b["shot_range"][0], b["shot_range"][1] + 1) if n in by_no], "explicit_shot_range_in_heading"))
    elif scenes and len(scenes) == len(runs):
        for b, r in zip(scenes, runs):
            links.append((b, [s for s in shots if isinstance(s["shot"], int) and r["first_shot"] <= s["shot"] <= r["last_shot"]], "ordinal_match_scene_count_equals_storyboard_scene_runs"))
    elif scenes and all(re.search(r"\((\d\d):(\d\d)[–\-](\d\d):(\d\d)\)", b["heading"]) for b in scenes):
        for b in scenes:
            m = re.search(r"\((\d\d):(\d\d)[–\-](\d\d):(\d\d)\)", b["heading"])
            a, z = int(m.group(1)) * 60 + int(m.group(2)), int(m.group(3)) * 60 + int(m.group(4))
            links.append((b, [s for s in shots if s["parsed_derived"]["start_s"] is not None and a <= s["parsed_derived"]["start_s"] < z], "timecode_in_heading_vs_cumulative_shot_start"))
    rec["scene_links_derived"] = [{"scene_no": b["scene_no"], "heading": b["heading"], "shots": [s["shot"] for s in ss], "method": m} for b, ss, m in links]
    # 3 scene intent -> shots
    for b, ss, method in links:
        if not ss: continue
        parts = [ss[i:i + CHUNK] for i in range(0, len(ss), CHUNK)]
        for k, ch in enumerate(parts):
            P["scene_intent_to_shots"].append(pair(f"{rec['id']}__sc{b.get('scene_label', b['scene_no'])}_{ch[0]['shot']}-{ch[-1]['shot']}", "scene_intent_to_shots", rec,
                OrderedDict(**ep_header(rec), scene_heading=b["heading"], scene_intent_text=b["text"], part=f"{k+1} of {len(parts)}",
                            target_shots=[ch[0]["shot"], ch[-1]["shot"]], scene_total_shots=len(ss),
                            previous_shot=compact(by_no[ch[0]["shot"] - 1]) if isinstance(ch[0]["shot"], int) and ch[0]["shot"] - 1 in by_no else None),
                OrderedDict(shots=[compact(s, ["shot", "duration", "shot_size", "camera_movement", "frame_description", "character_action", "emotion", "dialogue", "sound_effects"]) for s in ch]),
                rec["source_paths"], {"link_method_derived": method}))
    # 4 manual -> storyboard (scene-run chunks of <= CHUNK rows)
    link_for_shot = {}
    for b, ss, m in links:
        for s in ss: link_for_shot[s["id"]] = b
    for r in runs:
        rs = [s for s in shots if isinstance(s["shot"], int) and r["first_shot"] <= s["shot"] <= r["last_shot"]]
        for i in range(0, len(rs), CHUNK):
            ch = rs[i:i + CHUNK]
            b = link_for_shot.get(ch[0]["id"])
            prev = by_no.get(ch[0]["shot"] - 1)
            ctx = OrderedDict(**ep_header(rec),
                visual_style_section=secs.get("s2_visual_style_camera", {}).get("text"),
                beat_table=rec["manual"]["beat_table"],
                scene_intent=(OrderedDict(heading=b["heading"], text=b["text"]) if b else None),
                scene_intent_section_full=(None if b else secs.get("s4_scene_intent", {}).get("text")),
                continuity_section=secs.get("s6_transitions_continuity", {}).get("text"),
                storyboard_scene_value=r["scene"], target_shots=[ch[0]["shot"], ch[-1]["shot"]], episode_total_shots=len(shots),
                previous_shot=compact(prev) if prev else None, columns=rec["storyboard_header_raw"])
            P["manual_to_storyboard"].append(pair(f"{rec['id']}__m2sb_{ch[0]['shot']}-{ch[-1]['shot']}", "manual_to_storyboard", rec, ctx,
                OrderedDict(rows=[compact(s, COMPACT_COLS + ["asset_ids"]) for s in ch]), rec["source_paths"]))
    # 5 beat -> shot plan
    bt = rec["manual"]["beat_table"]
    if bt:
        hdr = bt["header"]
        shot_col = next((h for h in hdr if re.search(r"shots?", h, re.I)), None)
        if shot_col:
            ranges, cum, ok = [], 1, True
            for row in bt["rows"]:
                v = row.get(shot_col, "")
                first = list(row.values())[0] if row else ""
                if re.match(r"^total", str(first), re.I): continue
                m = re.match(r"^\s*(\d+)\s*[–\-—]\s*(\d+)\s*$", v); m1 = re.match(r"^\s*(\d+)\s*$", v)
                if m:
                    ranges.append((row, int(m.group(1)), int(m.group(2)), "explicit_range")); cum = int(m.group(2)) + 1
                elif m1:
                    n = int(m1.group(1)); ranges.append((row, cum, cum + n - 1, "cumulative_from_shot_counts")); cum += n
                else:
                    ok = False
            if ok and ranges and ranges[-1][2] == max(s["shot"] for s in shots if isinstance(s["shot"], int)):
                for row, a, z, method in ranges:
                    ss = [by_no[n] for n in range(a, z + 1) if n in by_no]
                    for i in range(0, len(ss), 10):
                        ch = ss[i:i + 10]
                        P["beat_to_shot_plan"].append(pair(f"{rec['id']}__beat_{a}-{z}_{ch[0]['shot']}", "beat_to_shot_plan", rec,
                            OrderedDict(**ep_header(rec), beat_row=row, beat_table_header=hdr, beat_shot_range=[a, z], target_shots=[ch[0]["shot"], ch[-1]["shot"]],
                                        camera_grammar=secs.get("s2_visual_style_camera", {}).get("text")),
                            OrderedDict(shot_plan=[compact(s, ["shot", "duration", "shot_size", "camera_movement", "frame_description", "dialogue"]) for s in ch]),
                            rec["source_paths"], {"range_method_derived": method}))
            rec["beat_shot_ranges_derived"] = [{"beat": list(r[0].values())[:2], "shots": [r[1], r[2]], "method": r[3]} for r in ranges] if ok and ranges else None

# 6 row -> critique
for rv in reviews_all:
    rec = eps_by_key.get((rv["show"], rv["episode"]))
    if rv["review_kind"] != "kronicle_storyboard_or_plan_audit":
        continue
    shots = shots_by_ep.get((rv["show"], rv["episode"]), [])
    by_no = {s["shot"]: s for s in shots}
    refs = [n for n in rv["referenced_shots_derived"] if n in by_no]
    if refs:
        sel = refs[:6]
        inp = OrderedDict(**ep_header(rec), audit_focus=rv["item"], rows=[compact(by_no[n], COMPACT_COLS + ["asset_ids"]) for n in sel],
                          rows_truncated=len(refs) > 6, referenced_shots_total=len(refs))
        grounding = "shot_rows"
    else:
        st = rec["stats"]
        inp = OrderedDict(**ep_header(rec), audit_focus=rv["item"],
                          episode_stats=OrderedDict(shot_count=st["shot_count"], total_duration_s=st["total_duration_s"], avg_shot_s=st["avg_shot_s"],
                                                    shot_size_distribution_raw=st["shot_size_distribution_raw"], scene_runs=st["scene_runs_derived"]),
                          manual_stated=rec["stats_vs_manual_derived"])
        grounding = "episode_stats"
    out = OrderedDict(severity=rv["severity_raw"], item=rv["item"], issue=rv["issue"], suggested_fix=rv["suggested_fix"])
    P["row_to_critique"].append(pair(f"{rv['id']}__critique", "row_to_critique", rec, inp, out, rv["source_paths"], {"grounding_derived": grounding, "review_id": rv["id"]}))

# 7 storyboard revision V1 -> V2 (same episode, two Kronicle versions)
by_base = {}
for e in episodes:
    if e.get("version"):
        by_base.setdefault((e["show"], e["episode_base"]), {})[e["version"]] = e
for (show, base), vs in by_base.items():
    if "V1" in vs and "V2" in vs:
        e1, e2 = vs["V1"], vs["V2"]
        s1, s2 = shots_by_ep[(show, e1["episode"])], shots_by_ep[(show, e2["episode"])]
        n = max(len(s1), len(s2))
        for i in range(0, n, CHUNK):
            c1, c2 = s1[i:i + CHUNK], s2[i:i + CHUNK]
            if not c2: continue
            m2 = e2["manual"]["sections"] if e2["manual"] else {}
            P["storyboard_revision"].append(pair(f"{e2['id']}__rev_from_V1_{c2[0]['shot']}-{c2[-1]['shot']}", "storyboard_revision", e2,
                OrderedDict(show=show, episode=base, title=e2["title"], from_version="V1", to_version="V2",
                            v1_rows=[compact(x, COMPACT_COLS + ["asset_ids"]) for x in c1], v1_total_shots=len(s1), v2_total_shots=len(s2),
                            target_shots=[c2[0]["shot"], c2[-1]["shot"]],
                            v2_manual_visual_style=m2.get("s2_visual_style_camera", {}).get("text"),
                            v2_manual_scene_intent=m2.get("s4_scene_intent", {}).get("text"),
                            v2_manual_continuity=m2.get("s6_transitions_continuity", {}).get("text")),
                OrderedDict(rows=[compact(x, COMPACT_COLS + ["asset_ids"]) for x in c2]),
                e1["source_paths"][1:] + e2["source_paths"],
                {"alignment_derived": "rows aligned by shot number; V1 and V2 are different Kronicle storyboard versions of the same episode, not an edit log"}))

for k, v in P.items():
    write_jsonl(PAIRS / f"{k}.jsonl", v)
# rewrite episodes (scene links / beat ranges added)
write_jsonl(ROOT / "episodes.jsonl", episodes)
print(json.dumps({"episodes": len(episodes), "shots": len(shots_all), "reviews": len(reviews_all), "pairs": {k: len(v) for k, v in P.items()},
                  "skipped": [s["episode"] for s in skipped], "unmatched_scripts": unmatched_scripts}, indent=1))
