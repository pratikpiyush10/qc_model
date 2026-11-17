# Director's-manual & storyboard craft rules

Distilled from the real manuals, storyboards and Kronicle review rows in this dataset. Rule text is a derived summary; every evidence quote below is verbatim from the cited file. A distilled rule was kept only if at least two episodes evidence it (exceptions are marked). Full evidence is in `rules.jsonl`.


## Director's manual rules

### `dm_structure_seven_sections` (manual_structure)
Write the director's manual as seven sections in fixed order: ① theme & emotional arc, ② visual style & camera, ③ narrative structure with a beat/pacing table, ④ scene-by-scene emotion & visual intent, ⑤ sound, ⑥ transitions & continuity anchors, ⑦ derivative asset pre-plan. Optional ⑧ holds execution steps or look notes.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc2, UW ioc3, UW ioc4, UW ioc5

- EP2 · section_order: "① Theme & Narrative Core | ② Visual Style & Spatial Staging | ③ Narrative Structure & Pacing | ④ Scene-by-Scene Emotional & Visual Intent | ⑤ Sound Direction | ⑥ Transitions & Visual Continuity | ⑦ Derivative Assets Pre-planning List"
- Ep1 · section_order: "① Theme, Premise & Narrative Core | ② Visual Style & Framing Tone (16:9 Landscape with 9:16 Safe Area) | ③ Narrative Structure & Rhythm Planning (38 Shots / 286 Seconds) | ④ Scene-by-Scene Emotion & Visual Intent | ⑤ Diegetic Sound Direction (No Music / Pure SFX) | ⑥ Transitions & Visual Continuity Anchors | ⑦ Derivative Asset Pre-Planning List"
- EP3 · section_order: "① Theme & Narrative Core | ② Visual Style & Framing Tone | ③ Narrative Structure & Pacing | ④ Scene-by-Scene Emotion & Visual Intent | ⑤ Sound Direction | ⑥ Transitions & Visual Continuity | ⑦ Derived Asset Pre-planning List"

