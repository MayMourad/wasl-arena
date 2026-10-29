# WASL Arena: One family. Three games. One fair AI referee.

**6th Annual COE STEM Programming with AI Competition · Abu Dhabi University · Theme: AI for Family**

| | |
|---|---|
| **Team** | 204 |
| **Team code** | AYUCK |
| **Track** | Cycle 3: grades 9-12 |
| **Members** | May Ahmed Mourad (G12) · Shamsa Faris Almazrouei (G12) · Fatima Mohamed Almazrouei (G11) |
| **Challenge** | Family AI Game Day: football + two original games, judged by AI from real video and audio |

WASL Arena is a working web app where a family plays three games while an AI referee watches the video, listens to the audio, applies written rules and keeps score. Every score is backed by **replayable evidence** (source video, timestamps, annotated frames, rule applied, status). If the AI cannot see it, the call is `NEEDS_REVIEW` and the human host decides.

| Game | Mode | What the AI does |
|---|---|---|
| **Football AI** | Team | Tracks ball and players, detects goals in calibrated zones, measures possession, MVP = longest possession |
| **Falaj Flow** | Team | Reads a printed 5x5 board and tiles (ArUco markers), rebuilds the channel network as a graph, traces water to three farms |
| **Souq Signal** | Individual | Recognises product cards, transcribes Arabic/English speech, checks audio and video agree, does budget maths |

## Screens (all working)
Launch · Family Setup · Game Library · Game Preparation · Live Arena · AI Referee Replay · Family Cup · Evaluation Lab. Printable boards, tiles and cards are in `frontend/public/printables/`.

## Repository layout
```
frontend/      React + TypeScript + Vite + Tailwind (+ Three.js orb)
backend/       FastAPI judge: app/rules (deterministic), app/vision (OpenCV/FFmpeg), tests/
tools/         fixtures, printables, sample export, screenshots, report converters
fixtures/      SYNTHETIC test clips + manifest (ground truth)   [mp4s git-ignored; regenerate]
docs/          6-page technical report (.docx + .pdf), figures, screenshots
presentation/  30-slide deck (.pptx, editable) + generator
video/         120 s production package + draft animatic
ai-usage/      AI chat usage report + original conversation exports (redacted)
```

## Run locally
```bash
# backend (Python 3.11+)
cd backend && python -m venv .venv && .venv/Scripts/activate   # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add GEMINI_API_KEY (speech transcription only) and a JUDGE_SIGNING_KEY
uvicorn app.main:app --port 8000

# frontend
cd frontend && npm install && npm run dev      # Vite proxies /api to :8000
```

## Tests (all actually run)
```bash
cd backend
python ../tools/make_fixtures.py     # synthetic fixtures with known ground truth
pytest                               # 46 tests: rules, CV pipelines, integrity, API, audit chain
python ../tools/export_samples.py    # re-generates frontend/public/samples + evaluation.json
```
Last run: **46/46 passed**; 9/9 synthetic fixtures match ground truth. The fixtures are **synthetic renders, not real gameplay**; no real family footage has been analysed yet and no accuracy percentage is claimed.

## Stand-alone AI judge (hash-verified)
```bash
python -m app.judge_cli football match.mp4 -o report.json     # also: falaj, souq
```
Import `report.json` in Live Arena → "Import AI report". The app verifies SHA-256 + HMAC and rejects edited reports.

## Deploy
* **Frontend → Vercel:** import this repo, set *Root Directory* = `frontend`, add env `VITE_API_URL=https://<your-render-service>.onrender.com`.
* **Backend → Render:** `render.yaml` (root dir `backend`). Set `GEMINI_API_KEY`, `JUDGE_SIGNING_KEY`, `CORS_ORIGINS=https://<your-vercel-app>.vercel.app`.
* Credentials live only in server environment variables. `.env` is git-ignored.

**Live deployment (verified):**
* App: https://frontend-three-fawn-47.vercel.app
* AI judge API: https://wasl-arena.onrender.com/api/health
* Checked: all routes 200, header badge "AI judge online", a Falaj fixture judged on the live backend scored 11 with a valid integrity seal, CORS restricted to the Vercel origin.
* Free-tier hosting sleeps when idle (first request ~30 s) and does not persist uploads.

## Honest limitations
Controlled setup (fixed camera, single-colour ball, contrasting shirts, calibrated goals); colour segmentation is lighting-sensitive; shirt numbers are not read (host assigns tracks to players); printed markers can be hidden; speech timing is approximate (about 1 s); detection scores are heuristics, not calibrated probabilities.

## AI assistance
Built with ChatGPT (concept) and Claude Code / Claude Sonnet 5.5 (implementation); Gemini used at runtime for transcription only. See `ai-usage/`.
