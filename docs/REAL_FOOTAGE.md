# Recording real gameplay for WASL Arena (Team 204 · AYUCK)

Why: the judges want to see the AI judging **real play**. Our tests so far use synthetic clips, so these recordings are the most valuable thing left. Record **two kinds** of footage for each game:

1. **Judging clips** (30-60 s, landscape): uploaded to the live app. These produce the real results.
2. **Screen recording** of the app while it judges: used in the video (clips 04-08, 10-12, 14-16, 18-23).

Everyone filmed must agree to be filmed. Keep faces out of frame if possible.

## Before you start (5 min)
- Open https://frontend-three-fawn-47.vercel.app and wait for the badge **"AI judge online"** (the free server sleeps; the first load can take ~30 s).
- Family Setup: enter the family, players (P1-P4), teams (A = P1+P2, B = P3+P4) and pick **different shirt colours** (red vs blue works best; **not green**, not the same as the ball).
- Phone: landscape, **1080p, 30 fps**, tripod or something stable, lens cleaned, **no zoom, no auto-HDR/beauty filters**, airplane mode on. Charge it.
- Keep each clip **under 60 s and under 100 MB** (free server memory is limited).

## 1. Football AI (team game) - judging clip + video clip 09
**Kit:** a bright **yellow or orange** ball (a tennis ball works), two goals marked with cones/tape (about 2 m wide), two teams in clearly different shirt colours (red vs blue), 2-3 players per team.

**Camera:** fixed and **high** (balcony, stairs, or a tripod on a table at the edge), whole pitch and **both goals** in frame, goals near the **left and right edges**, even daylight, no strong shadows over the goals.

**Calibrate:** Prepare → Football AI: drag the sliders so the gold goal boxes sit over your real goals; pick the ball colour and team colours (matching the shirts).

**Record 3 takes (30-60 s each):**
- **Take A, clean goal:** Team A scores once clearly into the right goal. The ball must be seen **outside** the goal zone first, then inside it. Expected result: VERIFIED goal.
- **Take B, no goal:** shots that miss wide. Expected: no goal.
- **Take C, uncertain:** someone briefly blocks the camera's view of the goal while the ball is heading for it. Expected: NEEDS_REVIEW (this shows the AI being honest).

**Tips:** keep the ball moving at walking/jogging pace, avoid white shirts and grey ground, don't let two same-colour players overlap for long, one person dribbles the ball for a few seconds (possession and MVP are measured from this).

## 2. Falaj Flow (team game) - judging clip + video clip 13
**Kit:** print `falaj-board.html` and `falaj-tiles.html` from the app (Prepare → Falaj Flow → Printables) at **100% scale** (no "fit to page"), on matte paper (glossy causes glare). Cut out the 16 tiles. Tape the board flat.

**Camera:** **directly above** the board (phone on a stand or books, about 50-70 cm for A4/A3), board centred, **all four corner markers visible and sharp**, no shadows from the phone or your arms, no glare.

**Record 2-3 takes (up to 90 s):**
- **Take A, full route:** start with an empty board; teams place tiles until the well connects to all three farms; **hold the final board still for 3 s, hands out**. Expected: 3 farms, 0 leaks, speed bonus.
- **Take B, mistakes:** leave a gap, or point a channel at the rock. Expected: leaks counted.
- Tiles may be turned in 90° steps; keep the marker facing up and don't cover it with fingers at the end.

**Tips:** start recording **before** the round and say "start"; tiles must sit inside the grid cells; a tile only counts if it stays still for 1 s.

## 3. Souq Signal (individual game) - judging clip + video clip 17
**Kit:** print `souq-cards.html` (16 cards, 2 per product) at 100%. In Prepare → Souq Signal set the **mission** (e.g. dates, coffee, pottery) and **budget** (e.g. AED 60).

**Camera + microphone:** phone facing the player at eye level, quiet room, light on the face and the cards, mic not covered.

**Record 3 takes (30-60 s):**
- **Take A, correct:** show each requested card **steadily for about 1-2 s**, facing the camera, and say its name clearly ("dates", "coffee", "pottery"). Expected: items +2 and spoken match +1 each.
- **Take B, mismatch:** show one card but say a different product. Expected: audio ≠ video → host review.
- **Take C, budget + duplicate:** pick items over the budget and show one card twice (after a pause). Expected: -2 and no extra points.

**Tips:** Arabic or English both work; one card in view at a time; keep your hand from covering the marker square.

## Judging the clips
1. Live Arena → choose the game → **Upload video** (or Camera + mic) → **Send to AI Referee**.
2. Watch the stages (Uploading → Extracting Evidence → Detecting Events → Applying Rules → Verified Result), then the Replay opens.
3. Check the events. If the AI is unsure it shows **NEEDS_REVIEW**: accept or reject it as the host. Don't force results: honest "needs review" results are good evidence.
4. Football: assign the tracks (A1, A2, ...) to the real players to get the **MVP**.
5. Click **Apply verified result** to send it to the Family Cup.
6. If something fails (ball not found, markers not seen), tell me the game, what you filmed and the Replay screen; I'll tune the settings.

## Screen-recording the app for the video
- Windows: **Win + G** (Xbox Game Bar) or OBS Studio; 1920×1080, 30 fps; browser zoom 100%.
- Record the **real flows** listed in the script PDF (setup, library hover, arena timer, the judging stages, replay click on an event, accept/reject, Evaluation Lab, Family Cup).
- For the "judging stages" shot, upload a clip and record while it runs (about 30-60 s; speed up the waiting part in the editor).

## What to send me
- The 3-6 judged **Replay links or screenshots** and the clip files (or tell me the report IDs). I will update the report, deck and video package with the **real** numbers, and replace the red "synthetic" banners in the animatic.
- Never describe synthetic results as real: the documents keep them separate.
