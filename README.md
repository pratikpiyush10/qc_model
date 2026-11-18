# Scene QC

**Repository:** https://github.com/pratikpiyush10/qc_model

Scene QC is a local web app for microdrama continuity checks and a separate clothing fix. Upload an MP4, review the key frames, and read timestamped issues from Gemini. The same results page offers direction suggestions drawn from the continuity rules and the director's manuals. The clothing fix sends the clip and a reference image to Seedance 2.5 and does not run a quality check. Videos, frames, and job files stay on this machine.

## Features

- Upload an MP4 and follow extraction and analysis on a progress screen.
- Extract key frames (opening, scene change, interval, and ending) and keep the full gallery on the results page.
- Send those frames to Gemini 3.8 Flash through the LiteLLM proxy.
- Show issues in a table: Timestamp, Type of error, Severity, Description, and frame thumbnails.
- **Continuity** rules page, from `continuity_dataset/rules.jsonl`.
- **Direction** rules page, from `manual_dataset/rules.jsonl`.
- **Director's Input** page, one episode manual at a time (theme, camera, pacing, scene intent, continuity anchors).
- **Director's Suggestions** on the results page, matched to the issues already found. This box does not call Gemini again.
- **Minimal fix** page for clothing only. Pick frames of the current look, add one or more JPEG, PNG, or WebP images of the desired look, and optionally write what should change. Seedance 2.5 edits the clip through the same LiteLLM proxy. The result is Original next to Fixed, with a download.

Open the rules, direction, and manual pages from the **Guides** button.

## Tech stack

- FastAPI and Uvicorn
- Plain HTML, CSS, and JavaScript
- OpenCV (headless) for key-frame extraction
- LiteLLM proxy at `https://litellm.kukufm.com`
- Vision model `google/gemini-3.8-flash`
- Video model `runwayml/seedance2_5` (Seedance 2.5) for the clothing fix

## Setup

Clone the repository and move into the project folder:

```powershell
git clone https://github.com/pratikpiyush10/qc_model.git
cd qc_model
```

Create a virtual environment and install dependencies. Python 3.14 is the version this project uses.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a `.env` file in the project root and set the LiteLLM key. The same key is used for the Gemini quality check and the Seedance clothing fix:

```
LITELLM_API_KEY=your_api_key
```

Do not commit `.env`. It is listed in `.gitignore`. The server reads it at startup. Restart the server after you change the key. A value already set in the shell overrides `.env`.

Optional settings, also read at startup:

| Variable | Default | What it does |
| --- | --- | --- |
| `QC_ANALYSIS_LEVEL` | `high` | Vision pass size: `low`, `medium`, or `high` |
| `QC_LITELLM_MODEL` | `google/gemini-3.8-flash` | Model for the quality check |
| `QC_SEEDANCE_MODEL` | `runwayml/seedance2_5` | Model for the clothing fix |
| `QC_LITELLM_BASE_URL` | `https://litellm.kukufm.com` | LiteLLM proxy |
| `QC_MAX_UPLOAD_MB` | `400` | Upload size limit |

Start the server from the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Stop the server with Ctrl+C.

Without a key, frame extraction still finishes. The results page reports that the key is missing. The clothing fix also stops and asks for the key.

## How to use

1. The home page has two paths. **Open QC** goes to the quality-check page. **Open Minimal Fix** goes to the clothing-fix page. H.264 in an MP4 is the expected input. The upload limit is 400 MB, and the QC scan stops at 20 minutes. The fix page does not run QC.
2. On the QC path, wait on the progress view while frames are extracted and then reviewed.
3. On the results page, read the issues table. Severity is shown as Low, Medium, or High. Click a timestamp or a thumbnail to focus that key frame. The full gallery stays below the table.
4. Read **Director's Suggestions** under the table. When the analysis finished with issues, the suggestions point at the matching timestamps. When it finished with none, the box shows standing continuity checks.
5. Use **Guides** for Continuity rules, Direction rules, and Director's Input. Those pages are separate from the QC pass. Episode manuals and direction rules are not sent to Gemini.
6. On **Minimal Fix**, upload the clip, then select one or more frames of the current look and at least one image of the desired clothing. **Generate Fix** stays off until both are set. Several desired-look images are combined into one JPEG. The prompt sent with the job names the selected timestamps and any note you typed. Seedance keeps the motion, face, camera, and background, and changes the clothing to match the reference. Clips longer than 30 seconds are rejected. When the job finishes, compare Original and Fixed, download the MP4, or try again. **Accept Fix** stores a local note only.

Recent jobs on the upload screen reopen a finished check. A job URL (`/#/jobs/<id>`) restores progress or results. A fix URL (`/#/fix/<id>`) reopens the clothing-fix setup for that clip.

The default analysis level is `high`: up to 80 key frames, in groups of 4 around each cut. Set `QC_ANALYSIS_LEVEL` to `low` or `medium` before starting the server if you want a smaller vision pass. Restart after changing it.

## Project structure

```
backend/app/main.py         HTTP routes and the static frontend
backend/app/pipeline.py     Extraction, then the LiteLLM vision pass
backend/app/fix_pipeline.py Seedance clothing fix through LiteLLM /v1/videos
backend/app/extractor.py    Key-frame selection
backend/app/rules.py        Continuity rules
backend/app/direction.py    Direction rules
backend/app/director.py     Per-episode director's manuals
backend/app/store.py        One JSON file per QC job, and fix-job records
backend/app/config.py       Paths, limits, and the LiteLLM settings
frontend/                   Home, QC, clothing fix, guides, and suggestions
continuity_dataset/         Continuity rules used by the Rules page and the vision prompt
manual_dataset/             Direction rules and episode manuals
data/                       Uploads, frames, jobs, and fixes (local only)
requirements.txt            Python dependencies
.env                        LiteLLM key (not committed)
```

Interactive API docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) while the server is running.
