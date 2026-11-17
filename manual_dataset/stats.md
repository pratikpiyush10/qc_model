# Dataset statistics

All numbers computed by `tools/make_stats.py` from the JSONL files. Buckets are derived labels (see schema.json).

## Episodes

| Show | Ep | Version | Title (derived) | Manual | Shots | Row-sum s | Manual says (shots / s) | Dialogue shots | Scene runs | Reviews | Script paired | Split |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Maharishi Durvasa | EP2 | — | The Frozen Ascent | yes | 22 | 100 | — / — | 4 | 1 | 0 | — | train |
| Maharishi Durvasa | EP3 | — | — | yes | 17 | 97 | — / — | 9 | 7 | 0 | — | val |
| Maharishi Durvasa | EP4 | V1 | — | no | 24 | 122 | — / — | 14 | 3 | 0 | — | train |
| Maharishi Durvasa | EP4 | V2 | — | yes | 24 | 90 | — / — | 14 | 2 | 0 | — | train |
| Maharishi Durvasa 2 | EP11 | — | — | no | 27 | 135 | — / — | 15 | 3 | 0 | — | train |
| Maharishi Durvasa 2 | EP12 | — | — | no | 27 | 108 | — / — | 12 | 2 | 0 | kronicle/script_EP12.md | val |
| Maharishi Durvasa 2 | EP13.1 | — | — | no | 43 | 181 | — / — | 26 | 5 | 0 | ep13_1/script.md | train |
| Maharishi Durvasa 2 | EP14 | — | — | no | 48 | 241 | — / — | 21 | 3 | 0 | kronicle/script_EP14.md | train |
| Ultimate Warrior | Ep1 | — | The Eclipse Prince | yes | 38 | 286 | 38 / 286 | 28 | 6 | 0 | uw2/scripts/EP1.txt | train |
| Ultimate Warrior | Ep2 | — | Khatre ka Sanket | yes | 46 | 262 | 46 / 262 | 24 | 4 | 2 | uw2/scripts/EP2.txt | train |
| Ultimate Warrior | Ep3 | — | Mita Hua Rajkumar | yes | 49 | 305 | 49 / 305 | 17 | 3 | 0 | uw2/scripts/EP3.txt | val |
| Ultimate Warrior | Ep4 | — | Dwaar Ka Rakshak | yes | 79 | 332 | 79 / 332 | 22 | 28 | 0 | uw2/scripts/EP4.txt | train |
| Ultimate Warrior | Ep5 | — | Andhere Ka Dwaar | yes | 83 | 321 | — / — | 30 | 32 | 14 | uw2/scripts/EP5.txt | train |
| Ultimate Warrior | Ep6 | — | Champion Ka Patan | yes | 69 | 270 | — / — | 19 | 6 | 0 | — | train |
| Ultimate Warrior | Ep7 | — | Timiraksha Ka Daava | yes | 46 | 182 | — / — | 14 | 2 | 13 | — | train |
| Ultimate Warrior | Ep8 | — | The Awakening of the Solar Heir | yes | 47 | 198 | — / — | 17 | 1 | 0 | — | train |
| Ultimate Warrior | Ep9 | — | Andhere Ka Vortex | yes | 50 | 193 | — / — | 11 | 1 | 2 | — | val |
| Ultimate Warrior | Ep10 | — | Maha Yoddha Ka Aadesh | yes | 64 | 269 | — / — | 21 | 1 | 4 | — | train |
| Ultimate Warrior | Ep11 | — | MAA KA VACHAN | yes | 39 | 150.5 | — / — | 9 | 4 | 9 | — | train |
| Ultimate Warrior | Ep12 | — | Rajmarg Ka Jaala | yes | 51 | 176 | — / — | 19 | 4 | 3 | — | train |
| Ultimate Warrior | Ep14.2 | — | Pita Ka Jhooth | yes | 58 | 246 | — / — | 17 | 3 | 0 | — | train |
| Ultimate Warrior | Ep15 | — | Surya Ka Shikaar | yes | 84 | 352 | — / — | 27 | 3 | 3 | — | train |
| Ultimate Warrior | Ep16 | — | Mace Over the Gorge | yes | 79 | 348 | 79 / 344 | 38 | 1 | 13 | — | train |
| Ultimate Warrior | ioc1 | — | — | yes | 7 | 20 | — / — | 5 | 2 | 1 | uw_ioc/ioc_doc.txt#section1 | train |
| Ultimate Warrior | ioc2 | — | Ek Dulhan, Do Rajkumar | yes | 7 | 20 | — / — | 4 | 1 | 3 | uw_ioc/IOC2_script.txt | train |
| Ultimate Warrior | ioc3 | — | The Royal Darbar Awakening | yes | 7 | 21 | — / — | 3 | 1 | 0 | uw_ioc/ioc_doc.txt#section3 | train |
| Ultimate Warrior | ioc4 | — | — | yes | 8 | 20 | — / — | 4 | 1 | 1 | uw_ioc/ioc_doc.txt#section4 | val |
| Ultimate Warrior | ioc5 | — | — | yes | 8 | 18 | — / — | 5 | 3 | 0 | uw_ioc/ioc_doc.txt#section5 | train |
| Ultimate Warrior | IOCSCRIPT1_V1 | — | Suryagarh Shrapit Shishu | yes | 22 | 82 | — / — | 13 | 2 | 6 | uw_ioc/IOC1_script.txt | train |

