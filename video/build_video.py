"""24 x 5 s video: production package (markdown/csv/txt) + a DRAFT animatic MP4 built from real app screenshots,
real pipeline evidence frames and scratch text-to-speech narration. Exactly 120 s, 1920x1080, 30 fps."""
import csv
import json
import subprocess
import sys
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.vision import video as V  # noqa: E402

OUT = ROOT / "video"; WORK = OUT / "work"; WORK.mkdir(exist_ok=True)
SHOT, EVD, FIX = ROOT / "docs/screenshots", ROOT / "frontend/public/samples/evidence", ROOT / "fixtures"
TEAM = "Team 204 · Code AYUCK · Cycle 3 (grades 9-12) · May Ahmed Mourad · Shamsa Faris Almazrouei · Fatima Mohamed Almazrouei"


def fixture_frame(name, t, out):
    cap = cv2.VideoCapture(str(FIX / f"{name}.mp4")); cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read(); cap.release()
    cv2.imwrite(str(out), f); return out


fb_frame = fixture_frame("football_goal", 5.0, WORK / "fx_football.png")
fa_frame = fixture_frame("falaj_valid", 12.0, WORK / "fx_falaj.png")
so_frame = fixture_frame("souq_correct", 6.5, WORK / "fx_souq.png")
SYN = "SYNTHETIC TEST FIXTURE: replace with real footage before submission"

