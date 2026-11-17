# Director's-manual & storyboard training dataset (Kuku TV / Kronicle)

A training package for a model that writes **director's manuals** (sections ①–⑦) and **Kronicle storyboard tables** for Hindi micro-dramas, and critiques them. It follows the same approach as `/workspace/continuity_dataset/`: structured JSONL records, distilled rules with evidence, templates, a chat converter and a validator.

**Nothing was invented.** Every manual section, storyboard cell, review row and script in this package is copied verbatim from a source file (`validate.py` checks 20,500+ fields against the raw files byte for byte). Anything the builder computed (parsed lists, buckets, links between scenes and shots, splits, titles, rule summaries) is marked: the field name ends in `_derived`, the value sits under `parsed_derived`, or the rule has `rule_text_is_derived: true`. Unknown values are `null`.

## Files

| File | What it is | Records |
|---|---|---|
| `schema.json` | JSON Schema (`$defs`: episode, shot, review, pair, rule, chat_example) | — |
| `episodes.jsonl` | One record per episode (or episode version): show, episode, `episode_base` + `version` (Durvasa EP4 V1/V2), Kronicle id, title, manual parsed into sections ①–⑧ (verbatim text, labelled fields, every tab table), beat table / track table / derivative table as arrays, ④ split into scene blocks (with shot ranges where stated), appended blocks, raw manual, matched scripts, stats (shot count, total duration, shot-size & camera-move distributions raw + bucketed, speakers, scene runs, review severities), scene↔shot links | 29 |
| `shots.jsonl` | Every storyboard row: all columns verbatim under canonical names, plus parsed duration / start / end, asset name & ID lists, UUIDs, dialogue segments, orientation list, size/move buckets, prev/next shot ids | 1,173 |
| `reviews.jsonl` | Kronicle review/critique rows (severity, item, issue, suggested fix, referenced shots) + Durvasa 2 EP12 prompt-QC notes | 91 |
| `pairs/script_to_manual.jsonl` | Script → full manual (11) and script → each manual section (79) | 90 |
| `pairs/manual_to_storyboard.jsonl` | Manual context (② style, beat table, linked ④ scene intent or full ④, ⑥ continuity, previous shot) → ≤8 storyboard rows, chunked by storyboard scene runs | 198 |
| `pairs/section_to_section.jsonl` | ①→②, ①+②→③, ①+③→④, ④→⑤, ③+④→⑥, ④+⑥→⑦ | 144 |
| `pairs/scene_intent_to_shots.jsonl` | One ④ scene block → its shots (≤8 per chunk) | 108 |
| `pairs/row_to_critique.jsonl` | Referenced storyboard rows (or episode stats when no shot is named) + audit focus → severity / issue / fix | 74 |
| `pairs/beat_to_shot_plan.jsonl` | One ③ beat-table row + camera grammar → shot plan (≤10 per chunk) | 42 |
| `pairs/script_to_storyboard.jsonl` | Durvasa 2 only (no manuals): script → ≤8 storyboard rows | 16 |
| `pairs/storyboard_revision.jsonl` | Kronicle Durvasa EP4: V1 rows + V2 manual context (②, ④, ⑥) → V2 rows, aligned by shot number in chunks of 8 (both versions have 24 shots). V1/V2 are two saved versions, not an edit log | 3 |
| `rules.jsonl` / `rules.md` | 45 rules: 24 manual-craft, 11 from Kronicle review rows, 3 from table patterns, 7 production rules (Pratik/Ninni). Each has verbatim evidence quotes and cited episodes; evidence lists one quote per show first, so Durvasa quotes appear alongside UW | 45 |
| `templates/` | `manual_template.md` (①–⑧ skeleton with guidance + rule ids), `storyboard_template.md/.tsv`, `review_rows_template.tsv`, blank episode/shot JSON records | 6 files |
| `train_chat.jsonl` / `val_chat.jsonl` | Chat format `{"messages":[system,user,assistant],"meta":{...}}` | 633 / 85 |
| `convert_to_chat.py` | Rebuilds the chat files (`--max-chars N`, `--drop-meta`) | — |
| `validate.py` | Schema + unique ids + verbatim fidelity + split leakage + chat format; exits 1 on any error | — |
| `stats.md` | Per-episode table and distributions | — |
| `raw/` | The verbatim Kronicle extractions (`uw_<Ep>_*.txt` ×48, `durvasa_<Ep>_*.txt` ×8) | 56 files |
| `tools/` | `parse_lib.py`, `build.py`, `build_rules.py`, `make_stats.py`; `build_all.sh` reruns everything | — |
| `build_report.json` | Skipped episodes, script↔episode match scores, unmatched scripts | — |
| `extraction_log.md` | Where each raw file came from (Kronicle episode ids, agent ids) | — |

