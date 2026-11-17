#!/usr/bin/env python3
"""Convert manual_dataset pair + rule records into chat fine-tuning JSONL.

Usage:
  python3 convert_to_chat.py                       # writes train_chat.jsonl + val_chat.jsonl
  python3 convert_to_chat.py --in-dir /workspace/manual_dataset --max-chars 60000 --drop-meta

Reads pairs/*.jsonl and rules.jsonl. The split comes from each pair's `split` field (held-out episodes: UW Ep3, UW Ep9, UW ioc4,
Durvasa 2 EP12, Kronicle Durvasa EP3, so no episode appears in both files). Rules always go to train.
Each line: {"messages":[system,user,assistant], "meta":{...}}.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

SYSTEM = (
    "You are the AI director's assistant for Kuku TV Hindi micro-dramas made in Kronicle. You write director's manuals "
    "(① theme & emotional arc, ② visual style & camera, ③ narrative structure with a beat table, ④ scene-by-scene intent, "
    "⑤ sound, ⑥ transitions & continuity anchors, ⑦ derivative asset pre-plan) and Kronicle storyboard tables "
    "(Shot | Frame Description | Scene | Associated Asset Names | Duration | Shot Size | Camera Movement | Character Action | "
    "Orientation | Spatial Relationship | Emotion | Dialogue | Sound Effects | Associated Asset IDs), and you critique them. "
    "Standing rules: dialogue is copied byte-for-byte from the script (never reworded, translated, added or dropped); never change "
    "shots, shot order, framing or durations beyond what the director asks; lock every character's position, facing and eyeline in "
    "every shot and carry it forward; no eye glow; the location must match its reference asset used as the background plate; any "
    "visible on-screen text is Hindi Devanagari only; sound is SFX and dialogue only, no music. Every visible or speaking character "
    "is associated with its asset, and the bound derivative matches the shot's state. Use only facts from the input; if something "
    "is unknown, say null. Never invent plot, dialogue or assets."
)

def dumps(o):
    return json.dumps(o, ensure_ascii=False, indent=1)

def load(p: Path):
    return [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]

def hdr(i):
    return f"Show: {i.get('show')}\nEpisode: {i.get('episode')}\nTitle: {i.get('title')}\n"

def build(rec):
    t, i, o = rec["pair_type"], rec["input"], rec["output"]
    if t == "script_to_manual":
        u = ("Write the complete director's manual (sections ①–⑦) for this episode script. Keep every dialogue line verbatim where you quote it.\n\n"
             + hdr(i) + "\nSCRIPT:\n" + i["script_text"])
        return u, o["manual_text"]
    if t == "script_to_manual_section":
        u = (f"From this episode script, write only section {i['target_heading']!r} of the director's manual.\n\n" + hdr(i) + "\nSCRIPT:\n" + i["script_text"])
        return u, o["section_text"]
    if t == "section_to_section":
        given = "\n\n".join(i["given_sections"].values())
        u = (f"Here are earlier sections of a director's manual. Write the next section: {i['target_heading']!r}. Stay consistent with what is given.\n\n"
             + hdr(i) + "\n" + given)
        return u, o["section_text"]
    if t == "manual_to_storyboard":
        u = (f"Using the director's manual context below, write storyboard rows for shots {i['target_shots'][0]}–{i['target_shots'][1]} "
             f"(scene '{i['storyboard_scene_value']}', episode has {i['episode_total_shots']} shots). Return a JSON list of rows with the table's columns. "
             "Continue from the previous shot's positions and state.\n\n" + dumps({k: v for k, v in i.items() if k not in ('show', 'episode', 'title')}) + "\n\n" + hdr(i))
        return u, dumps(o["rows"])
    if t == "scene_intent_to_shots":
        u = (f"Break this scene intent into storyboard shots {i['target_shots'][0]}–{i['target_shots'][1]} (part {i['part']}, the scene has {i['scene_total_shots']} shots). "
             "Return JSON: shot, duration, shot_size, camera_movement, frame_description, character_action, emotion, dialogue (verbatim), sound_effects.\n\n"
             + hdr(i) + f"\nSCENE: {i['scene_heading']}\n{i['scene_intent_text']}\n\nPREVIOUS SHOT: {dumps(i.get('previous_shot'))}")
        return u, dumps(o["shots"])
    if t == "beat_to_shot_plan":
        u = (f"Turn this beat into a shot plan for shots {i['target_shots'][0]}–{i['target_shots'][1]} (the beat covers shots {i['beat_shot_range'][0]}–{i['beat_shot_range'][1]}). "
             "Follow the episode's camera grammar. Return JSON: shot, duration, shot_size, camera_movement, frame_description, dialogue (verbatim).\n\n"
             + hdr(i) + "\nBEAT ROW: " + dumps(i["beat_row"]) + "\n\nCAMERA GRAMMAR (manual ②):\n" + (i.get("camera_grammar") or "null"))
        return u, dumps(o["shot_plan"])
    if t == "row_to_critique":
        u = (f"Audit this storyboard for: {i['audit_focus']}. Return JSON with severity, item, issue, suggested_fix.\n\n" + hdr(i) + "\n"
             + dumps({k: v for k, v in i.items() if k not in ('show', 'episode', 'title', 'audit_focus')}))
        return u, dumps(o)
    if t == "script_to_storyboard":
        u = (f"Write storyboard rows for shots {i['target_shots'][0]}–{i['target_shots'][1]} of {i['total_shots']} from this script, using the columns "
             f"{i['columns_available']}. Dialogue verbatim. Return a JSON list.\n\n" + hdr(i) + "\nSCRIPT:\n" + i["script_text"]
             + "\n\nPREVIOUS SHOT: " + dumps(i.get("previous_shot")))
        return u, dumps(o["rows"])
    if t == "storyboard_revision":
        u = (f"Revise the {i['from_version']} storyboard rows below into the {i['to_version']} rows for shots {i['target_shots'][0]}–{i['target_shots'][1]} "
             f"(V1 has {i['v1_total_shots']} shots, V2 has {i['v2_total_shots']}), following the V2 director's manual context. Dialogue verbatim. Return a JSON list.\n\n"
             + hdr(i) + "\n" + dumps({k: v for k, v in i.items() if k not in ('show', 'episode', 'title')}))
        return u, dumps(o["rows"])
    raise ValueError(t)

def rule_example(r):
    u = f"What is the {r['category'].replace('_', ' ')} rule '{r['id']}' for director's manuals / storyboards, and where does it come from?"
    a = {"rule": r["rule_text"], "category": r["category"], "applies_to": r.get("applies_to"), "origin": r["origin"],
         "seen_in": r.get("cited_episodes"), "evidence": [{"where": e.get("episode") or e["source_path"], "quote": e["quote"]} for e in r["evidence"][:3]],
         "notes": r.get("notes")}
    return u, dumps(a)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--train-out", default=None)
    ap.add_argument("--val-out", default=None)
    ap.add_argument("--max-chars", type=int, default=0, help="drop examples whose user+assistant text exceeds this (0 = keep all)")
    ap.add_argument("--drop-meta", action="store_true")
    a = ap.parse_args()
    d = Path(a.in_dir)
    train, val, dropped = [], [], 0
    for p in sorted((d / "pairs").glob("*.jsonl")):
        for rec in load(p):
            u, s = build(rec)
            if a.max_chars and len(u) + len(s) > a.max_chars:
                dropped += 1; continue
            ex = {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": u}, {"role": "assistant", "content": s}]}
            if not a.drop_meta:
                ex["meta"] = {"id": rec["id"], "pair_type": rec["pair_type"], "show": rec["show"], "episode": rec["episode"], "source_paths": rec["source_paths"]}
            (val if rec["split"] == "val" else train).append(ex)
    for r in load(d / "rules.jsonl"):
        u, s = rule_example(r)
        ex = {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": u}, {"role": "assistant", "content": s}]}
        if not a.drop_meta:
            ex["meta"] = {"id": r["id"], "pair_type": "rule", "show": None, "episode": None, "source_paths": r["source_paths"]}
        train.append(ex)
    for path, rows in ((a.train_out or d / "train_chat.jsonl", train), (a.val_out or d / "val_chat.jsonl", val)):
        with open(path, "w", encoding="utf-8") as f:
            for ex in rows:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"train={len(train)} val={len(val)} dropped_by_max_chars={dropped}")

if __name__ == "__main__":
    main()