# (title, description, ai_prompt, camera, asset_note, asset_path, narration, on_screen, sfx, transition, placeholder_label)
CLIPS = [
 ("Cinematic family-gaming opening", "Golden-hour courtyard in the UAE. A family of four plays football with a bright ball; a child laughs, the ball rolls toward a mini goal.",
  "Cinematic 16:9, golden hour UAE courtyard, family (father, mother, two children) playing mini football with a bright yellow ball, warm light, shallow depth of field, handheld feel, no text, no logos, photorealistic", "Slow push-in from low angle, subtle handheld", "AI-generated B-roll (generate), fallback: Launch screenshot", SHOT / "01-launch.png", "Every family has a game they love.", "", "Warm ambient courtyard, children laughing, soft oud pad rising", "Quick fade through white", None),
 ("The problem of fair game judging", "Same scene freezes. Family points in different directions: 'Goal!' 'No!' Whistle stops. Question mark graphic.",
  "Cinematic 16:9, family mid-argument over a football goal, pausing frame, expressive faces, warm tones, playful not angry, no text", "Static wide, then slow zoom on the argument", "AI-generated B-roll, fallback: text card", SHOT / "03-library.png", "But who decides what really happened?", "Was that a goal?", "Whistle, overlapping voices fade to silence", "Cut on whistle", None),
 ("WASL Arena brand reveal", "Navy background, the reactive orb blooms in teal; WASL Arena wordmark and tagline resolve.",
  "Abstract 16:9 motion graphic, midnight navy #12243A background, glowing teal #167E80 organic orb pulsing with subtle gold #C6A36B ring, elegant serif wordmark 'WASL Arena', premium, minimal", "Slow dolly-in on orb, wordmark fades in", "Real app: launch screen orb (screen capture)", SHOT / "01-launch.png", "Meet WASL Arena: one family, three games, one fair AI referee.", "WASL Arena\nOne family. Three games. One fair AI referee.", "Soft low swell, glass chime on logo", "Match-cut orb to app", None),
 ("Three games, one AI referee", "Three game cards slide in: Football, Falaj, Souq. The orb glows above them.",
  "UI motion 16:9 using supplied screenshot: three game cards animate in with stagger, orb glow overlay, clean editorial typography", "Slow parallax push", "Real app screenshot: Game library", SHOT / "03-library.png", "Football, Falaj Flow and Souq Signal. Team and individual play.", "Football AI · Falaj Flow · Souq Signal", "Three soft card whooshes", "Slide transition left", None),
 ("Actual app landing page", "Screen recording of the Launch page: hero text, orb reacting to pointer, state pills.",
  "Screen capture 16:9 of the WASL Arena landing page, smooth scroll, orb reacting; use real recording", "Static with subtle zoom to orb", "Real screen recording / screenshot: Launch", SHOT / "01-launch.png", "A real app, built for real family game day.", "Working prototype", "UI tick as pills change state", "Zoom-through to setup", None),
 ("Family registration", "Setup wizard: family name, players, teams, match rules.",
  "Screen capture 16:9, family setup wizard filling in names and picking teams", "Static, cursor highlight", "Real app screenshot: Family setup", SHOT / "02-setup.png", "The host registers players, teams and match rules.", "Players · Teams · Rules", "Soft keystrokes, selection clicks", "Wipe up", None),
 ("Three-game library", "Library page; cursor hovers each card revealing AI skills and scoring.",
  "Screen capture 16:9, hover over game cards revealing details", "Pan across the three cards", "Real app screenshot: Game library", SHOT / "03-library.png", "Each game uses a different kind of AI.", "Tracking · Vision + graph · Vision + speech", "Hover blips", "Cross-dissolve", None),
 ("Host console", "Live Arena: camera on, timer counting, turn order, verified scoreboard.",
  "Screen capture 16:9, Live Arena with timer, record button, turn list", "Static with push on timer and record", "Real app screenshot: Live Arena", SHOT / "05-arena.png", "The host runs rounds, timers and turns.", "Record · Upload · Import AI report", "Record beep, timer ticks", "Whip pan", None),
 ("Real football gameplay", "REAL footage required: family mini-match, fixed camera, bright ball, two goals, coloured shirts, a goal is scored.",
  "Not AI-generated: use real recorded footage from the actual demo (fixed high camera, whole pitch visible)", "Fixed camera as the AI sees it", "REAL FOOTAGE (record). Animatic uses a synthetic fixture frame", fb_frame, "Real play, filmed on a fixed camera.", "Real gameplay", "Real ambient audio, cheers", "Cut on the shot", SYN),
 ("Football video analysis", "Upload to the AI Referee: staged sequence Uploading, Extracting Evidence, Detecting Events, Applying Rules.",
  "Screen capture 16:9 of the judging sequence with orb switching to processing", "Static with progress highlight", "Real app: judging sequence (record from Live Arena)", SHOT / "06-replay-football.png", "The AI extracts evidence, detects events and applies the rules.", "Extracting evidence → Detecting events → Applying rules", "Subtle data-stream shimmer", "Match cut to replay", None),
 ("Player and ball tracking", "Replay screen: ball trail and player boxes tracking over the video.",
  "Screen capture 16:9 of replay with overlays", "Slow push on pitch", "Real evidence frame from the pipeline", EVD / "football_goal/goal-2-before.jpg", "It follows the ball and every player.", "Ball + player tracking", "Soft sonar pings", "Slide", SYN),
 ("Goal verification and score", "The goal moment frame; event card turns VERIFIED; score 1-0 and rule FB-1 shown.",
  "Screen capture 16:9: event card verified, score changes, rule text visible", "Push on the event card", "Real evidence frame + replay screen", EVD / "football_goal/goal-2-moment.jpg", "A goal counts only when the ball is seen crossing the line.", "Verified goal · Rule FB-1 · +1", "Confirmation chime", "Flash cut", SYN),
 ("Falaj physical gameplay", "REAL footage required: hands placing printed channel tiles on the printed 5x5 board, timer visible.",
  "Not AI-generated: use real top-down footage of the printed board and tiles", "Top-down fixed camera", "REAL FOOTAGE (record). Animatic uses synthetic fixture frame", fa_frame, "Falaj Flow: build channels to water the farms.", "Falaj Flow · 90 seconds", "Real tile clacks, timer", "Cut on last tile", SYN),
 ("Visual tile recognition", "The AI draws tile types and rotations on the board frame; water path teal.",
  "Screen capture 16:9 of the board with detected tiles and path overlay", "Slow push on board", "Real evidence frame from the pipeline", EVD / "falaj_valid/final-board.jpg", "Printed markers tell the AI each tile and its rotation.", "Tile type + rotation read from video", "Soft scanning sweep", "Dissolve to twin", SYN),
 ("Digital irrigation graph", "Split screen: physical board and digital twin; water animates along validated edges.",
  "Screen capture 16:9 of split-screen replay with water animation", "Static, then focus on twin", "Real app screenshot: Falaj replay", SHOT / "07-replay-falaj.png", "It rebuilds the network and traces the water.", "Digital reconstruction", "Water trickle rising", "Slide", None),
 ("Verified Falaj scoring", "Events list: three farms watered +3 each, speed bonus +2; total 11.",
  "Screen capture 16:9 of events list with points", "Push on events list", "Real app screenshot: Falaj replay", SHOT / "07-replay-falaj.png", "Three farms, zero leaks, a speed bonus: eleven points.", "+3 +3 +3 +2 = 11", "Counting ticks, chime", "Whip pan", None),
 ("Souq physical gameplay", "REAL footage required: player shows product cards to the camera and names them aloud.",
  "Not AI-generated: use real footage facing the player with cards and voice", "Medium close-up at eye level", "REAL FOOTAGE (record). Animatic uses synthetic fixture frame", so_frame, "Souq Signal: show it, say it, stay in budget.", "Souq Signal", "Real voice, soft market ambience", "Cut on card reveal", SYN),
 ("Visual and speech recognition", "Card detected with product label; transcript appears with timestamps.",
  "Screen capture 16:9 of the replay with card overlay and transcript", "Push on transcript", "Real app screenshot: Souq replay", SHOT / "08-replay-souq.png", "It sees the card and hears the player.", "Vision + speech", "Voice-wave blips", "Dissolve", None),
 ("Budget and item verification", "Basket panel: items, prices, spend 55 of 60, remaining 5.",
  "Screen capture 16:9 of the verified basket", "Push on basket", "Real evidence frame + screenshot", EVD / "souq_correct_gemini/requested_item-1.jpg", "Items, prices and budget are checked automatically.", "AED 55 of 60", "Cash-register tick", "Slide", SYN),
 ("Souq results", "Souq scores per player; winner highlighted.",
  "Screen capture 16:9 of Family Cup Souq section", "Static", "Real app screenshot: Family Cup (demo data)", SHOT / "10-cup.png", "Correct items and matching speech earn points.", "Item +2 · Spoken +1 · Over budget −2", "Soft chime", "Cross-dissolve", None),
 ("AI Referee Replay", "Replay: a NEEDS_REVIEW event selected; evidence frames, rule, Accept/Reject.",
  "Screen capture 16:9 of the review panel; cursor clicks Accept; score updates", "Push on evidence panel", "Real app screenshot: Replay (review)", SHOT / "09-replay-review.png", "If the AI is unsure, the host decides.", "NEEDS_REVIEW → host decision", "Soft click, confirmation tone", "Whip pan", None),
 ("Testing and technical evidence", "Evaluation Lab: 46 of 46 tests, 9 of 9 fixtures, honest note about synthetic vs real.",
  "Screen capture 16:9 of the Evaluation Lab", "Slow scroll", "Real app screenshot: Evaluation Lab", SHOT / "11-lab.png", "Forty-six tests pass. Fixtures are synthetic, and we say so.", "46/46 tests · Synthetic ≠ real", "Soft data pulses", "Dissolve", None),
 ("Family Cup leaderboard", "Standings, champion banner, per-game results.",
  "Screen capture 16:9 of the Family Cup", "Static with push on champion", "Real app screenshot: Family Cup (demo data)", SHOT / "10-cup.png", "Results, MVP and standings, all with reasons.", "Family Cup", "Applause swell", "Fade to navy", None),
 ("Cinematic closing statement", "Orb on navy; closing line and team credits.",
  "Abstract 16:9 closing card, orb on navy, serif text", "Slow pull-back", "Real app screenshot: Launch + team credits", SHOT / "01-launch.png", "WASL Arena: a fair referee that shows its evidence.", "WASL Arena\nTeam 204 · Code AYUCK · Cycle 3", "Resolving chord, silence", "End", None),
]
assert len(CLIPS) == 24


