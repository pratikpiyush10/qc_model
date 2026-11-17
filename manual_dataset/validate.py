#!/usr/bin/env python3
"""Validate manual_dataset: schema, unique ids, verbatim fidelity against raw sources, split hygiene, chat format.
python3 validate.py [--in-dir DIR]   -> exit 1 on any error. Uses `jsonschema` if installed, else a built-in subset validator."""
from __future__ import annotations
import argparse, json, sys
from collections import Counter
from pathlib import Path

def mini_validate(inst, schema, root, path="$"):
    errs = []
    if "$ref" in schema:
        ref = schema["$ref"].split("/")[-1]
        return mini_validate(inst, root["$defs"][ref], root, path)
    if "oneOf" in schema:
        oks = [s for s in schema["oneOf"] if not mini_validate(inst, s, root, path)]
        if len(oks) != 1:
            errs.append(f"{path}: matched {len(oks)} of oneOf")
        return errs
    t = schema.get("type")
    if t:
        ts = t if isinstance(t, list) else [t]
        pm = {"string": str, "integer": int, "number": (int, float), "object": dict, "array": list, "boolean": bool, "null": type(None)}
        ok = any((isinstance(inst, pm[x]) and not (x in ("integer", "number") and isinstance(inst, bool))) for x in ts)
        if not ok:
            return [f"{path}: type {type(inst).__name__} not in {ts}"]
    if "const" in schema and inst != schema["const"]:
        errs.append(f"{path}: != const {schema['const']}")
    if "enum" in schema and inst not in schema["enum"]:
        errs.append(f"{path}: {inst!r} not in enum")
    if isinstance(inst, dict):
        for k in schema.get("required", []):
            if k not in inst:
                errs.append(f"{path}: missing {k}")
        for k, s in schema.get("properties", {}).items():
            if k in inst:
                errs += mini_validate(inst[k], s, root, f"{path}.{k}")
        ap = schema.get("additionalProperties")
        if isinstance(ap, dict):
            for k, v in inst.items():
                if k not in schema.get("properties", {}):
                    errs += mini_validate(v, ap, root, f"{path}.{k}")
    if isinstance(inst, list):
        if len(inst) < schema.get("minItems", 0):
            errs.append(f"{path}: fewer than {schema['minItems']} items")
        if "items" in schema:
            for n, v in enumerate(inst):
                errs += mini_validate(v, schema["items"], root, f"{path}[{n}]")
    return errs

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--in-dir", default=str(Path(__file__).resolve().parent)); a = ap.parse_args()
    d = Path(a.in_dir); root = json.load(open(d / "schema.json"))
    try:
        import jsonschema
        V = jsonschema.Draft202012Validator(root)
        val = lambda rec, defn: [e.message for e in jsonschema.Draft202012Validator({**root, "$ref": f"#/$defs/{defn}"}).iter_errors(rec)][:3]
    except Exception:
        val = lambda rec, defn: mini_validate(rec, root["$defs"][defn], root)
    errors, counts = [], {}
    files = {"episodes.jsonl": "episode", "shots.jsonl": "shot", "reviews.jsonl": "review", "rules.jsonl": "rule",
             "train_chat.jsonl": "chat_example", "val_chat.jsonl": "chat_example"}
    files.update({f"pairs/{p.name}": "pair" for p in sorted((d / "pairs").glob("*.jsonl"))})
    data = {}
    for f, defn in files.items():
        rows = []
        for n, line in enumerate(open(d / f, encoding="utf-8"), 1):
            try:
                r = json.loads(line)
            except Exception as e:
                errors.append(f"{f}:{n} bad JSON {e}"); continue
            for e in val(r, defn):
                errors.append(f"{f}:{n} {e}")
            rows.append(r)
        data[f] = rows; counts[f] = len(rows)
        ids = [r.get("id") for r in rows if "id" in r]
        dup = [k for k, v in Counter(ids).items() if v > 1]
        if dup:
            errors.append(f"{f}: duplicate ids {dup[:5]}")
    # verbatim fidelity
    raw_cache = {}
    def raw(p):
        if p not in raw_cache:
            raw_cache[p] = open(p.split("#")[0], encoding="utf-8").read()
        return raw_cache[p]
    nchk = 0
    for s in data["shots.jsonl"]:
        src = raw(s["source_paths"][0])
        for k, v in s["columns"].items():
            if v and v not in src:
                errors.append(f"shot {s['id']} column {k} not verbatim in source"); break
            nchk += 1
    for r in data["reviews.jsonl"]:
        for k in ("item", "issue", "suggested_fix"):
            v = r.get(k)
            if v and v not in raw(r["source_paths"][0]):
                errors.append(f"review {r['id']} {k} not verbatim")
            nchk += 1
    for e in data["episodes.jsonl"]:
        if e["manual"]:
            for name, sec in e["manual"]["sections"].items():
                if sec["text"] not in e["manual_raw"]:
                    errors.append(f"episode {e['id']} section {name} not verbatim")
                nchk += 1
            if e["manual_raw"] != raw(e["source_paths"][0]):
                errors.append(f"episode {e['id']} manual_raw differs from file")
    shots_by_id = {(s["show"], s["episode"], str(s["shot"])): s for s in data["shots.jsonl"]}
    for f, rows in data.items():
        if not f.startswith("pairs/"):
            continue
        for p in rows:
            out = p["output"]
            lst = out.get("rows") or out.get("shots") or out.get("shot_plan") or []
            for row in lst:
                s = shots_by_id.get((p["show"], p["episode"], str(row.get("shot"))))
                if s is None:
                    errors.append(f"{p['id']}: output shot {row.get('shot')} not in shots.jsonl"); continue
                for k, v in row.items():
                    if s["columns"].get(k) != v:
                        errors.append(f"{p['id']}: shot {row.get('shot')} {k} differs from shots.jsonl"); break
                nchk += 1
            if "v1_rows" in p["input"]:
                ep1 = p["input"]["episode"] + "V1"
                for row in p["input"]["v1_rows"]:
                    s = shots_by_id.get((p["show"], ep1, str(row.get("shot"))))
                    if s is None or any(s["columns"].get(k) != val for k, val in row.items()):
                        errors.append(f"{p['id']}: v1 input shot {row.get('shot')} differs from shots.jsonl")
                    nchk += 1
            for k in ("manual_text", "section_text"):
                if k in out:
                    e = next(x for x in data["episodes.jsonl"] if x["show"] == p["show"] and x["episode"] == p["episode"])
                    if out[k] not in e["manual_raw"]:
                        errors.append(f"{p['id']}: {k} not verbatim in manual_raw")
                    nchk += 1
    # split hygiene
    sp = {}
    for f, rows in data.items():
        if f.startswith("pairs/"):
            for p in rows:
                sp.setdefault((p["show"], p.get("episode_base") or p["episode"]), set()).add(p["split"])
    leak = [k for k, v in sp.items() if len(v) > 1]
    if leak:
        errors.append(f"episodes in both splits: {leak}")
    # chat format
    for f in ("train_chat.jsonl", "val_chat.jsonl"):
        for n, ex in enumerate(data[f], 1):
            roles = [m["role"] for m in ex["messages"]]
            if roles != ["system", "user", "assistant"] or not all(m["content"].strip() for m in ex["messages"]):
                errors.append(f"{f}:{n} bad message roles/content")
    print(json.dumps({"counts": counts, "fidelity_checks": nchk, "errors": len(errors)}, indent=1))
    for e in errors[:50]:
        print("ERROR", e)
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