Split: whole episodes are held out for validation (UW **Ep3, Ep9, ioc4**, Durvasa 2 **EP12**, Kronicle Durvasa **EP3**), so no episode is in both files. Both Durvasa EP4 versions are in train (`validate.py` checks the split by `episode_base`). Rules are train-only.

## Sources

1. **Ultimate Warrior (Kronicle project e3f21c53-5527-4cd0-93e4-6abdfffbf370)**, saved verbatim from the Director's Manual and Storyboard Table tabs: Ep1–Ep12, Ep14.2, Ep15, Ep16, ioc1–ioc5, IOC SCRIPT 1 V1 (21 episodes, 941 shots).
2. **Scripts paired by matching dialogue** (3-gram overlap between the script and the storyboard's Dialogue column, threshold 0.30; scores in `build_report.json`):
   - Ep1–Ep5 → `/workspace/uw2/scripts/EP1–5.txt` (overlap 0.78–0.84). Older versions in `/workspace/uw/scripts/` and `/workspace/uw_ep5/script.txt` also match and are listed in `scripts_matched_derived`.
   - ioc1, ioc3, ioc4, ioc5 → sections 1, 3, 4, 5 of `/workspace/uw_ioc/ioc_doc.txt`.
   - ioc2 → `uw_ioc/IOC2_script.txt`; IOC SCRIPT 1 V1 → `uw_ioc/IOC1_script.txt`.
   - No script on the box for Ep6–Ep16.
3. **Maharishi Durvasa (Kronicle project 02a204b6-b20d-48e7-aed4-3cbd2abb0edf)**, transcribed verbatim by computerUse agents and saved as `raw/durvasa_*`: EP2 "The Frozen Ascent" (manual + 22 shots), EP3 (manual + 17 shots), EP4 V2 (manual + 24 shots), EP4 V1 (24 different shots, no manual). Kronicle has no review rows for these. EP1 is empty in Kronicle. No scripts for these episodes are on the box, so they have no script→manual pairs.
4. **Maharishi Durvasa 2 (local files, a different project)**: storyboards `kronicle/storyboard_EP11.md`, `storyboard_EP12.md`, `storyboard_EP14.md`, `ep13_1/storyboard.md`; scripts `kronicle/script_EP12.md`, `script_EP14.md`, `ep13_1/script.md`; prompt QC `kronicle/qc_EP12.md`. There are no director's manuals for these, so they only feed shots, script→storyboard pairs and reviews.
5. **Production rules**: `uw_continuity/UW_PROMPT_STYLE_GUIDE.md`, `UW_CONTINUITY_SHEET.md`, `uw_ep9/MASTER_LOCKS.md`, `uw_ep10/MASTER_LOCKS_E10.md`, `raw/uw_ioc2_manual.txt` (§8 Ninni's director rules), `uw_ioc/IOC2_video_prompt.txt`, plus Pratik's standing rules.

## Caveats and gaps

- **Kronicle Durvasa headings vary** ("Director Creative Plan: …", "Director Creative & Production Plan", "Director Creation Plan · Episode 04"). Sections are filed by heading title when the circled number disagrees. EP4 V2 numbers its sound section "③ Sound Direction"; it is filed as ⑤ (`manual.heading_anomalies_derived`), and the heading text is kept verbatim. Durvasa EP3's ④ uses "Scene 1-1/1-2/1-3" labels (`scene_label`) that don't map onto its storyboard scene runs, so EP3 has no scene↔shot link. EP3 and EP4 manuals name no episode title.
- **Durvasa EP4 V1 vs V2:** the two storyboards have different rows and different totals (122 s vs. 90 s). Both are kept as separate episode records (`durk_EP4V1`, `durk_EP4V2`) that share `episode_base: "EP4"`.
- **Blank in Kronicle, skipped:** UW **Ep14** and **IOC SCRIPT 1 V2** (files contain only `EMPTY`). Ep13 and Ep17 have no manual or storyboard in Kronicle and were never extracted.
- **UW Ep1 manual:** the 12.7 KB file on disk was used. The fuller version that may be in the Ep1 agent report (sand-subagent-d8e094c0…) could not be read, so completeness can't be confirmed. Ep1's REVIEW ROWS block is empty on disk.
- **UW Ep2:** the saved manual ends with the Kronicle chat (producer audit, asset analysis, derivative-card instructions). It is kept verbatim in `appended_blocks.kronicle_chat_block` and left out of `manual_text_clean` and the training pairs. Two audit rows sat above `REVIEW ROWS` in the storyboard file and are parsed as reviews (`review_block: "pre_review_rows"`).
- **UW Ep4 / Ep5 manuals** start with a version preamble ("v5, 24 Oct 2026 … built from the approved storyboard …") and end with a "Video Workspace: per Nin …" note. These are kept in `manual.preamble` and `appended_blocks.appended_production_note`.
- **ioc2's manual** uses numbered headings (1.–8.) instead of ①–⑧ and has no tab tables, so it has no beat table.
- **Mixed column sets.** Ep1–Ep4 use display names (Shot | Frame Description | …). Ep5–Ep11, Ep15 and the iocs use API names and a `title` column. Ep12, Ep14.2 and Ep16 use API names without `title`. Everything is mapped to one canonical set, and the original header is kept in `storyboard_header_raw`.
- **Durvasa 2 EP13.1 is partial:** its source file kept only Shot, Scene, Duration, a merged size/camera cell, Assets, Description and Dialogue.
- **Scene↔shot links** (`scene_links_derived`) come from explicit "(Shots a–b)" headings (Ep1–Ep4, ioc1, ioc3), from matching the number of scenes to storyboard scene runs (Ep7, Ep8, Ep10, Ep11, Ep12, Ep14.2, Ep15, ioc4), or from timecodes (ioc5). Ep5, Ep6, Ep9, Ep16, ioc2 and IOC SCRIPT 1 V1 have no reliable link, so their manual→storyboard pairs carry the full ④ section instead.
- **Beat→shot ranges** exist only where the beat table has a Shots column that adds up to the storyboard: Ep1–Ep4 and Ep16 (counts or explicit ranges).
- **Stated vs. actual totals differ in places** (e.g. the Ep16 manual says 344 s while the rows sum to 348 s). Both values are kept in `stats_vs_manual_derived`. Nothing was "fixed".
- **Dialogue script:** Kronicle storyboards store dialogue in Roman Hindi (no Devanagari in any row). The UW video-prompt rules lock dialogue to Devanagari, while Durvasa 2's prompt QC required Roman. Visible on-screen text is Devanagari only either way. See `prod_devanagari_visible_text`.
- **Some Sound cells name chants** (e.g. uw_Ep1_s002, uw_Ep5_s035, uw_Ep11_s003), which sits awkwardly with the no-music rule. This is noted on `sb_sound_layered_plus`.
- Kronicle review items cite codes R1–R6. Their full definitions are not in any source file, so they are left as written.
- Long examples: the largest chat example is about 48 k characters (Ep3 script→manual). Use `--max-chars` if your trainer has a context limit.

## Rebuild

```bash
cd /workspace/manual_dataset && ./build_all.sh      # build → rules → chat → stats → validate
```

## Adding an episode or show

Save the Kronicle manual and storyboard verbatim into `raw/` (`<show>_<Ep>_manual.txt`; `durvasa_*` files are picked up automatically, with a `V1`/`V2` suffix for versions, `<show>_<Ep>_storyboard.txt`; storyboard = header line + ` | `-separated rows, then `REVIEW ROWS` and `# | Severity | …` blocks). Add the show to `tools/build.py` (UW is the model), run `./build_all.sh`, and check that `validate.py` reports 0 errors.