def font(sz, bold=False):
    return ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf", sz)


def compose(i, c):
    title, _, _, _, _, path, narr, onscreen, _, _, ph = c
    im = Image.new("RGB", (1920, 1080), (18, 36, 58)); d = ImageDraw.Draw(im)
    src = Image.open(path).convert("RGB"); sw, sh = src.size
    scale = min(1760 / sw, 800 / sh); src = src.resize((int(sw * scale), int(sh * scale)), Image.LANCZOS)
    x = (1920 - src.width) // 2; im.paste(src, (x, 60))
    d.rectangle([0, 900, 1920, 1080], fill=(12, 24, 40))
    lines = onscreen.split("\n") if onscreen else [title]
    y = 915
    for k, ln in enumerate(lines):
        d.text((60, y), ln, font=font(46 if k == 0 else 28, k == 0), fill=(247, 243, 235) if k == 0 else (198, 163, 107)); y += 58 if k == 0 else 34
    d.text((60, 1040), TEAM, font=font(18), fill=(160, 175, 190))
    d.text((1860, 920), f"{i + 1:02d}", font=font(40, True), fill=(198, 163, 107), anchor="ra")
    d.text((60, 14), "DRAFT ANIMATIC · scratch narration (TTS)", font=font(18, True), fill=(198, 163, 107))
    if ph:
        d.rectangle([x, 70, x + src.width, 118], fill=(185, 45, 57)); d.text((x + 16, 78), ph, font=font(26, True), fill="white")
    out = WORK / f"f{i + 1:02d}.png"; im.save(out); return out


def tts(text, wav):
    ps = f"Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.Rate=0; $s.SetOutputToWaveFile('{wav}'); $s.Speak('{text}'); $s.Dispose()"
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True, capture_output=True)


