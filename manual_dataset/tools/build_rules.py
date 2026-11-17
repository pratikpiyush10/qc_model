#!/usr/bin/env python3
"""Distil craft rules with automatically extracted evidence quotes. A distilled rule is kept only if >=2 episodes evidence it.
rule_text is a derived summary (labelled origin=distilled_*); every evidence quote is verbatim from the cited file."""
import json, re
from collections import OrderedDict, defaultdict
from pathlib import Path
ROOT = Path("/workspace/manual_dataset")
eps = [json.loads(l) for l in open(ROOT / "episodes.jsonl")]
shots = [json.loads(l) for l in open(ROOT / "shots.jsonl")]
revs = [json.loads(l) for l in open(ROOT / "reviews.jsonl")]
SEC = {"s1": "s1_theme_emotional_arc", "s2": "s2_visual_style_camera", "s3": "s3_narrative_structure_beats", "s4": "s4_scene_intent",
       "s5": "s5_sound", "s6": "s6_transitions_continuity", "s7": "s7_derivative_assets", "any": None}

def clip(s, n=320):
    s = s.strip()
    return s if len(s) <= n else s[:n].rstrip() + " …[clipped]"

def window(line, rx, n=320):
    line = line.strip()
    if len(line) <= n:
        return line
    m = re.search(rx, line, re.I)
    if not m or m.start() < n - 60:
        return clip(line, n)
    a = max(0, m.start() - n // 2)
    return "…" + line[a:a + n].strip() + " …[clipped]"

def manual_evidence(sec, rx, maxn=6):
    out = []
    for e in eps:
        if not e["manual"]:
            continue
        if sec == "any":
            text = e["manual"]["manual_text_clean"]
        else:
            s = e["manual"]["sections"].get(SEC[sec])
            if not s:
                continue
            text = "\n".join(s["text"].split("\n")[1:])  # skip the section heading line
        lines = [l for l in text.split("\n") if re.search(rx, l, re.I if rx.islower() else 0)]
        if lines:
            best = next((l for l in lines if len(l.strip()) >= 40), lines[0])
            out.append({"show": e["show"], "episode": e["episode"], "source_path": e["source_paths"][0], "section": SEC[sec] or "manual", "quote": window(best, rx)})
    return out

def review_evidence(rx):
    out, seen = [], set()
    for r in revs:
        if r["review_kind"] != "kronicle_storyboard_or_plan_audit":
            continue
        blob = " ".join(x for x in [r["item"], r["issue"], r["suggested_fix"]] if x)
        if re.search(rx, r["item"] or "", re.I) and r["episode"] not in seen:
            seen.add(r["episode"])
            out.append({"show": r["show"], "episode": r["episode"], "source_path": r["source_paths"][0], "section": "REVIEW ROWS", "review_id": r["id"],
                        "quote": clip(f"{r['severity_raw']} | {r['item']} | {r['issue']} | {r['suggested_fix']}", 420)})
    return out

def shot_evidence(col, rx):
    out, seen = [], set()
    for s in shots:
        v = s["columns"].get(col) or ""
        if re.search(rx, v) and (s["show"], s["episode"]) not in seen:
            seen.add((s["show"], s["episode"]))
            out.append({"show": s["show"], "episode": s["episode"], "source_path": s["source_paths"][0], "section": f"storyboard.{col}", "shot_id": s["id"], "quote": clip(v)})
    return out

def file_evidence(path, rx, maxn=3):
    out = []
    for i, line in enumerate(open(path, encoding="utf-8"), 1):
        if re.search(rx, line, re.I):
            out.append({"show": None, "episode": None, "source_path": path, "section": f"line {i}", "quote": window(line, rx)})
            if len(out) >= maxn:
                break
    return out

R = []
def rule(rid, cat, text, ev, origin="distilled_from_manual_patterns", applies="director_manual", notes=None, min_eps=2):
    eps_cited = sorted(set(f"{x['show']}|{x['episode']}" for x in ev if x.get("episode")))
    # order evidence so each show is represented before repeats (first quote per show, then the rest)
    seen, first, rest = set(), [], []
    for x in ev:
        (rest if x.get("show") in seen else first).append(x); seen.add(x.get("show"))
    ev = first + rest
    if origin.startswith("distilled") and len(eps_cited) < min_eps:
        print("DROPPED (evidence < 2 episodes):", rid, eps_cited); return
    R.append(OrderedDict(id=rid, record_type="rule", category=cat, applies_to=applies, origin=origin,
                         rule_text=text, rule_text_is_derived=origin != "verbatim", cited_episodes=eps_cited,
                         evidence_count=len(ev), evidence=ev[:6], notes=notes,
                         source_paths=sorted(set(x["source_path"] for x in ev))))

# ---- manual structure
full7 = [{"show": e["show"], "episode": e["episode"], "source_path": e["source_paths"][0], "section": "section_order",
          "quote": " | ".join(e["manual"]["sections"][k]["heading"] for k in e["manual"]["section_order"][:7])}
         for e in eps if e["manual"] and all(k in e["manual"]["sections"] for k in SEC.values() if k)]
rule("dm_structure_seven_sections", "manual_structure",
     "Write the director's manual as seven sections in fixed order: ① theme & emotional arc, ② visual style & camera, ③ narrative structure with a beat/pacing table, ④ scene-by-scene emotion & visual intent, ⑤ sound, ⑥ transitions & continuity anchors, ⑦ derivative asset pre-plan. Optional ⑧ holds execution steps or look notes.",
     full7, notes="Ep14.2, Ep16, Ep8, ioc1 and ioc2 add an eighth section (execution plan, photoreal look, or Ninni's director rules).")
rule("dm_core_theme_one_line", "theme", "Open ① with a single-sentence Core Theme that states the moral thesis of the episode (what is earned vs. what is inherited/imposed).",
     manual_evidence("s1", r"^Core Theme"))
rule("dm_emotional_arc_tiers", "theme", "After the theme, give the emotional arc as ordered tiers or a through-line, each tied to a visible physical behaviour (posture, breath, hands), not abstract feelings.",
     manual_evidence("s1", r"Emotional (Arc|Through-Line|Through Line)|Tier 1"))
rule("dm_audience_takeaway", "theme", "State the intended audience takeaway / emotional strategy, usually ending on a hook or cliffhanger that pulls into the next episode.",
     manual_evidence("s1", r"Audience|Takeaway|cliffhanger|Hook"))
rule("dm_format_declared", "visual_style", "Declare the frame format in ② (native 9:16 vertical, or 16:9 with all key action inside a central 9:16 safe area) and compose for it.",
     manual_evidence("any", r"9:16"))
rule("dm_three_layer_depth", "visual_style", "Specify three-layer spatial depth for the show: what lives in the foreground, midground (the acting subject) and background (architecture/crowds).",
     manual_evidence("s2", r"Three-Layer|3-Layer|three-layer|3-layer|Foreground"))
rule("dm_composition_modes_tied_to_beats", "visual_style", "Name each compositional mode (symmetry, rule of thirds with negative space, diagonal, frame-within-frame) and attach it to the specific story moment it serves.",
     manual_evidence("s2", r"Symmetric|Symmetrical|Rule of Thirds|Diagonal|Frame-Within|Frame Within|frame-within"))
rule("dm_camera_move_purpose", "camera", "Give every camera move a dramatic job (e.g. push-in on a dialogue turn or impact, pull-back to reveal isolation, tracking to show inevitability) rather than listing moves generically.",
     manual_evidence("s2", r"Push-In|push-in|Push In|Pull-Back|pull-back|Dolly"))
rule("dm_camera_exclusions_explicit", "camera", "State explicitly which camera behaviours are banned or reserved for single beats (handheld shake, whip-pans, crash zooms).",
     manual_evidence("s2", r"[Hh]andheld|[Ww]hip"))
rule("dm_beat_table", "narrative_structure", "In ③, include a beat/section table with one row per beat: name, scene, core event, shots or shot range, duration, emotional intensity, and pacing/camera rhythm; close with a Total row when shot counts are given.",
     [{"show": e["show"], "episode": e["episode"], "source_path": e["source_paths"][0], "section": "s3 beat table header", "quote": " | ".join(e["manual"]["beat_table"]["header"])}
      for e in eps if e["manual"] and e["manual"]["beat_table"]])
rule("dm_intensity_curve", "narrative_structure", "Give each beat an explicit emotional intensity (percent, x/10, or a labelled density) so the escalation curve is visible, and describe the curve in one line.",
     manual_evidence("s3", r"Emotional (Curve|Intensity|Density)|\d+/10|\d+%"))
rule("dm_turning_points_visual", "narrative_structure", "List key turning points as concrete visual executions (what the hand, prop or camera does), not as plot summaries.",
     manual_evidence("s3", r"Turning Point|Turn \d"))
rule("dm_scene_blocks_with_ranges", "scene_intent", "In ④, open each scene block with a heading naming the scene, and where possible its shot range and duration, so the storyboard can be checked against it.",
     manual_evidence("s4", r"^Scene \d+.*\(Shots? \d+|^Scene \d+.*\(\d\d:\d\d"))
rule("dm_scene_emotion_acting", "scene_intent", "Each scene block states the emotional objective and acting notes per character, plus the camera/visual intent for that scene.",
     manual_evidence("s4", r"Emotional (Objective|Goal|Target)|Acting Notes|Emotion Target|Frame Intent|Visual Intent|Camera Intent|Key Visual"))
rule("dm_spatial_distance_design", "scene_intent", "For each scene, design spatial staging and distance: how far apart characters are, who occupies foreground vs. deep background, and how that distance changes with the power or emotional shift.",
     manual_evidence("any", r"Distance Design|Spatial Staging:"))
rule("dm_scene_atmosphere_line", "scene_intent", "Give each scene a one-line atmospheric direction (the felt mood of the space) alongside its emotional goal.",
     manual_evidence("any", r"Atmospheric Direction|Atmosphere:"))
rule("dm_sound_concrete_diegetic", "sound", "Write sound as concrete physical (diegetic) events grouped as ambience and action SFX: what material makes which sound.",
     manual_evidence("s5", r"Ambient|Ambience|Action SFX|SFX|Foley"))
rule("dm_sound_designed_silence", "sound", "Plan silence deliberately: name the exact moments where ambience drops out and what single sound is left.",
     manual_evidence("s5", r"[Ss]ilence|cutout|drops? (away|out)"))
rule("dm_transitions_motivated", "transitions", "In ⑥, specify each scene-to-scene transition as a motivated cut (hard cut on an impact or line, match cut on a shape/flash) and keep dissolves rare.",
     manual_evidence("s6", r"Scene \d+ (to|→) Scene \d+|Inter-Scene|[Hh]ard [Cc]ut|[Mm]atch [Cc]ut"))
rule("dm_continuity_anchors_per_character", "continuity", "List continuity anchors per character and key prop: costume, wound, prop state and hand, so every later shot can be checked against them.",
     manual_evidence("s6", r"Continuity Anchor|Anchors|^[A-Z][a-zA-Z ]+:\s.*(cuff|wound|sword|costume|angrakha|sari|armou?r)"))
rule("dm_derivative_table", "derivative_assets", "In ⑦, list derivative assets as a table: parent Asset Name | Derivative State | Reason / narrative appearance (with the scenes or shots that need it). Parent names must match existing assets exactly.",
     [{"show": e["show"], "episode": e["episode"], "source_path": e["source_paths"][0], "section": "s7 table header", "quote": " | ".join(e["manual"]["derivative_asset_table"]["header"])}
      for e in eps if e["manual"] and e["manual"]["derivative_asset_table"]])
rule("dm_derivative_reverse_views", "derivative_assets", "Plan reverse/angle views of locations as derivatives whenever the storyboard needs the camera looking the other way.",
     manual_evidence("s7", r"[Rr]everse|[Aa]ngle|[Vv]iew"))
rule("dm_derivative_reuse_no_turnarounds", "derivative_assets", "Reuse existing derivatives instead of duplicating them, and do not plan turnaround / multi-view grid sheets; say so when no new derivative is needed.",
     manual_evidence("s7", r"[Rr]eused existing|No new derivative|already possess|turnaround|multi-view|[Pp]runed"))
rule("dm_transient_effects_in_video", "derivative_assets", "Transient effects (glows flickering, torches guttering, cracks spreading) are handled in the video prompt, not as new asset cards.",
     manual_evidence("s7", r"[Hh]andled in video"), min_eps=2)

# ---- storyboard / review patterns
rule("sb_field_completeness", "storyboard", "Fill every storyboard column on every row (description, scene, asset names, duration, shot size, camera move, action, orientation, spatial relation, emotion, dialogue, sound, asset IDs).",
     review_evidence(r"[Ff]ield [Cc]ompleteness"), origin="distilled_from_kronicle_reviews", applies="storyboard")
rule("sb_visible_characters_associated", "storyboard", "Every character visible or speaking in a shot must be in that row's associated asset names and IDs; extras that look like a known asset should be linked or explicitly kept generic.",
     review_evidence(r"[Vv]isible [Cc]haracter|Asset match|Asset bindings|Scene asset association|Insert shot association|Cut-away"), origin="distilled_from_kronicle_reviews", applies="storyboard")
rule("sb_derivative_state_matches_shot", "storyboard", "Bind the derivative whose state matches the shot (sheathed vs drawn weapon, wounded vs clean, reverse view for reverse-angle setups); switch bindings at the shot where the state changes.",
     review_evidence(r"[Pp]arent/child|Derivative Selection|Weapon State|Angle Derivative"), origin="distilled_from_kronicle_reviews", applies="storyboard")
rule("sb_orientation_spatial_columns", "storyboard", "Keep Orientation (each character's facing/eyeline) and Spatial Relationship (position in frame, depth layer) in their own columns, per character, every row.",
     review_evidence(r"[Oo]rientation|[Ss]patial"), origin="distilled_from_kronicle_reviews", applies="storyboard")
rule("sb_axis_eyeline_continuity", "storyboard", "Hold screen direction and eyelines across cuts (axis, trajectory, OTS geometry); a character's travel direction does not flip without a shown reason.",
     review_evidence(r"Axis|Eyeline|Trajectory|OTS|Orientation Continuity"), origin="distilled_from_kronicle_reviews", applies="storyboard")
rule("sb_dialogue_duration_headroom", "storyboard", "Give each dialogue shot enough duration for the full line at a natural speaking rate plus a pause/headroom; lengthen the shot rather than clip speech.",
     review_evidence(r"[Dd]uration sound|Dialogue (Pacing|Duration)|Pacing & Duration") + manual_evidence("any", r"words per second"), origin="distilled_from_kronicle_reviews", applies="storyboard")
rule("sb_total_duration_matches_target", "storyboard", "The row durations must sum to the episode's stated target; recompute after every edit and reconcile the manual's stated total.",
     review_evidence(r"Total Duration|Duration baseline|Headroom"), origin="distilled_from_kronicle_reviews", applies="storyboard", min_eps=1,
     notes="Only Ep16 audits flag this, but stats_vs_manual_derived shows the stated totals vs. row sums for every episode.")
rule("sb_shot_size_variety", "storyboard", "Avoid three consecutive shots of the same size (e.g. three close-ups in a row) and repetitive camera moves; vary the middle shot.",
     review_evidence(r"[Ss]hot-[Ss]ize|[Cc]amera move variety"), origin="distilled_from_kronicle_reviews", applies="storyboard")
rule("sb_split_granularity", "storyboard", "Split shots on a change of perspective or action, not on every micro-reaction; merge static micro-splits.",
     review_evidence(r"[Ss]plitting granularity|[Pp]acing soundness|Pacing"), origin="distilled_from_kronicle_reviews", applies="storyboard")
rule("sb_no_lighting_in_fields", "storyboard", "Do not write lighting, colour temperature or grading into storyboard fields; light comes from the locked scene reference images.",
     review_evidence(r"[Ll]ighting|colou?r grade") + manual_evidence("any", r"omitting explicit lighting|lighting, colou?r temperature"), origin="distilled_from_kronicle_reviews", applies="storyboard")
rule("sb_script_coverage_attribution", "storyboard", "Every script line appears in the table, attributed to the speaker the script names (or the change is flagged as an option for the director).",
     review_evidence(r"Script (coverage|vs)"), origin="distilled_from_kronicle_reviews", applies="storyboard")
rule("sb_action_carries_continuity", "storyboard", "Write Character Action as the physical sequence inside the shot and carry continuity forward explicitly (e.g. a 'Continuity:' note or '(Continuing previous shot…)').",
     shot_evidence("character_action", r"Continuity:|Continu(ing|ation) (from )?previous"), origin="distilled_from_storyboard_patterns", applies="storyboard")
rule("sb_sound_layered_plus", "storyboard", "Write the Sound column as concrete layered effects joined with '+', with no music.",
     shot_evidence("sound_effects", r" \+ "), origin="distilled_from_storyboard_patterns", applies="storyboard",
     notes="Some rows name crowd or temple chants (e.g. uw_Ep1_s002, uw_Ep5_s035, uw_Ep11_s003); the UW prompt style guide bans chanting melody, so treat chants as spoken/shouted only.")
rule("sb_dialogue_speaker_prefix", "storyboard", "Write Dialogue as 'Speaker: line' copied verbatim from the script; write 'None'/'No dialogue' for silent shots.",
     shot_evidence("dialogue", r"^[^:]{2,40}: "), origin="distilled_from_storyboard_patterns", applies="storyboard")

# ---- Pratik's production rules (from memory / production docs)
SG = "/workspace/uw_continuity/UW_PROMPT_STYLE_GUIDE.md"; IOC2 = "/workspace/manual_dataset/raw/uw_ioc2_manual.txt"; ML = "/workspace/uw_ep10/MASTER_LOCKS_E10.md"
V2 = "/workspace/uw_ioc/IOC2_video_prompt.txt"; ML9 = "/workspace/uw_ep9/MASTER_LOCKS.md"; CS = "/workspace/uw_continuity/UW_CONTINUITY_SHEET.md"
prod = [
    ("prod_dialogue_byte_for_byte", "dialogue", "Dialogue stays byte-for-byte as in the script: no rewording, translating, adding or dropping lines. Only the speaking character's mouth moves.",
     [(IOC2, r"word for word|mouth moves"), (SG, r"never reworded"), (ML, r"no rewording"), (V2, r"exactly as written")]),
    ("prod_no_shot_changes_unless_asked", "shot_structure", "Never change shots, shot order, shot size, framing or durations beyond exactly what Pratik or Ninni ask for.",
     [(IOC2, r"not changed once approved"), (SG, r"shots and durations unchanged")]),
    ("prod_positions_lock_every_shot", "continuity", "Positions lock in every shot: each character's side, depth, posture and facing is written in every shot and carried from shot to shot and track to track.",
     [(IOC2, r"Positions line|Positions lock"), (SG, r"Name every character in every shot")]),
    ("prod_no_eye_glow", "visual", "No eye glow on any character (natural eyes only), unless the director explicitly approves an exception.",
     [(IOC2, r"No eye glow"), (SG, r"no glowing eyes|NO EYE GLOW"), (V2, r"No eye glow")]),
    ("prod_location_matches_plate", "location", "The rendered location must match its location reference asset exactly, used as the background plate; no redesigned layouts or mixed conflicting location refs.",
     [(IOC2, r"background plate"), (V2, r"background plate")]),
    ("prod_devanagari_visible_text", "visible_text", "Any visible on-screen text in assets or frames (scrolls, decrees, banners, inscriptions) is Hindi Devanagari only.",
     [(V2, r"Devanagari writing only"), (ML9, r"Devanagari"), (CS, r"Devanagari")]),
    ("prod_no_music", "sound", "No music in sound: SFX and dialogue only; no score, songs, singing or chanting melody, and no musical wording in prompts.",
     [(IOC2, r"No music"), (SG, r"no music, score|musical wording"), (V2, r"No music")]),
]
for rid, cat, text, srcs in prod:
    ev = []
    for path, rx in srcs:
        if Path(path).exists():
            ev += file_evidence(path, rx, 1)
    R.append(OrderedDict(id=rid, record_type="rule", category=cat, applies_to="all_kuku_tv_shows", origin="pratik_production_rule",
                         rule_text=text, rule_text_is_derived=True, cited_episodes=[], evidence_count=len(ev), evidence=ev,
                         notes=("Standing rule from Pratik's production memory; evidence lines show where it is written in production files. "
                                + ("Dialogue script itself follows the episode lock: UW video prompts used Devanagari (style guide, Ep9/Ep10 master locks), Kronicle storyboards store Roman Hindi, and Durvasa 2 prompt QC (kronicle/qc_EP12.md) required Roman. Keep whichever the episode locks, verbatim." if rid == "prod_devanagari_visible_text" else "")).strip(),
                         source_paths=sorted(set(x["source_path"] for x in ev)) or [SG]))

with open(ROOT / "rules.jsonl", "w", encoding="utf-8") as f:
    for r in R:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(ROOT / "rules.md", "w", encoding="utf-8") as f:
    f.write("# Director's-manual & storyboard craft rules\n\nDistilled from the real manuals, storyboards and Kronicle review rows in this dataset. Rule text is a derived summary; every evidence quote below is verbatim from the cited file. A distilled rule was kept only if at least two episodes evidence it (exceptions are marked). Full evidence is in `rules.jsonl`.\n\n")
    cur = None
    for r in R:
        grp = {"pratik_production_rule": "Production rules (Pratik / Ninni)", "distilled_from_kronicle_reviews": "Storyboard rules (from Kronicle review rows)",
               "distilled_from_storyboard_patterns": "Storyboard rules (from table patterns)"}.get(r["origin"], "Director's manual rules")
        if grp != cur:
            f.write(f"\n## {grp}\n\n"); cur = grp
        f.write(f"### `{r['id']}` ({r['category']})\n{r['rule_text']}\n\n")
        if r["cited_episodes"]:
            lab = lambda x: ("UW " if x.startswith("Ultimate") else "Durvasa 2 " if x.startswith("Maharishi Durvasa 2") else "Durvasa ") + x.split("|")[1]
            f.write(f"Seen in: {', '.join(lab(x) for x in r['cited_episodes'])}\n\n")
        for e in r["evidence"][:3]:
            where = f"{e.get('episode') or Path(e['source_path']).name} · {e['section']}"
            f.write(f"- {where}: \"{e['quote']}\"\n")
        if r["notes"]:
            f.write(f"\nNote: {r['notes']}\n")
        f.write("\n")
print(len(R), "rules")
