<div align="center">

<img src="frontend/public/favicon.svg" width="72" alt="WASL Arena logo" />

# WASL Arena

### One family. Three games. One fair AI referee.

**6th Annual COE STEM Programming with AI Competition · Abu Dhabi University · Theme: AI for Family**

[![Live prototype](https://img.shields.io/badge/%E2%96%B6%20LIVE%20PROTOTYPE-open%20the%20app-167E80?style=for-the-badge)](https://frontend-three-fawn-47.vercel.app)
[![Walkthrough](https://img.shields.io/badge/WATCH-full%20walkthrough%20(MP4)-12243A?style=for-the-badge)](docs/tour/website-tour.mp4)
[![Slides](https://img.shields.io/badge/DOWNLOAD-slides%20PDF-C6A36B?style=for-the-badge)](https://github.com/MayMourad/wasl-arena/releases/download/v1.0-submission/WASL-Arena-30-Slides.pdf)

![Team](https://img.shields.io/badge/Team-204-12243A) ![Code](https://img.shields.io/badge/Team%20code-AYUCK-167E80) ![Track](https://img.shields.io/badge/Track-Cycle%203%20%C2%B7%20grades%209--12-B92D39) ![Tests](https://img.shields.io/badge/tests-46%2F46%20passing-167E80)

<a href="https://frontend-three-fawn-47.vercel.app"><img src="docs/tour/website-tour.gif" alt="WASL Arena: recorded walkthrough of the live website" width="860" /></a>

*A recording of the real, deployed website: launch screen, family setup, game library, a live upload judged by the production AI backend, the AI Referee Replay with host review, and the Family Cup. [Full video »](docs/tour/website-tour.mp4)*

</div>

---

## Try the prototype (60 seconds)

| Step | Where | What you will see |
|---|---|---|
| 1 | **[Open the app](https://frontend-three-fawn-47.vercel.app)** | The AI-Referee orb reacts to its state (Idle, Watching, Processing, Verified, Review). The header badge shows **AI judge online**. |
| 2 | **See an AI Referee Replay** (button on the launch screen) | A real judged clip: video with tracking overlay, evidence frames, the rule applied, score change, verification status, integrity hashes. |
| 3 | [Falaj Flow replay](https://frontend-three-fawn-47.vercel.app/replay?report=sample-falaj_valid) | Split screen: the physical board and the digital twin rebuilt by the AI, water tracing the validated route. |
| 4 | [Souq Signal replay](https://frontend-three-fawn-47.vercel.app/replay?report=sample-souq_correct_gemini) | Cards recognised, speech transcribed (Arabic/English), verified basket and budget. |
| 5 | **Live Arena → Upload video → Send to AI Referee** | Your own clip is judged by the live backend through five real stages, then opens in Replay. |
| 6 | [Evaluation Lab](https://frontend-three-fawn-47.vercel.app/lab) | The tests that actually ran, expected vs actual, and an honest synthetic-vs-real note. |

> The free-tier AI judge sleeps when idle: the first live upload after a break can take about 30 s. The sample replays work instantly.

**Links:** [App](https://frontend-three-fawn-47.vercel.app) · [AI judge health](https://wasl-arena.onrender.com/api/health) · [Walkthrough video](docs/tour/website-tour.mp4) · [Technical report (PDF)](https://github.com/MayMourad/wasl-arena/releases/download/v1.0-submission/WASL-Arena-Technical-Report.pdf) · [All release downloads](https://github.com/MayMourad/wasl-arena/releases/tag/v1.0-submission) · [Recording guide](docs/REAL_FOOTAGE.md)

## The team

| Team | Code | Track |
|---|---|---|
| **204** | **AYUCK** | **Cycle 3: grades 9-12** |

May Ahmed Mourad (G12) · Shamsa Faris Almazrouei (G12) · Fatima Mohamed Almazrouei (G11)

## What it is

WASL Arena is a working web app where a family plays three games while an AI referee watches the video, listens to the audio, applies written rules and keeps score. Every score is backed by **replayable evidence** (source video, timestamps, annotated frames, rule applied, status). If the AI cannot see it, the call is `NEEDS_REVIEW` and the human host decides.

| Game | Mode | What the AI does |
|---|---|---|
| **Football AI** | Team | Tracks ball and players, detects goals in calibrated zones, measures possession, MVP = longest possession |
| **Falaj Flow** | Team | Reads a printed 5x5 board and tiles (ArUco markers), rebuilds the channel network as a graph, traces water to three farms |
| **Souq Signal** | Individual | Recognises product cards, transcribes Arabic/English speech, checks audio and video agree, does budget maths |

## The full website, screen by screen

Full-page captures of the deployed site, recorded in a real browser session (click any image for full size).

<table>
<tr>
<td width="50%"><a href="docs/fullpage/01-launch.png"><img src="docs/fullpage/01-launch.png" alt="Launch screen" /></a><br/><b>1 · Launch</b>: interactive AI-Referee orb, pipeline, games, team</td>
<td width="50%"><a href="docs/fullpage/02-setup-teams.png"><img src="docs/fullpage/02-setup-teams.png" alt="Family setup" /></a><br/><b>2 · Family Setup</b>: players, teams, language, match rules</td>
</tr>
<tr>
<td><a href="docs/fullpage/03-library.png"><img src="docs/fullpage/03-library.png" alt="Game library" /></a><br/><b>3 · Game Library</b>: exactly three games, team and individual</td>
<td><a href="docs/fullpage/04-prepare-football.png"><img src="docs/fullpage/04-prepare-football.png" alt="Game preparation" /></a><br/><b>4 · Game Preparation</b>: rules, goal calibration, equipment, printables</td>
</tr>
<tr>
<td><a href="docs/fullpage/05-arena-clip-ready.png"><img src="docs/fullpage/05-arena-clip-ready.png" alt="Live arena" /></a><br/><b>5 · Live Arena</b>: camera/mic or upload, timer, turns, scoreboard</td>
<td><a href="docs/fullpage/05-judging-stages.png"><img src="docs/fullpage/05-judging-stages.png" alt="Judging stages" /></a><br/><b>5b · Live judging</b>: real stages from the production AI judge</td>
</tr>
<tr>
<td><a href="docs/fullpage/06-replay-needs-review.png"><img src="docs/fullpage/06-replay-needs-review.png" alt="AI Referee Replay with a call needing review" /></a><br/><b>6 · AI Referee Replay</b>: a NEEDS_REVIEW call, evidence, rule, accept/reject</td>
<td><a href="docs/fullpage/08-replay-falaj.png"><img src="docs/fullpage/08-replay-falaj.png" alt="Falaj replay with digital twin" /></a><br/><b>6b · Falaj replay</b>: physical board + digital twin, water on validated edges</td>
</tr>
<tr>
<td><a href="docs/fullpage/09-replay-souq.png"><img src="docs/fullpage/09-replay-souq.png" alt="Souq replay" /></a><br/><b>6c · Souq replay</b>: card recognition, transcript, verified basket</td>
<td><a href="docs/fullpage/07-cup-live-result.png"><img src="docs/fullpage/07-cup-live-result.png" alt="Family Cup" /></a><br/><b>7 · Family Cup</b>: results with reasons, MVP, standings</td>
</tr>
<tr>
<td colspan="2"><a href="docs/fullpage/11-lab.png"><img src="docs/fullpage/11-lab.png" alt="Evaluation lab" /></a><br/><b>8 · Evaluation Lab</b>: tests that actually ran, expected vs actual, limitations</td>
</tr>
</table>

*The Cup and live-judging captures come from a scripted tour that uploads a clearly named **synthetic test clip**. They demonstrate the product flow, not real family gameplay.*

**Responsive:** the same site on a phone.

<p>
<img src="docs/screenshots/m-01-launch.png" width="23%" alt="Mobile launch" /> <img src="docs/screenshots/m-02-games.png" width="23%" alt="Mobile game library" /> <img src="docs/screenshots/m-03-replay.png" width="23%" alt="Mobile replay" />
</p>

## How the AI judges (and shows its work)

<img src="docs/figures/pipeline.png" alt="AI judging pipeline" />

<table>
<tr>
<td width="50%"><img src="frontend/public/samples/evidence/football_goal/goal-2-moment.jpg" alt="Football evidence frame" /><br/>Football: evidence frame (ball trail, player tracks, goal zone), from a synthetic fixture</td>
<td width="50%"><img src="frontend/public/samples/evidence/falaj_valid/final-board.jpg" alt="Falaj evidence frame" /><br/>Falaj: board read from video, tiles recognised, water path in teal (synthetic fixture)</td>
</tr>
</table>

<img src="docs/figures/architecture.png" alt="System architecture" />

## Repository layout
```
frontend/      React + TypeScript + Vite + Tailwind (+ Three.js orb)  -> Vercel
backend/       FastAPI judge: app/rules (deterministic), app/vision (OpenCV/FFmpeg), tests/  -> Render
tools/         fixtures, printables, sample export, screenshots, tour recorder, converters
fixtures/      SYNTHETIC test clips + manifest (ground truth)   [mp4s git-ignored; regenerate]
docs/          technical report (.docx + .pdf), figures, screenshots, full-page captures, website tour
presentation/  30-slide deck (.pptx + .pdf) + generator
video/         120 s production package, final script PDF, draft animatic
ai-usage/      AI chat usage report + original conversation exports (redacted)
```
Printable boards, tiles and cards: `frontend/public/printables/` (also linked from the Prepare screen).

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
python ../tools/export_samples.py    # regenerates frontend/public/samples + evaluation.json
```
Last run: **46/46 passed**; 9/9 synthetic fixtures match ground truth. The fixtures are **synthetic renders, not real gameplay**; no real family footage has been analysed yet and no accuracy percentage is claimed.

## Stand-alone AI judge (hash-verified)
```bash
python -m app.judge_cli football match.mp4 -o report.json     # also: falaj, souq
```
Import `report.json` in Live Arena → "Import AI report". The app verifies SHA-256 + HMAC and rejects edited reports.

## Deploy
* **Frontend → Vercel:** Root Directory `frontend`, env `VITE_API_URL=https://<render-service>.onrender.com`.
* **Backend → Render:** root dir `backend` (`render.yaml`). Set `GEMINI_API_KEY`, `JUDGE_SIGNING_KEY`, `CORS_ORIGINS=https://<vercel-app>.vercel.app`.
* Credentials live only in server environment variables. `.env` is git-ignored.

**Live deployment (verified):** app https://frontend-three-fawn-47.vercel.app · AI judge https://wasl-arena.onrender.com/api/health. All routes return 200, the header badge shows "AI judge online", a Falaj fixture judged on the live backend scored 11 with a valid integrity seal, CORS is restricted to the Vercel origin. Free-tier hosting sleeps when idle and does not persist uploads.

## Honest limitations
Controlled setup (fixed camera, single-colour ball, contrasting shirts, calibrated goals); colour segmentation is lighting-sensitive; shirt numbers are not read (host assigns tracks to players); printed markers can be hidden; speech timing is approximate (about 1 s); detection scores are heuristics, not calibrated probabilities.

## AI assistance
Built with ChatGPT (concept) and Claude Code / Claude Sonnet 5.5 (implementation); Gemini used at runtime for transcription only. See [`ai-usage/`](ai-usage/).
