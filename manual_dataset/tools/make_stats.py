#!/usr/bin/env python3
import json, glob, os
from collections import Counter
from pathlib import Path
D = Path("/workspace/manual_dataset")
L = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
eps, shots, revs, rules = L(D/"episodes.jsonl"), L(D/"shots.jsonl"), L(D/"reviews.jsonl"), L(D/"rules.jsonl")
tr, va = L(D/"train_chat.jsonl"), L(D/"val_chat.jsonl")
o = ["# Dataset statistics", "", "All numbers computed by `tools/make_stats.py` from the JSONL files. Buckets are derived labels (see schema.json).", ""]
o += ["## Episodes", "", "| Show | Ep | Version | Title (derived) | Manual | Shots | Row-sum s | Manual says (shots / s) | Dialogue shots | Scene runs | Reviews | Script paired | Split |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for e in eps:
    st = e["stats"]; sm = e.get("stats_vs_manual_derived") or {}
    o.append(f"| {e['show']} | {e.get('episode_base') or e['episode']} | {e.get('version') or '—'} | {e['title'] or '—'} | {'yes' if e['has_manual'] else 'no'} | {st['shot_count']} | {st['total_duration_s']:g} | "
             f"{sm.get('stated_shot_count') or '—'} / {sm.get('stated_duration_s') or '—'} | {st['dialogue_shot_count']} | {len(st['scene_runs_derived'])} | {st['review_count']} | "
             f"{os.path.relpath(e['primary_script_path'].split('#')[0], '/workspace') + ('#' + e['primary_script_path'].split('#')[1] if '#' in e['primary_script_path'] else '') if e['primary_script_path'] else '—'} | {e['split']} |")
sc = Counter(s["show"] for s in shots)
o += ["", f"Totals: {len(eps)} episode records ({sum(e['has_manual'] for e in eps)} with a manual), {len(shots)} shots (" + ", ".join(f"{k} {v}" for k, v in sc.items()) + "), "
      f"{sum(s['parsed_derived']['duration_s'] or 0 for s in shots):g} s of storyboarded time, {len(revs)} review rows.", ""]
def dist(title, c, n=20):
    tot = sum(c.values())
    return [f"### {title}", "", "| Value | Count | % |", "|---|---|---|"] + [f"| {k} | {v} | {100*v/tot:.1f} |" for k, v in c.most_common(n)] + [""]
o += ["## Shot craft distributions (all shows)", ""]
o += dist("Shot size bucket (derived)", Counter(s["parsed_derived"]["shot_size_bucket"] for s in shots))
o += dist("Camera move buckets (derived, multi-label)", Counter(b for s in shots for b in s["parsed_derived"]["camera_move_buckets"]))
o += dist("Most common raw Shot Size strings", Counter(s["columns"].get("shot_size") or s["columns"].get("shot_size_and_camera_merged_raw") for s in shots), 15)
o += dist("Most common raw Camera Movement strings", Counter(s["columns"].get("camera_movement") for s in shots if s["columns"].get("camera_movement")), 15)
d = [s["parsed_derived"]["duration_s"] for s in shots if s["parsed_derived"]["duration_s"] is not None]
o += ["### Shot duration (s)", "", f"min {min(d):g} · median {sorted(d)[len(d)//2]:g} · mean {sum(d)/len(d):.2f} · max {max(d):g}", ""]
o += dist("Review severity (derived)", Counter(r["severity_level_derived"] or "n/a (prompt QC)" for r in revs))
pc = Counter(); ps = Counter()
for f in sorted(glob.glob(str(D/"pairs/*.jsonl"))):
    for p in L(f):
        pc[p["pair_type"]] += 1; ps[(p["pair_type"], p["split"])] += 1
o += ["## Training pairs", "", "| Pair type | Total | Train | Val |", "|---|---|---|---|"]
for k, v in sorted(pc.items()):
    o.append(f"| {k} | {v} | {ps[(k,'train')]} | {ps[(k,'val')]} |")
o += [f"| rules (chat) | {len(rules)} | {len(rules)} | 0 |", ""]
ch = [len(m["content"]) for ex in tr + va for m in ex["messages"][1:]]
o += ["## Chat files", "", f"train_chat.jsonl: {len(tr)} examples · val_chat.jsonl: {len(va)} examples (val episodes: UW Ep3, Ep9, ioc4; Durvasa 2 EP12; Kronicle Durvasa EP3).",
      f"User+assistant characters per example: median {sorted([len(ex['messages'][1]['content'])+len(ex['messages'][2]['content']) for ex in tr+va])[len(tr+va)//2]:,}, "
      f"max {max(len(ex['messages'][1]['content'])+len(ex['messages'][2]['content']) for ex in tr+va):,}. Use `convert_to_chat.py --max-chars N` to cap length.", ""]
o += ["## Rules", "", f"{len(rules)} rules: " + ", ".join(f"{k} {v}" for k, v in Counter(r['origin'] for r in rules).items()), ""]
open(D/"stats.md", "w").write("\n".join(o))
print("stats.md written")
