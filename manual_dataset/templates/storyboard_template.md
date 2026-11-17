# Storyboard Table — blank template (with guidance)

Columns (Kronicle export names in brackets). One row per shot. Fill every column on every row *(sb_field_completeness)*.

| Column | Guidance (derived from real rows + Kronicle review rows) |
|---|---|
| Shot [id] | Integer, consecutive from 1. |
| Title [title] | Short shot title (present in newer exports; Kronicle flags its absence in Ep5). |
| Frame Description [description] | What the frame shows, foreground → midground → background. No lighting/grade words *(sb_no_lighting_in_fields)*. |
| Scene [scene] | Location/scene name exactly as the scene asset or script heading. |
| Associated Asset Names [associateAssetsNames] | `[Name, Name, …]` — every visible or speaking character, the location (or its angle derivative) and key props *(sb_visible_characters_associated)*. |
| Duration [duration] | Seconds. Long enough for the full line plus headroom *(sb_dialogue_duration_headroom)*; rows must sum to the episode target *(sb_total_duration_matches_target)*. |
| Shot Size [shotSize] | e.g. Extreme Wide, Wide, Medium Wide, Medium, Medium Close-up, Close-up, Extreme Close-up, Insert, OTS. Avoid three identical sizes in a row *(sb_shot_size_variety)*. |
| Camera Movement [cameraMove] | One move with its purpose; match the manual's ② exclusions. |
| Character Action [action] | Physical sequence inside the shot; carry continuity ("Continuity: …" / "(Continuing previous shot …)") *(sb_action_carries_continuity)*. |
| Orientation [orientation] | `Character - facing, screen direction, eyeline target; …` for every character *(sb_orientation_spatial_columns, sb_axis_eyeline_continuity)*. |
| Spatial Relationship [spatialRelation] | `Character (safe-centre/left/right, Fore/Mid/Back, third); …` — positions lock shot to shot *(prod_positions_lock_every_shot)*. |
| Emotion [emotion] | Two- or three-word emotional label. |
| Dialogue [lines] | `Speaker: line` copied byte-for-byte from the script, or `None` *(prod_dialogue_byte_for_byte, sb_dialogue_speaker_prefix)*. |
| Sound Effects [sound] | Concrete layered effects joined with `+`; no music *(sb_sound_layered_plus, prod_no_music)*. |
| Associated Asset IDs [associateAssetsIds] | UUIDs of the bound assets, choosing the derivative whose state matches this shot *(sb_derivative_state_matches_shot)*. |

## Review rows (critique block under the table)

`# | Severity | Review item | Issue | Suggested fix` — severity uses 🔴 Critical / 🟡 Moderate / ⚪ Minor. Common review items seen: Field completeness (R4), Visible characters fully associated (R1), Script coverage (R2), Orientation & eyeline (R3), Lighting description prohibition / Sound perceivable (R5), Parent/child asset selection (R6), Duration sound, Splitting granularity, Shot-size variety, Total duration calibration. (R-codes are as written in Kronicle's review rows; their full definitions are not in the sources.)