Note: Ep14.2, Ep16, Ep8, ioc1 and ioc2 add an eighth section (execution plan, photoreal look, or Ninni's director rules).

### `dm_core_theme_one_line` (theme)
Open ① with a single-sentence Core Theme that states the moral thesis of the episode (what is earned vs. what is inherited/imposed).

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s1_theme_emotional_arc: "Core Theme: Unyielding inner stillness (Maun Vrat) triumphs over tempestuous wrath, awakening primordial cosmic retribution."
- Ep1 · s1_theme_emotional_arc: "Core Theme: Sovereign legitimacy is born from enduring sacrificial humiliation, not inherited thrones or martial arrogance."
- EP3 · s1_theme_emotional_arc: "Core Theme: The ultimate battle against inner wrath—true mastery over fury lies not in outward destruction, but in unyielding physical restraint under supreme provocation."

### `dm_emotional_arc_tiers` (theme)
After the theme, give the emotional arc as ordered tiers or a through-line, each tied to a visible physical behaviour (posture, breath, hands), not abstract feelings.

Seen in: Durvasa EP2, Durvasa EP3, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s1_theme_emotional_arc: "Emotional Arc:"
- Ep1 · s1_theme_emotional_arc: "Tier 1 (Martial Vaunt vs. Ascetic Quiet): Ranvijay projects broad, chest-forward pomp on horseback while Agnivesh maintains stillness, measured finger movements, and steady breathing over ancient manuscripts."
- EP3 · s1_theme_emotional_arc: "Emotional Arc:"

### `dm_audience_takeaway` (theme)
State the intended audience takeaway / emotional strategy, usually ending on a hook or cliffhanger that pulls into the next episode.

Seen in: Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep12, UW Ep14.2, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep6, UW ioc2, UW ioc3, UW ioc4

- EP3 · s1_theme_emotional_arc: "Audience Exit Feeling: A breathless, high-tension cliffhanger that leaves the audience viscerally suspended on the razor-edge of Durvasa's silence about to shatter."
- Ep1 · s1_theme_emotional_arc: "Audience Takeaway & Emotional Strategy: Cultivate acute cathartic anticipation. By driving filial rejection and brotherly arrogance to an unbearable peak, the audience is primed to crave ruthless karmic retribution, sealed by a supernatural physical cliffhanger."
- EP4V2 · s1_theme_emotional_arc: "Audience Takeaway (Departure Feeling) — Cathartic awe at the supreme composure of the sage, followed by chilling anticipation as he willingly crosses into the dark cavern of inner examination."

### `dm_format_declared` (visual_style)
Declare the frame format in ② (native 9:16 vertical, or 16:9 with all key action inside a central 9:16 safe area) and compose for it.

Seen in: Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc2, UW ioc3, UW ioc4, UW ioc5

- EP4V2 · manual: "② Visual Style & Camera Framing (9:16 Vertical · Peter Jackson Cinematography)"
- Ep1 · manual: "② Visual Style & Framing Tone (16:9 Landscape with 9:16 Safe Area)"
- Ep2 · manual: "② Visual Style & Framing Tone (Native 9:16 Vertical)"

### `dm_three_layer_depth` (visual_style)
Specify three-layer spatial depth for the show: what lives in the foreground, midground (the acting subject) and background (architecture/crowds).

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s2_visual_style_camera: "Foreground: Swirling ice crystals, splitting crevasses, and the fluttering saffron pennant (Kesariya Dhwaja) tied to the staff providing immediate spatial depth."
- Ep1 · s2_visual_style_camera: "Foreground: Ringing brass bridle bells, sand drifts, stone balustrades, or the ornate jade sword hilt placed close to the lens."
- EP3 · s2_visual_style_camera: "Foreground: Shivering orange cloth fragments, cracking ice shards, demonic claws encroaching the frame edge to guide visual focus."

### `dm_composition_modes_tied_to_beats` (visual_style)
Name each compositional mode (symmetry, rule of thirds with negative space, diagonal, frame-within-frame) and attach it to the specific story moment it serves.

Seen in: Durvasa EP2, Durvasa EP3, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s2_visual_style_camera: "Symmetrical Center-Framing: Enforce rigid centered stability exclusively for Durvasa's rooted Padmasana post-avalanche and Rudra's high-peak meditation to establish inviolable divine order."
- Ep2 · s2_visual_style_camera: "Symmetry vs. Diagonal Conflict:"
- EP3 · s2_visual_style_camera: "Symmetrical Rupture: Initial balanced frames of meditation and mountain ridges violently fractured by diagonal fissures and asymmetrical winged beast postures."

### `dm_camera_move_purpose` (camera)
Give every camera move a dramatic job (e.g. push-in on a dialogue turn or impact, pull-back to reveal isolation, tracking to show inevitability) rather than listing moves generically.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc2, UW ioc3, UW ioc4, UW ioc5

- EP2 · s2_visual_style_camera: "Slow, relentless push-in toward facial micro-details (frost-sealed lips, widening demonic pupils, opening of the third eye)."
- Ep1 · s2_visual_style_camera: "Dolly Push / Pull: Smooth, slow linear dolly push-ins to intensify psychological weight on crucial dialogue turns; smooth dolly pull-backs to reveal isolation against oppressive court grandeur."
- EP3 · s2_visual_style_camera: "Creeping Slow Push-In: Tightening focus from medium shot to extreme close-up during demonic whisperings to isolate psychological tension."

### `dm_camera_exclusions_explicit` (camera)
State explicitly which camera behaviours are banned or reserved for single beats (handheld shake, whip-pans, crash zooms).

Seen in: Durvasa EP2, UW Ep1, UW Ep10, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc2, UW ioc3, UW ioc4

- EP2 · s2_visual_style_camera: "Rapid tilt-downs and whip-pans tracking descending glacial boulders and the collapsing snow cliff."
- Ep1 · s2_visual_style_camera: "Strict Exclusions: Zero handheld shake, zero whip-pans, zero crash zooms, and zero erratic camera jitter. Every motion begins and decelerates with silky, cinematic precision."
- Ep2 · s2_visual_style_camera: "Agnivesh's shove (12, handheld-energy push)."

### `dm_beat_table` (narrative_structure)
In ③, include a beat/section table with one row per beat: name, scene, core event, shots or shot range, duration, emotional intensity, and pacing/camera rhythm; close with a Total row when shot counts are given.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s3 beat table header: "Seg # | Name | Scene | Core Event | Emotional Intensity | Rhythm"
- Ep1 · s3 beat table header: "Beat # | Beat Name | Scene / Setting | Core Narrative Event | Shots | Duration | Emotional Density | Camera Rhythm"
- EP3 · s3 beat table header: "Beat No. | Beat Name | Scenes | Core Dramatic Event | Emotional Intensity | Pacing & Shot Rhythm"

### `dm_intensity_curve` (narrative_structure)
Give each beat an explicit emotional intensity (percent, x/10, or a labelled density) so the escalation curve is visible, and describe the curve in one line.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s3_narrative_structure_beats: "Seg #	Name	Scene	Core Event	Emotional Intensity	Rhythm"
- Ep1 · s3_narrative_structure_beats: "Beat #	Beat Name	Scene / Setting	Core Narrative Event	Shots	Duration	Emotional Density	Camera Rhythm"
- EP3 · s3_narrative_structure_beats: "Beat No.	Beat Name	Scenes	Core Dramatic Event	Emotional Intensity	Pacing & Shot Rhythm"

### `dm_turning_points_visual` (narrative_structure)
List key turning points as concrete visual executions (what the hand, prop or camera does), not as plot summaries.

Seen in: Durvasa EP2, Durvasa EP3, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s3_narrative_structure_beats: "Turning Point 1: Durvasa's boots halt dead in the snow as the massive avalanche wall looms directly overhead."
- Ep1 · s3_narrative_structure_beats: "Key Visual Turning Points:"
- EP3 · s3_narrative_structure_beats: "Turning Point 1 (Physical Anchor): Staff violently lodges into the fissure while the flag tears away, transitioning kinetic freefall into static suspension."

### `dm_scene_blocks_with_ranges` (scene_intent)
In ④, open each scene block with a heading naming the scene, and where possible its shot range and duration, so the storyboard can be checked against it.

Seen in: UW Ep1, UW Ep2, UW Ep3, UW Ep4, UW ioc1, UW ioc3, UW ioc5

- Ep1 · s4_scene_intent: "Scene 1: Royal Tournament Pavilion — The Arrogant Parade (Shots 1–6 / 45s)"
- Ep2 · s4_scene_intent: "Scene 1: EXT. RAJMAHAL - DAY TO NIGHT (TIME-LAPSE) (Shot 1 / 4s)"
- Ep3 · s4_scene_intent: "Scene 1: INT. ARCHIVE WARD CHAMBER - NIGHT (CONTINUOUS) (Shots 1–10 / 52s)"

### `dm_scene_emotion_acting` (scene_intent)
Each scene block states the emotional objective and acting notes per character, plus the camera/visual intent for that scene.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s4_scene_intent: "Emotional Target: Relentless ascetic endurance confronting feral demonic agitation, transitioning into overwhelming cosmic shock."
- Ep1 · s4_scene_intent: "Emotional Objective: Unchecked martial hubris; squared shoulders, lifted chin, smirking eye-locks."
- EP3 · s4_scene_intent: "Emotional Goal: Sudden visceral vertigo and desperate physical survival."

### `dm_spatial_distance_design` (scene_intent)
For each scene, design spatial staging and distance: how far apart characters are, who occupies foreground vs. deep background, and how that distance changes with the power or emotional shift.

Seen in: Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP3 · manual: "Spatial Staging & Distance Design: Extreme separation—Durvasa suspended in deep negative space below, the colossal two-headed avian beast dominating the upper ridge."
- Ep1 · manual: "Distance Design: Wide arena vista gliding smoothly into medium tracking of the stallion and close-up smirks."
- EP4V2 · manual: "Spatial Staging: Durvasa stands centered on the narrow snow ledge; the breached ice wall and charging Rakshak vanguard flank camera-left/rear; Rudra, Nandi, and Vasuki loom stationary across camera-right against the cloud precipice."

### `dm_scene_atmosphere_line` (scene_intent)
Give each scene a one-line atmospheric direction (the felt mood of the space) alongside its emotional goal.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep5

- EP2 · manual: "Atmospheric Direction: Oppressive, desolate, violent, transcendent."
- Ep1 · manual: "Atmospheric Direction: Oppressive courtly pomp, intoxicating hubris, celebratory adulation."
- EP3 · manual: "Atmospheric Direction: Catastrophic, oppressive, towering mythological dread."

### `dm_sound_concrete_diegetic` (sound)
Write sound as concrete physical (diegetic) events grouped as ambience and action SFX: what material makes which sound.

Seen in: Durvasa EP4V2, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc2, UW ioc3, UW ioc4, UW ioc5

- EP4V2 · s5_sound: "Ambient Sound Layers:"
- Ep2 · s5_sound: "Concrete Environmental & Foley SFX:"
- Ep3 · s5_sound: "Concrete Environmental & Foley SFX:"

### `dm_sound_designed_silence` (sound)
Plan silence deliberately: name the exact moments where ambience drops out and what single sound is left.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s5_sound: "Sudden drop to absolute ambient silence the moment Durvasa opens his eyes amidst the settling snow, instantly cutting off Krodha's laughter."
- Ep1 · s5_sound: "Key Silence Moments:"
- EP3 · s5_sound: "Dead silence on Durvasa's final breath as his lips part slightly before the abrupt cut to black."

### `dm_transitions_motivated` (transitions)
In ⑥, specify each scene-to-scene transition as a motivated cut (hard cut on an impact or line, match cut on a shape/flash) and keep dissolves rare.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s6_transitions_continuity: "Inter-Shot Transitions: Rapid hard cuts during the avalanche cascade; smooth cutaways to Rudra's distant silhouette to maintain mountain geography."
- Ep1 · s6_transitions_continuity: "Scene 1 to Scene 2: Sound bridge: Ranvijay's booming laugh dissolves into the dry rustle of turning parchment inside the reading room."
- EP3 · s6_transitions_continuity: "From 1-1 to 1-2: Match cut from the downward spiral of dark mist inside the crevasse into the close formation of the demonic entity."

### `dm_continuity_anchors_per_character` (continuity)
List continuity anchors per character and key prop: costume, wound, prop state and hand, so every later shot can be checked against them.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s6_transitions_continuity: "Visual Continuity Anchors:"
- Ep1 · s6_transitions_continuity: "Wardrobe State: Agnivesh's royal-blue silk angrakha sleeves remain fastened at the wrists until the cuff scorches and draws back at the cliffhanger."
- EP3 · s6_transitions_continuity: "Visual Continuity Anchors:"

### `dm_derivative_table` (derivative_assets)
In ⑦, list derivative assets as a table: parent Asset Name | Derivative State | Reason / narrative appearance (with the scenes or shots that need it). Parent names must match existing assets exactly.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s7 table header: "Asset Name | Derivative State | Reason & Scene Occurrence"
- Ep1 · s7 table header: "Asset Name | Derivative State | Reason / Appearing Segment"
- EP3 · s7 table header: "Asset Name | Derived State | Reason / Scene Occurrence"

### `dm_derivative_reverse_views` (derivative_assets)
Plan reverse/angle views of locations as derivatives whenever the storyboard needs the camera looking the other way.

Seen in: Durvasa EP2, Durvasa EP3, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3, UW ioc4, UW ioc5

- EP2 · s7_derivative_assets: "The Frozen Ascent	Multi-View Reference	Multi-view structural layout reference for shot staging and derivative alignment."
- Ep1 · s7_derivative_assets: "Royal Tournament Pavilion	Reverse Arena View	Facing South Grand Entrance Gate from the northern throne dais; required for Agnivesh's walk-in and crowd jeering coverage (Sc 1, Sc 3, Sc 4)"
- EP3 · s7_derivative_assets: "Gandaberunda-Krodha	Multi-Angle Reference	Comprehensive anatomical and structural reference for dual-headed avian form across dynamic action shots."

### `dm_derivative_reuse_no_turnarounds` (derivative_assets)
Reuse existing derivatives instead of duplicating them, and do not plan turnaround / multi-view grid sheets; say so when no new derivative is needed.

Seen in: UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep6, UW Ep8, UW IOCSCRIPT1_V1, UW ioc1, UW ioc3

- Ep2 · s7_derivative_assets: "Reused existing (no new card):"
- Ep3 · s7_derivative_assets: "Reused existing (no new card):"
- Ep4 · s7_derivative_assets: "Reused existing cards: Agnivesh / Scorched Cuff + Throat Nick (every Agnivesh shot) and Scorched Cuff Glowing Mark (74–78); Suryagarh Citadel / Raksha-Kavach Cracked (Violet Thunder) and Temple Steps, Low Angle (Sc 1)."

### `dm_transient_effects_in_video` (derivative_assets)
Transient effects (glows flickering, torches guttering, cracks spreading) are handled in the video prompt, not as new asset cards.

Seen in: UW Ep2, UW Ep3, UW Ep4, UW Ep5

- Ep2 · s7_derivative_assets: "Handled in video, no card:"
- Ep3 · s7_derivative_assets: "Handled in video, no card:"
- Ep4 · s7_derivative_assets: "Handled in video, no card: the crack spreading; the compass spinning and the gate symbols lighting up on the map; the weapon rack; the golden fire and the ash; Kaalini's silhouette."


## Storyboard rules (from Kronicle review rows)

### `sb_field_completeness` (storyboard)
Fill every storyboard column on every row (description, scene, asset names, duration, shot size, camera move, action, orientation, spatial relation, emotion, dialogue, sound, asset IDs).

Seen in: UW Ep12, UW Ep5, UW Ep7, UW IOCSCRIPT1_V1, UW ioc2

- Ep5 · REVIEW ROWS: "🔴 Critical | Field completeness (R4) | The storyboard table omits the mandatory title column across all 83 rows, moving directly from id to description. | Add a separate title column containing a 2–4 word slug per shot (e.g., "Agnivesh at Harbor Gate", "Kaalini Enters Courtyard") / Formally approve the current table schema using id + description without a shot title."
- Ep7 · REVIEW ROWS: "🔴 Critical | Field completeness (R4) | The mandatory title column is entirely absent from the storyboard table schema across all 46 rows. | Add the title column (e.g., Courtyard Standoff, Timiraksha Descent, Sun Blade Shattered, Chained Sovereign, Brother's Shield) to fulfill the required schema (id / title / duration / scene / camera / description / action / emotion / associateAssetsIds)."
- Ep12 · REVIEW ROWS: "⚪ Minor | Field completeness | The table separates camera into granular shotSize and cameraMove columns but omits an explicit title (slugline) column specified in the R4 schema checklist. | Add a concise title column (e.g. "Fork Standoff", "Renuka Discovery", "Gargoyle Plunge") if downstream ingestion requires the explicit header field."

### `sb_visible_characters_associated` (storyboard)
Every character visible or speaking in a shot must be in that row's associated asset names and IDs; extras that look like a known asset should be linked or explicitly kept generic.

Seen in: UW Ep10, UW Ep11, UW Ep5, UW Ep7, UW IOCSCRIPT1_V1

- Ep5 · REVIEW ROWS: "🔴 Critical | Visible characters fully associated (R1) | In Shots 60, 64, 73, and 81, royal/palace guards appear visibly in frame and carry out key physical actions, matching the script's declared asset Royal Guard 2, but Royal Guard 2 (ec190bb1-b9f2-4589-8d72-f07b02c9c9c0) is omitted from associateAssetsNames and associateAssetsIds. | Add Royal Guard 2 (ec190bb1-b9f2-4589-8d72-f07b02c9c9c0) to associateAssetsNames an …[clipped]"
- Ep7 · REVIEW ROWS: "🔴 Critical | Asset match (R1) | Prop asset b815585d-1f33-4264-8772-bf54ff75ad43 (Iron Shield) exists in assets and is actively used across multiple shots (Shots 1, 8, 14, 18, 27, 45), but is described only as a generic "fallen guard's shield" and never included in associateAssetsNames or associateAssetsIds. | Add Iron Shield (b815585d-1f33-4264-8772-bf54ff75ad43) to associateAssetsNames and associateAssetsIds in Shot …[clipped]"
- Ep10 · REVIEW ROWS: "🔴 Critical | Visible Characters Association (Shot 56) | In Shot 56, the dialogue and visual description describe both Royal Guards and Praja roaring in unison (ROYAL GUARDS: "hum bhi chalenge!"), but associateAssetsIds only contains Praja (survivors) and the scene asset, omitting the Royal Guards asset. | Add Royal Guards (f24135c9-2650-45e3-a631-f47d45598afe) to associateAssetsIds and include Royal Guards in associa …[clipped]"

### `sb_derivative_state_matches_shot` (storyboard)
Bind the derivative whose state matches the shot (sheathed vs drawn weapon, wounded vs clean, reverse view for reverse-angle setups); switch bindings at the shot where the state changes.

Seen in: UW Ep10, UW Ep16, UW IOCSCRIPT1_V1

- Ep10 · REVIEW ROWS: "🟡 Moderate | Derivative Selection (Shot 2) | Shot 2 highlights Agnivesh's glowing wrist mark, but uses the standard battle-damaged body asset instead of the dedicated wrist mark derivative. | Optional: Switch to the glowing wrist mark derivative (dd435c3f... or 48fdd2e1...)."
- Ep16 · REVIEW ROWS: "🔴 Critical | Parent/child asset selection correct (R1 / R6) | All 79 shots reference the base scene asset 57d14e84-cc69-472e-ba8f-4f35cd7bff1d for Black Gorge Bridge, ignoring the pre-existing angle derivative d120688f-37a0-4dd9-ae5d-5c6a021a077b (reverse view) in shots facing the cliff ledge (e.g., Shots 23, 25, 27, 48, 61, 62, 65, 71, 78) | In all reverse-angle setups facing the cliff ledge and anchor posts, replac …[clipped]"
- IOCSCRIPT1_V1 · REVIEW ROWS: "🔴 Critical | Parent/child asset selection correct | Shot 13 explicitly depicts the torch snuffing out into smoke, but associates parent asset Wall Torch (2dad23e8-0125-4e82-82b4-374f999f0f49) instead of its existing derivative extinguished state (51347bcf-59c6-4c36-a8c2-ca4a80c3ec05). | Update Shot 13 associateAssetsIds to ["51347bcf-59c6-4c36-a8c2-ca4a80c3ec05", "48f839af-e451-499a-a2e2-90ffad328bd5"] and associateA …[clipped]"

### `sb_orientation_spatial_columns` (storyboard)
Keep Orientation (each character's facing/eyeline) and Spatial Relationship (position in frame, depth layer) in their own columns, per character, every row.

Seen in: UW Ep11, UW Ep15, UW Ep5, UW Ep9

- Ep5 · REVIEW ROWS: "🟡 Moderate | Spatial relationship & orientation completeness | In Shot 71, Kaalini is listed in associateAssetsNames but omitted from both orientation and spatialRelation; in Shot 58, Temple Priestesses are listed in associateAssetsNames and action but omitted from orientation and spatialRelation. | In Shot 71, add Kaalini(left-back) to spatialRelation and Kaalini-3/4 back facing left to orientation (or remove Kaalin …[clipped]"
- Ep9 · REVIEW ROWS: "🟡 Moderate | Separate orientation column | In Shot 17, orientation is filled with — even though the camera move explicitly frames from behind Maharaja Someshwar as chains converge on him | Update orientation to Maharaja Someshwar-back facing forward"
- Ep11 · REVIEW ROWS: "🔴 Critical | Orientation & Eyeline Match (R3) | In Shot 38, Devika's orientation is marked Devika-3/4 back facing left, pointing her gaze away from Agnivesh (center-mid, facing left) and breaking the 180° dialogue axis established in Shot 37. | Update Shot 38 Devika orientation to Devika-3/4 back facing right / Reframe as a clean profile Devika-profile facing right looking directly toward Agnivesh."

### `sb_axis_eyeline_continuity` (storyboard)
Hold screen direction and eyelines across cuts (axis, trajectory, OTS geometry); a character's travel direction does not flip without a shown reason.

Seen in: UW Ep10, UW Ep11, UW Ep7

- Ep7 · REVIEW ROWS: "🟡 Moderate | Visual continuity (Axis) | In Shot 8, Agnivesh and Ranvijay suddenly switch orientation to facing left to absorb the shockwave, while the blast source (Timiraksha and the gate side) originated from screen-right, creating an abrupt 180° axis flip without an establishing transition. | Change orientation in Shot 8 to profile facing right, braced / Explicitly specify a 180° reverse-angle camera setup in came …[clipped]"
- Ep10 · REVIEW ROWS: "🟡 Moderate | Dialogue Pacing (Shots 13 & 34) | Shot 13 (25 words in 8s) and Shot 34 (21 words in 7s) have tight delivery windows. | Optional: Extend Shot 13 to 9s/10s and Shot 34 to 8s."
- Ep11 · REVIEW ROWS: "🔴 Critical | Orientation & Eyeline Match (R3) | In Shot 38, Devika's orientation is marked Devika-3/4 back facing left, pointing her gaze away from Agnivesh (center-mid, facing left) and breaking the 180° dialogue axis established in Shot 37. | Update Shot 38 Devika orientation to Devika-3/4 back facing right / Reframe as a clean profile Devika-profile facing right looking directly toward Agnivesh."

### `sb_dialogue_duration_headroom` (storyboard)
Give each dialogue shot enough duration for the full line at a natural speaking rate plus a pause/headroom; lengthen the shot rather than clip speech.

Seen in: UW Ep10, UW Ep15, UW Ep16, UW Ep4, UW Ep5, UW Ep7, UW ioc1, UW ioc2

- Ep7 · REVIEW ROWS: "🟡 Moderate | Duration sound & beat density | Shot 37 packs multi-step physical blocking (crouching, lifting the crown, turning it, raising gaze) and a 14-word solemn oath into 7s, creating severe beat crowding. | Split Shot 37 into Shot 37a (retrieving and inspecting the crown, 3s) and Shot 37b (raising eyes and delivering the oath, 5s) / Extend Shot 37 duration to 8s."
- Ep10 · REVIEW ROWS: "🟡 Moderate | Dialogue Pacing (Shots 13 & 34) | Shot 13 (25 words in 8s) and Shot 34 (21 words in 7s) have tight delivery windows. | Optional: Extend Shot 13 to 9s/10s and Shot 34 to 8s."
- Ep15 · REVIEW ROWS: "🟡 Moderate | Duration sound | Non-dialogue shots 21 (7s), 24 (7s), 40 (7s), 44 (7s), 62 (7s), 64 (9s), and 78 (9s) exceed the 6-second ceiling for shots without dialogue. | Trim durations of these non-dialogue shots down to ≤6s (e.g., 4s–6s) / Split extended 9s climax shots (64 and 78) into two connected action beats"

### `sb_total_duration_matches_target` (storyboard)
The row durations must sum to the episode's stated target; recompute after every edit and reconcile the manual's stated total.

Seen in: UW Ep16

- Ep16 · REVIEW ROWS: "🟡 Moderate | Total Duration Calibration | The current row-by-row sum is 332s across the 79 shots (short of your 348s target). | Calibrate shot durations to reach exactly 348s by adjusting the dialogue headroom and locked action beats."

Note: Only Ep16 audits flag this, but stats_vs_manual_derived shows the stated totals vs. row sums for every episode.

### `sb_shot_size_variety` (storyboard)
Avoid three consecutive shots of the same size (e.g. three close-ups in a row) and repetitive camera moves; vary the middle shot.

Seen in: UW Ep11, UW Ep12, UW Ep16

- Ep11 · REVIEW ROWS: "⚪ Minor | Shot-Size & Proportions | Shot 4 focuses strictly on an insert of the scorched cuff and inner wrist mark ("Foreground scorched fabric fibers... midground sword-shaped brand pulsing upon the inner right wrist..."), but shotSize is labeled medium shot. | Update Shot 4 shotSize from medium shot to close-up (or extreme close-up) for accurate scale and framing proportion."
- Ep12 · REVIEW ROWS: "🟡 Moderate | Camera move variety | Shots 20–25 and Shots 30–35 each feature 6 consecutive push-in moves (slow push in / push in / crash push-in), resulting in repetitive camera kinetics during the canyon fork debate. | Change Shot 24 to static on Ranvijay's obstinate declaration / Change Shot 31 to static or subtle pan left across the reflecting breastplate to break kinetic monotony."
- Ep16 · REVIEW ROWS: "⚪ Minor | Shot-size variety | Shots 34–36 and Shots 45–47 each feature three consecutive close-ups across alternating characters | Adjust the middle shot of each cluster (Shot 35 and Shot 46) to medium close-up or over-the-shoulder framing for smoother visual breathing"

### `sb_split_granularity` (storyboard)
Split shots on a change of perspective or action, not on every micro-reaction; merge static micro-splits.

Seen in: UW Ep10, UW Ep16, UW Ep7, UW ioc2

- Ep7 · REVIEW ROWS: "🟡 Moderate | Splitting granularity | Shot 28 duration is 9s, exceeding the 8s single-shot ceiling for vertical microdrama. | Trim Shot 28 to 6–7s by tightening Timiraksha's reaction pause / Split into Shot 28a (over-the-shoulder dismissive glance, 3s) and Shot 28b (dialogue delivery, 5s)."
- Ep10 · REVIEW ROWS: "🟡 Moderate | Dialogue Pacing (Shots 13 & 34) | Shot 13 (25 words in 8s) and Shot 34 (21 words in 7s) have tight delivery windows. | Optional: Extend Shot 13 to 9s/10s and Shot 34 to 8s."
- Ep16 · REVIEW ROWS: "🟡 Moderate | Splitting granularity & Pacing | The table totals 332s across 79 shots (a 2.65× expansion over the script's 125s baseline; also note the actual duration sum is 332s rather than the dispatched 348s), with micro-splitting on static beats (e.g., Shots 49 & 50 splitting Devika's hand contact into two 3s/2s frames without a perspective shift) | Merge micro-split reaction pairs (e.g., combine Shots 49 & 50 int …[clipped]"

### `sb_no_lighting_in_fields` (storyboard)
Do not write lighting, colour temperature or grading into storyboard fields; light comes from the locked scene reference images.

Seen in: UW Ep15, UW Ep7, UW ioc4

- Ep7 · REVIEW ROWS: "🟡 Moderate | Lighting description prohibition (R5) | Shots 44 and 46 include the word "shadow" ("beneath the demon's shadow", "beneath the shadow"), which conflicts with the strict prohibition on lighting/shadow terminology. | Replace "beneath the demon's shadow" with physical framing descriptions such as "beneath the towering asura king" / "under Timiraksha's looming silhouette"."
- Ep15 · REVIEW ROWS: "🔴 Critical | No lighting / colour grade in any field | Shot 77 description includes the directional lighting phrase "lit from below by blazing palm", violating the rule that lighting must be derived by the video model rather than written into storyboard prompts. | Rephrase to "Foreground Agnivesh's resolute face framed against his blazing palm, midground eyes narrowing with divine authority" / Rephrase to "Foreground …[clipped]"
- ioc4 · manual: "Build shot prompts referencing locked character, scene, and prop assets, strictly omitting explicit lighting, color temperature, or grading descriptions to ensure illumination and shadow relationships are derived automatically from the locked scene image references."

### `sb_script_coverage_attribution` (storyboard)
Every script line appears in the table, attributed to the speaker the script names (or the change is flagged as an option for the director).

Seen in: UW Ep10, UW Ep7

- Ep7 · REVIEW ROWS: "🔴 Critical | Script coverage (R2) | Shots 45–46 omit the script's climax: Agnivesh dropping the crown, darting forward, and bracing his raised shield between Timiraksha and Ranvijay. Instead, Shot 45 invents an unscripted defeat beat where Agnivesh is pinned on his knees clutching the crown, leaving Ranvijay defenseless. | Option A: Revise Shot 45 so Agnivesh drops the crown and charges forward, and revise Shot 46 in …[clipped]"
- Ep10 · REVIEW ROWS: "🔴 Critical | Script vs. Asset Attribution (Shot 54) | The original script gives the line "Mai bhi chalunga rajkumar." to ROYAL GUARD 3 (Asset: 4c3072a1-dfaf-4eac-93ec-01ee25463b94), whereas Shot 54 is currently assigned to ROYAL GUARD 5 (Asset: 54992d3b-40cd-4edb-aa8a-405289c0f26e). | Option A: Align with the original script by setting the speaker/asset to ROYAL GUARD 3.Option B: Retain ROYAL GUARD 5 as the active gu …[clipped]"


## Storyboard rules (from table patterns)

### `sb_action_carries_continuity` (storyboard)
Write Character Action as the physical sequence inside the shot and carry continuity forward explicitly (e.g. a 'Continuity:' note or '(Continuing previous shot…)').

Seen in: Durvasa 2 EP11, Durvasa 2 EP14, Durvasa EP2, Durvasa EP4V1, UW Ep1, UW Ep2, UW Ep3, UW Ep4

- Ep1 · storyboard.character_action: "The royal gong crashes and the citizens raise sun-emblem flags. The camera descends to the sand as Ranvijay rides in on the black stallion, which stops mid-arena with its bells ringing, and he raises his jeweled sword. Continuity: he enters from the south gate and travels screen-right."
- EP2 · storyboard.character_action: "(Continuation from previous shot: continuing uphill stride) Frost-crusted lips remain clamped shut -> chest expands in measured nasal breath -> chin tilts slightly upward"
- EP11 · storyboard.character_action: "(Continuing previous shot: holding garland at chest) Indra pivots torso 45 degrees right toward Airavat → raises garland outward with both hands toward elephant brow → chuckles aloud with elevated chin; Airavat stands calm beside dais"

### `sb_sound_layered_plus` (storyboard)
Write the Sound column as concrete layered effects joined with '+', with no music.

Seen in: Durvasa 2 EP11, Durvasa 2 EP12, Durvasa 2 EP14, Durvasa EP2, Durvasa EP3, Durvasa EP4V1, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc2, UW ioc3, UW ioc4, UW ioc5

- Ep1 · storyboard.sound_effects: "Royal gong crash + hooves thudding across dry sand + brass rein bells ringing + swelling crowd roar"
- EP2 · storyboard.sound_effects: "Staff crunching into frozen crust + whistling mountain wind"
- EP11 · storyboard.sound_effects: "Marble hall echo + silk fabric rustle"

Note: Some rows name crowd or temple chants (e.g. uw_Ep1_s002, uw_Ep5_s035, uw_Ep11_s003); the UW prompt style guide bans chanting melody, so treat chants as spoken/shouted only.

### `sb_dialogue_speaker_prefix` (storyboard)
Write Dialogue as 'Speaker: line' copied verbatim from the script; write 'None'/'No dialogue' for silent shots.

Seen in: Durvasa 2 EP11, Durvasa 2 EP12, Durvasa 2 EP13.1, Durvasa 2 EP14, Durvasa EP2, Durvasa EP3, Durvasa EP4V1, Durvasa EP4V2, UW Ep1, UW Ep10, UW Ep11, UW Ep12, UW Ep14.2, UW Ep15, UW Ep16, UW Ep2, UW Ep3, UW Ep4, UW Ep5, UW Ep6, UW Ep7, UW Ep8, UW Ep9, UW IOCSCRIPT1_V1, UW ioc1, UW ioc2, UW ioc3, UW ioc4, UW ioc5

- Ep1 · storyboard.dialogue: "Several Citizens: Dekho dekho kaun aaya...Suryagarh ka sher aaya...Rajkumar Ranvijay ki jay, Rajkumar Ranvijay ki jay"
- EP2 · storyboard.dialogue: "Krodha: Yeh adiyal aise nahi maanega."
- EP11 · storyboard.dialogue: "INDRA: Mujhse zyada... Mera Airavat iss samman ka adhikari hai."


## Production rules (Pratik / Ninni)

### `prod_dialogue_byte_for_byte` (dialogue)
Dialogue stays byte-for-byte as in the script: no rewording, translating, adding or dropping lines. Only the speaking character's mouth moves.

- uw_ioc2_manual.txt · line 49: "- Dialogue is used exactly as written in the script, word for word. No rewording, no added or removed lines."
- UW_PROMPT_STYLE_GUIDE.md · line 54: "- **Dialogue** in Devanagari, never reworded; shots and durations unchanged unless Pratik approves."
- MASTER_LOCKS_E10.md · line 4: "3. Dialogue in Devanagari only, the exact same words transliterated (no rewording)."

Note: Standing rule from Pratik's production memory; evidence lines show where it is written in production files.

### `prod_no_shot_changes_unless_asked` (shot_structure)
Never change shots, shot order, shot size, framing or durations beyond exactly what Pratik or Ninni ask for.

- uw_ioc2_manual.txt · line 61: "- Shot size and camera move follow the Storyboard Table. Shots, shot order and framing are not changed once approved."
- UW_PROMPT_STYLE_GUIDE.md · line 54: "- **Dialogue** in Devanagari, never reworded; shots and durations unchanged unless Pratik approves."

Note: Standing rule from Pratik's production memory; evidence lines show where it is written in production files.

### `prod_positions_lock_every_shot` (continuity)
Positions lock in every shot: each character's side, depth, posture and facing is written in every shot and carried from shot to shot and track to track.

- uw_ioc2_manual.txt · line 39: "Positions lock: Agnivesh frame-left, Devika frame-right facing him for 0-11s; when the door opens Ranvijay appears in the background doorway, and in 16-20s the triangle reads Agnivesh left, Devika centre, Ranvijay right. Keep these sides the same in every shot."
- UW_PROMPT_STYLE_GUIDE.md · line 28: "- **Name every character in every shot** with tag and chip, giving position (screen left / centre / right, foreground / mid / background), posture (standing…), movement and facing, separated by `;`."

Note: Standing rule from Pratik's production memory; evidence lines show where it is written in production files.

### `prod_no_eye_glow` (visual)
No eye glow on any character (natural eyes only), unless the director explicitly approves an exception.

- uw_ioc2_manual.txt · line 63: "- No eye glow on any character."
- UW_PROMPT_STYLE_GUIDE.md · line 22: "- **Costume locks** for each lead (Ranvijay, Agnivesh, guards), **IDENTITY** (never swap the brothers) and **NO EYE GLOW**."
- IOC2_video_prompt.txt · line 1: "…ince Ranvijay. Props: @Marriage Scroll (Hindi Devanagari writing only), @Royal sword. Smooth mechanical camera only, no handheld, no whip-pans, no crash zooms. No eye glow. No music, SFX only. Only the speaking character's mouth moves; everyone else keeps mouth closed. Dialogue in Hindi exactly as written. …[clipped]"

Note: Standing rule from Pratik's production memory; evidence lines show where it is written in production files.

### `prod_location_matches_plate` (location)
The rendered location must match its location reference asset exactly, used as the background plate; no redesigned layouts or mixed conflicting location refs.

- uw_ioc2_manual.txt · line 57: "- The rendered location must match the location asset exactly, used as the background plate. No invented or redesigned layout, no mixing of conflicting location refs."
- IOC2_video_prompt.txt · line 1: "IOC2 "Ek Dulhan, Do Rajkumar" - 20s, 16:9, one continuous location: @Rajmahal Royal Chamber used exactly as the background plate (same layout, door, bed, pillars, diyas). Characters exactly as their refs: @Agnivesh, @Devika (wearing red bridal vastra and bridal jewellery), @Prince Ranvijay. Props: @Marriage Scroll (Hin …[clipped]"

Note: Standing rule from Pratik's production memory; evidence lines show where it is written in production files.

### `prod_devanagari_visible_text` (visible_text)
Any visible on-screen text in assets or frames (scrolls, decrees, banners, inscriptions) is Hindi Devanagari only.

- IOC2_video_prompt.txt · line 1: "…diyas). Characters exactly as their refs: @Agnivesh, @Devika (wearing red bridal vastra and bridal jewellery), @Prince Ranvijay. Props: @Marriage Scroll (Hindi Devanagari writing only), @Royal sword. Smooth mechanical camera only, no handheld, no whip-pans, no crash zooms. No eye glow. No music, SFX only. Only the spea …[clipped]"
- MASTER_LOCKS.md · line 3: "1. Dialogue is in Devanagari ONLY. No Roman-letter copy."
- UW_CONTINUITY_SHEET.md · line 10: "- **Dialogue stays in Devanagari** and is never changed."

Note: Standing rule from Pratik's production memory; evidence lines show where it is written in production files. Dialogue script itself follows the episode lock: UW video prompts used Devanagari (style guide, Ep9/Ep10 master locks), Kronicle storyboards store Roman Hindi, and Durvasa 2 prompt QC (kronicle/qc_EP12.md) required Roman. Keep whichever the episode locks, verbatim.

### `prod_no_music` (sound)
No music in sound: SFX and dialogue only; no score, songs, singing or chanting melody, and no musical wording in prompts.

- uw_ioc2_manual.txt · line 33: "No music. SFX only: diya flame crackle, soft rustle of bridal fabric and bangles, scroll unrolling on wood, footsteps, heavy door slamming open, sword ring. Narrator voice-over only in 16-20s."
- UW_PROMPT_STYLE_GUIDE.md · line 49: "- **Always**: no hole, crack, opening or skylight in the roof; no music, score, songs, singing or chanting melody; no glowing eyes, no eye glow, no luminous irises; no duplicate Ranvijay; no villagers; no sword standing upright or stuck in the floor."
- IOC2_video_prompt.txt · line 1: "…. Props: @Marriage Scroll (Hindi Devanagari writing only), @Royal sword. Smooth mechanical camera only, no handheld, no whip-pans, no crash zooms. No eye glow. No music, SFX only. Only the speaking character's mouth moves; everyone else keeps mouth closed. Dialogue in Hindi exactly as written. …[clipped]"

Note: Standing rule from Pratik's production memory; evidence lines show where it is written in production files.

