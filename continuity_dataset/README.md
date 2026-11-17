# Continuity training dataset

A reusable package for training (or prompting) a model that writes continuity-locked video prompts and QCs generations. It was built from Ultimate Warrior (UW) production files, plus a clearly labeled Raktbeej template so another show can be added the same way.

Nothing here was invented. If a fact was not in the source files, the field is `null`. Facts taken only from a prompt, not a checked render, are marked `from_prompt_unverified`.

## Files

| File | What it is |
|---|---|
| `schema.json` | JSON Schema for every record |
| `uw_continuity.jsonl` | Real UW records (continuity states, prompt pairs, QC examples) |
| `rules.jsonl` | Show-agnostic continuity rules with good/bad examples |
| `template_new_show.jsonl` | Example-labeled Raktbeej / blank templates for adding a new show |
| `convert_to_chat.py` | Converts those files into chat fine-tuning JSONL |
| `train_chat.jsonl` | Output of the converter (templates skipped) |
| `README.md` | This file |

Each JSONL line is one record. The four `record_type` values are:

- **continuity_state** — a locked state at a moment in the show (usually the end of a track): characters (position, facing, costume, props, injuries, state), location + view, lighting, time of day, damage, and the handoff paragraph.
- **prompt_pair** — input: previous track end state + script beat + assets + locks; output: the continuity locks / shot outline that went into the next prompt. Full multi-thousand-word prompt bodies are not copied here; `source_paths` points at the original files.
- **qc_example** — prompt intent + observed video + passes + errors (each with a category) + verdict + fix. The fix is always meant to go *inside* the shot text, not as a note at the end.
- **rule** — one continuity rule, a category, and a good/bad example.

## How to add data

1. Copy a record of the right type. For a new show, start from `template_new_show.jsonl` and set `is_example_template` to `false`.
2. Fill only facts you can point at in `source_paths`. Use `null` when unknown. Set `verification` honestly (`verified_from_render`, `from_prompt_unverified`, `observed_partial`, `planned_not_selected`, `rejected`, `prompt_preflight`).
3. Put show-specific locks in that show's JSONL (or a new `SHOW_continuity.jsonl`). Keep generic rules in `rules.jsonl`.
4. Validate against `schema.json`.
5. Rebuild the chat file:

```bash
python3 convert_to_chat.py --in-dir /workspace/continuity_dataset --out /workspace/continuity_dataset/train_chat.jsonl
```

`is_example_template: true` records are skipped by the converter (they are for authors, not for training). Use `--drop-meta` if your trainer wants only `{"messages":[...]}` with no `meta` key.

## How to use for fine-tuning

`train_chat.jsonl` is one instruction example per record, in the usual chat format:

```json
{"messages":[{"role":"system","content":"..."},{"role":"user","content":"..."},{"role":"assistant","content":"..."}],"meta":{"id":"...","record_type":"..."}}
```

The system prompt restates the standing continuity rules. The assistant target is structured JSON:

- continuity_state → the state object
- prompt_pair → the output locks / shot outline
- qc_example → verdict, passes, errors, fix
- rule → the rule plus examples

Fine-tune a small instruction model on this file, or retrieve nearest records (by show, location, or error category) and put them in the prompt when writing the next track or QCing a take.

After a new approved take, add a `continuity_state` from the last frame, then a `qc_example` for that gen, then a `prompt_pair` for the next track. That is the loop the model is meant to learn.

## Standing rules the dataset teaches

These are also listed, with examples, in `rules.jsonl`:

- Dialogue stays verbatim.
- Do not change shot types, order, or framing unless asked.
- Visible on-screen text follows the show's script lock (for Hindi shows: Devanagari only). Dialogue script (Devanagari vs Roman) follows the current episode lock, still verbatim.
- Position lock: every character, every shot; carry the previous end state forward.
- Location must match the named reference asset as the background plate; do not mix conflicting refs.
- Characters keep their walking direction (no unexplained U-turns when the camera reverses).
- Damaged locations, costumes and props stay damaged until an approved beat changes them.
- No eye glow (unless the director explicitly approves an exception).
- Put changes inside the shot text, not in override notes at the end.
- QC every generation. Update continuity from what was actually rendered.

## Gaps (sources that exist but were not fully mined)

- Hundreds of episode prompt files (`uw_ep2`–`uw_ep12`, `ep13_1`) were not turned into one `prompt_pair` each. Only handoffs where a previous end state and a locked next prompt were clearly documented were extracted.
- Many episodes have blocking notes, edit specs, or frames without a written QC report; those were not turned into `qc_example` records.
- Ep1 clip 6 v4 was still generating and was not QC'd (`c6_v4_qc.md`) — no record.
- IOC1 track 1 v3 render QC (crying, glows, timing) was discussed in production chat but is not in a saved QC file, so it is not in this dataset.
- `kronicle/continuity_EP11.md`, `continuity_EP12.md`, and `qc_EP12.md` belong to a different show (Maharishi Durvasa / Indra's Raj Sabha), not UW. They were not mixed into `uw_continuity.jsonl`. They can be added later as a third show using the same schema.
- Raktbeej Video Workspace prompts, assets Ep2–16, and renders were not saved (`PREP_STATUS.md`), so Raktbeej stays template-only.
- Two T09N blocking notes disagree in places (`E10_LOCATION_CONTINUITY_MASTER.md` vs `E10_POSITIONS_T09N_T10L.md`). The approved last-frame master is the one used; the conflict is noted on that record.
- Agnivesh's costume has an open canon question (prompt lock vs approved T09 render).

## Sources used

- `/workspace/uw_continuity/UW_CONTINUITY_SHEET.md`
- `/workspace/uw_continuity/UW_PROMPT_STYLE_GUIDE.md`
- `/workspace/uw_ioc/` (`ioc_doc.txt`, `IOC1_breakdown.md`, `IOC1_track1_edits.md`, `IOC1_track1_tail_new.txt`, `IOC2_manual.txt`, `IOC2_video_prompt.txt`, `brief_head.txt`)
- `/workspace/uw_ep9/E8_end_continuity_note.md`, `MASTER_LOCKS.md`, `BROKEN_STATE_LEDGER.md`, `POSITION_ORIENTATION_LEDGER.md`
- `/workspace/uw_ep10/E10_LOCATION_CONTINUITY_MASTER.md`, `MASTER_LOCKS_E10.md`, `E10_POSITION_LEDGER.md`, `E10_CHARACTER_POSITIONS.md`, `E10_POSITIONS_AFTER_T07.md`, `E10_POSITIONS_T09N_T10L.md`, `E10_T1_T2_positions_observed.md`
- `/workspace/uw_ep11/E11_QC_PLAN.md`, `qc_runs/2026-11-05_t01d_t02f_t08l_notes.txt`
- `/workspace/uw_ep8/qc/` (`E8_T01_v7_qc.md`, `E8_T03_v4_qc.md`)
- `/workspace/uw_ep4/qc/` (T08–T15)
- `/workspace/uw2/qc/` (Ep1 clip QC)
- `/workspace/uw2/video_prompts/ep1/handoff_track*.txt` (consulted; track-to-track pairs were only written where an end-state note also existed)
- `/workspace/new_show/RAKTBEEJ_BIBLE_short.md`, `RAKTBEEJ_BIBLE.md`, `PREP_STATUS.md`