def dur(path):
    import re
    r = subprocess.run([V.FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", r); return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def build_clip(i, c):
    png = compose(i, c); wav = WORK / f"n{i + 1:02d}.wav"; out = WORK / f"c{i + 1:02d}.mp4"
    tts(c[6].replace("'", ""), wav); d = dur(wav); af = "apad=whole_dur=5"
    if d > 4.6: af = f"atempo={min(1.7, d / 4.6):.3f},apad=whole_dur=5"
    zoom = "zoompan=z='min(zoom+0.0006,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1920x1080:fps=30"
    fade = "fade=t=in:st=0:d=0.3,fade=t=out:st=4.7:d=0.3"
    subprocess.run([V.FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-loop", "1", "-i", str(png), "-i", str(wav), "-vf", f"{zoom},{fade},format=yuv420p",
                    "-af", af, "-t", "5", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-r", "30", str(out)], check=True)
    return out


if __name__ == "__main__":
    clips = [build_clip(i, c) for i, c in enumerate(CLIPS)]
    lst = WORK / "list.txt"; lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in clips), encoding="utf-8")
    final = OUT / "WASL-Arena-draft-animatic-120s.mp4"
    subprocess.run([V.FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(final)], check=True)
    print("final duration", dur(final))

    # ---- production package
    md = ["# WASL Arena: 120-second video production package", "", f"**{TEAM}**", "",
          "24 clips × 5.0 s = **120.0 s**, 16:9, 1920×1080, 30 fps, H.264 MP4. Transitions happen *inside* each clip's 5 s (no added runtime).", "",
          "**Mandatory rules:** use real screenshots/recordings from the finished app; use genuine gameplay for scoring demos; never fabricate functioning UI or AI evidence. Clips 09, 13 and 17 need **real footage**: the draft animatic marks them with a red SYNTHETIC FIXTURE banner.", "",
          "A draft animatic (`WASL-Arena-draft-animatic-120s.mp4`) built from real screenshots, real pipeline evidence frames and scratch text-to-speech narration is included to check pacing. Replace scratch narration with the final voice-over.", ""]
    for i, c in enumerate(CLIPS):
        t0 = i * 5
        md += [f"## Clip {i + 1:02d}: {c[0]}  ({t0 // 60}:{t0 % 60:02d}–{(t0 + 5) // 60}:{(t0 + 5) % 60:02d})", "",
               f"- **Scene (exactly 5 s):** {c[1]}", f"- **AI video prompt:** {c[2]}", f"- **Camera:** {c[3]}", f"- **Source asset:** {c[4]}",
               f"- **Narration:** “{c[6]}”", f"- **On-screen text:** {c[7].replace(chr(10), ' / ') or '(none)'}", f"- **Sound / music:** {c[8]}", f"- **Transition to next:** {c[9]}", ""]
    md += ["## Style guide", "- Palette: midnight navy #12243A, ivory #F7F3EB, heritage teal #167E80, Emirates red #B92D39, muted gold #C6A36B.", "- Type: Fraunces (display), Inter (UI text). Pacing reference: product-focused launch videos with interface-led motion and clean transitions (original film, nothing copied).",
           "- Music: warm, restrained, one rising swell to the reveal (clip 03) and a resolving chord at the end; keep under narration; royalty-free or original only.", "",
           "## Export settings", "MP4 (H.264 High, yuv420p), 1920×1080, 30 fps constant, 12–16 Mbps, AAC 192 kbps 48 kHz stereo, loudness −14 LUFS, duration ≤ 120.0 s, captions burned in or SRT supplied.", ""]
    (OUT / "WASL-Arena-Video-Production-Package.md").write_text("\n".join(md), encoding="utf-8")
    with open(OUT / "editing-timeline.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["clip", "start_s", "end_s", "title", "asset", "narration", "on_screen", "transition"])
        for i, c in enumerate(CLIPS): w.writerow([f"{i + 1:02d}", i * 5, i * 5 + 5, c[0], c[4], c[6], c[7].replace("\n", " / "), c[9]])
    (OUT / "narration-transcript.txt").write_text("\n".join(f"[{i * 5:3d}s] {c[6]}" for i, c in enumerate(CLIPS)), encoding="utf-8")
    chk = ["# Asset checklist", "", "- [ ] Real football footage (fixed camera, goal scored): clip 09", "- [ ] Real Falaj footage (top-down, board + tiles): clip 13", "- [ ] Real Souq footage (cards + voice): clip 17",
           "- [ ] Screen recording of the judging sequence (Uploading → Verified result) from a real upload: clip 10", "- [ ] AI-generated B-roll for clips 01–02 (or filmed family footage with consent)",
           "- [ ] Final voice-over (replace scratch TTS)", "- [ ] Music licence / original track", "- [x] Real app screenshots: launch, setup, library, prepare, arena, replay ×4, cup, lab (docs/screenshots)",
           "- [x] Real pipeline evidence frames (frontend/public/samples/evidence)", "- [x] Team credits end card (Team 204 · Code AYUCK · Cycle 3)", "", "Everyone filmed must consent."]
    (OUT / "asset-checklist.md").write_text("\n".join(chk), encoding="utf-8")
    print("package written")