Totals: 29 episode records (24 with a manual), 1173 shots (Ultimate Warrior 941, Maharishi Durvasa 87, Maharishi Durvasa 2 145), 5145.5 s of storyboarded time, 91 review rows.

## Shot craft distributions (all shows)

### Shot size bucket (derived)

| Value | Count | % |
|---|---|---|
| MS | 331 | 28.2 |
| MCU | 224 | 19.1 |
| WS | 186 | 15.9 |
| CU | 168 | 14.3 |
| MWS | 105 | 9.0 |
| FS | 88 | 7.5 |
| ECU | 31 | 2.6 |
| EWS | 23 | 2.0 |
| OTHER | 15 | 1.3 |
| OTS | 2 | 0.2 |

### Camera move buckets (derived, multi-label)

| Value | Count | % |
|---|---|---|
| push_in | 432 | 30.6 |
| track_dolly | 302 | 21.4 |
| static | 151 | 10.7 |
| tilt | 129 | 9.1 |
| crane_jib_pedestal | 83 | 5.9 |
| arc_orbit | 65 | 4.6 |
| pan | 57 | 4.0 |
| handheld | 52 | 3.7 |
| other | 37 | 2.6 |
| pull_back | 32 | 2.3 |
| speed_ramp | 20 | 1.4 |
| whip | 20 | 1.4 |
| zoom | 15 | 1.1 |
| rack_focus | 10 | 0.7 |
| aerial_drone | 6 | 0.4 |

### Most common raw Shot Size strings

| Value | Count | % |
|---|---|---|
| medium shot | 199 | 17.0 |
| medium close-up | 156 | 13.3 |
| close-up | 122 | 10.4 |
| wide shot | 99 | 8.4 |
| full shot | 47 | 4.0 |
| Medium Shot | 43 | 3.7 |
| Medium Close-Up | 28 | 2.4 |
| medium long shot | 23 | 2.0 |
| Full Shot | 22 | 1.9 |
| Wide Shot | 21 | 1.8 |
| Medium Wide | 16 | 1.4 |
| extreme close-up | 15 | 1.3 |
| Medium, Low angle | 14 | 1.2 |
| Medium Long Shot | 12 | 1.0 |
| medium wide shot | 11 | 0.9 |

### Most common raw Camera Movement strings

| Value | Count | % |
|---|---|---|
| slow push in | 104 | 9.2 |
| static | 84 | 7.4 |
| push in | 58 | 5.1 |
| fast push in | 27 | 2.4 |
| low-angle push in | 18 | 1.6 |
| crash push in | 14 | 1.2 |
| low angle push in | 14 | 1.2 |
| tilt down | 9 | 0.8 |
| tilt up | 9 | 0.8 |
| crash push-in | 9 | 0.8 |
| slow push | 8 | 0.7 |
| slow tilt up | 8 | 0.7 |
| track | 8 | 0.7 |
| Slow push-in; 9:16 vertical composition, all characters fully inside frame | 7 | 0.6 |
| track forward | 7 | 0.6 |

### Shot duration (s)

min 1 · median 4 · mean 4.39 · max 15

### Review severity (derived)

| Value | Count | % |
|---|---|---|
| moderate | 31 | 34.1 |
| critical | 28 | 30.8 |
| n/a (prompt QC) | 17 | 18.7 |
| minor | 15 | 16.5 |

## Training pairs

| Pair type | Total | Train | Val |
|---|---|---|---|
| beat_to_shot_plan | 42 | 36 | 6 |
| manual_to_storyboard | 198 | 175 | 23 |
| row_to_critique | 74 | 71 | 3 |
| scene_intent_to_shots | 108 | 99 | 9 |
| script_to_manual | 11 | 9 | 2 |
| script_to_manual_section | 79 | 65 | 14 |
| script_to_storyboard | 16 | 12 | 4 |
| section_to_section | 144 | 120 | 24 |
| storyboard_revision | 3 | 3 | 0 |
| rules (chat) | 45 | 45 | 0 |

## Chat files

train_chat.jsonl: 635 examples · val_chat.jsonl: 85 examples (val episodes: UW Ep3, Ep9, ioc4; Durvasa 2 EP12; Kronicle Durvasa EP3).
User+assistant characters per example: median 7,526, max 48,145. Use `convert_to_chat.py --max-chars N` to cap length.

## Rules

45 rules: distilled_from_manual_patterns 24, distilled_from_kronicle_reviews 11, distilled_from_storyboard_patterns 3, pratik_production_rule 7
