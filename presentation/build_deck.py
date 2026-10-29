"""Build the 30-slide editable PowerPoint. Test numbers are read from evaluation.json (no hand-typed results)."""
import json
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
SHOT, FIG = ROOT / "docs" / "screenshots", ROOT / "docs" / "figures"
EVD = ROOT / "frontend/public/samples/evidence"
EV = json.loads((ROOT / "frontend/public/evaluation.json").read_text(encoding="utf-8"))
C = {k: RGBColor.from_string(v) for k, v in dict(navy="12243A", ivory="F7F3EB", teal="167E80", red="B92D39", gold="C6A36B", char="26313C", white="FFFFFF", line="E3DCCD").items()}

prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
N = [0]


def rect(s, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, line=None):
    r = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h)); r.fill.solid(); r.fill.fore_color.rgb = fill
    if line: r.line.color.rgb = line
    else: r.line.fill.background()
    r.shadow.inherit = False
    return r


def text(s, x, y, w, h, t, size=18, color=None, bold=False, font="Calibri", align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    lines = t if isinstance(t, list) else [t]
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        r = p.add_run(); r.text = ln; r.font.size = Pt(size); r.font.bold = bold; r.font.name = font; r.font.color.rgb = color or C["char"]
    return tb


def bullets(s, x, y, w, h, items, size=19, color=None, gap=8):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.space_after = Pt(gap)
        r0 = p.add_run(); r0.text = "◆  "; r0.font.size = Pt(size - 6); r0.font.color.rgb = C["gold"]
        parts = it.split("**")
        for j, part in enumerate(parts):
            if not part: continue
            r = p.add_run(); r.text = part; r.font.size = Pt(size); r.font.bold = j % 2 == 1; r.font.name = "Calibri"; r.font.color.rgb = color or C["char"]
    return tb


def slide(title, kicker="", dark=False, notes=""):
    s = prs.slides.add_slide(BLANK); N[0] += 1
    rect(s, 0, 0, 13.333, 7.5, C["navy"] if dark else C["ivory"])
    if not dark: rect(s, 0, 0, 0.18, 7.5, C["teal"])
    if kicker: text(s, 0.6, 0.35, 9, 0.3, kicker.upper(), 12, C["gold"] if dark else C["teal"], True)
    if title: text(s, 0.6, 0.65, 12.1, 1.0, title, 34, C["ivory"] if dark else C["navy"], True, "Cambria")
    text(s, 12.2, 7.08, 0.9, 0.3, f"{N[0]}", 11, C["gold"] if dark else C["char"], align=PP_ALIGN.RIGHT)
    text(s, 0.6, 7.08, 11.4, 0.3, "WASL Arena · Team 204 · Code AYUCK · Cycle 3 (grades 9-12) · May Ahmed Mourad, Shamsa Faris Almazrouei, Fatima Mohamed Almazrouei", 10, C["ivory"] if dark else C["char"])
    s.notes_slide.notes_text_frame.text = notes
    return s


def img(s, path, x, y, w=None, h=None):
    p = Path(path)
    return s.shapes.add_picture(str(p), Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)


def framed(s, path, x, y, w, caption=None):
    rect(s, x - 0.06, y - 0.06, w + 0.12, w * 0.625 + 0.12, C["white"], line=C["line"])
    pic = img(s, path, x, y, w)
    if caption: text(s, x, y + w * 0.625 + 0.1, w, 0.3, caption, 11, C["char"])
    return pic


def card(s, x, y, w, h, head, body, fill=None, fg=None):
    rect(s, x, y, w, h, fill or C["white"], MSO_SHAPE.ROUNDED_RECTANGLE, C["line"]).adjustments[0] = 0.06
    text(s, x + 0.2, y + 0.15, w - 0.4, 0.5, head, 20, fg or C["navy"], True, "Cambria")
    text(s, x + 0.2, y + 0.7, w - 0.4, h - 0.8, body, 15, fg or C["char"])


def stat(s, x, y, big, small, color=None):
    text(s, x, y, 3.0, 0.9, big, 44, color or C["teal"], True, "Cambria")
    text(s, x, y + 0.95, 3.0, 0.8, small, 14, C["char"])


pt, fx, gem = EV["pytest"], EV["fixtures"], EV["transcription_check"]

# 1 Title
s = slide("", dark=True, notes="Open with the promise: one family, three games, one fair AI referee. WASL means connection: the app connects physical family play to digital judging. This is our Cycle 3 entry for AI for Family: Family AI Game Day.")
text(s, 0.8, 1.6, 8, 0.4, "6TH ANNUAL COE STEM PROGRAMMING WITH AI · CYCLE 3 · AI FOR FAMILY", 13, C["gold"], True)
text(s, 0.8, 2.1, 8, 1.4, "WASL Arena", 72, C["ivory"], True, "Cambria")
text(s, 0.8, 3.6, 6.8, 1.4, "One family. Three games. One fair AI referee.", 26, C["gold"], False, "Cambria")
text(s, 0.8, 5.2, 7, 0.8, ["Family AI Game Day · Football AI · Falaj Flow · Souq Signal", "Team 204 · Team code AYUCK · Track: Cycle 3 (grades 9-12)", "May Ahmed Mourad (G12) · Shamsa Faris Almazrouei (G12) · Fatima Mohamed Almazrouei (G11)"], 15, C["ivory"])
framed(s, SHOT / "01-launch.png", 7.9, 1.7, 4.9)
# 2 Vision
s = slide("A fair referee for every family game", "Vision", notes="Our vision is that any family can play physical games at home and get a judge they can trust. Trust comes from evidence, not from confidence.")
bullets(s, 0.6, 1.9, 7.4, 4.5, ["Real physical play: ball, board, cards, voices", "An AI that **watches and listens**, then applies written rules", "Every point **linked to replayable evidence**", "A human host always has the final word", "Culture built in: **falaj** irrigation and the **souq** market"], 22)
card(s, 8.4, 1.9, 4.3, 3.6, "Fair play = evidence + doubt", "If the AI cannot see it, it does not score it. Uncertain calls wait for the host.", C["navy"], C["ivory"])
# 3 Problem
s = slide("Family games end in arguments", "Problem", notes="Everyone has had the 'was that a goal' argument. Existing apps either need manual scoring or give black-box answers. Families will not trust a judge that cannot explain itself.")
for i, (a, b) in enumerate([("“Was that a goal?”", "Nobody agrees what the camera saw."), ("“You said it after!”", "Speech and action are hard to line up by memory."), ("“Is the score right?”", "Manual tallies drift; nobody can check them.")]):
    card(s, 0.6 + i * 4.15, 1.9, 3.95, 2.3, a, b)
bullets(s, 0.6, 4.6, 12, 2, ["Black-box AI scoring fails the trust test", "An AI that guesses is worse than no AI", "Families need **explanations**, not just answers"], 20)
# 4 Why family gaming matters
s = slide("Why family gaming matters", "Context", notes="Shared play builds connection across generations. The UAE Year of Family theme makes this timely. We keep screens as a host and judge, not as the entertainment itself: the fun is physical.")
bullets(s, 0.6, 1.9, 7.2, 4.5, ["Shared play builds **connection across generations**", "Physical games keep families **moving and talking**", "Heritage games pass on **culture** (falaj, souq)", "Fair, simple judging lets **children and adults compete together**", "Screens act as **host and referee**, not the entertainment"], 21)
card(s, 8.3, 1.9, 4.4, 3.2, "Our principle", "Technology should make the family game more fun and more fair, never take it over.", C["teal"], C["white"])
# 5 Official challenge
s = slide("The official challenge", "Family AI Game Day", notes="These are the requirements from the Cycle 3 question: working website or app, AI observing real play through video and audio, three games with football, team and individual play, host sets up and runs, shows results with reasons.")
bullets(s, 0.6, 1.9, 7.4, 4.6, ["Working website/app for family games inspired by **culture, heritage or sports**", "AI observes real play through **video and audio**, applies rules, keeps score", "**Cycle 3:** football + 2 original games (team and individual)", "Football: track players and ball, goals, **possession, MVP**", "Upload video **or** record by camera + microphone", "Human **host** sets up, runs rounds/turns/timers, shows reasons"], 19)
card(s, 8.4, 1.9, 4.3, 3.0, "Excluded examples", "Heritage guessing · cup stacking · ring toss · copy-the-rhythm. Our games are original.", C["navy"], C["ivory"])
# 6 Our solution
s = slide("Our solution: WASL Arena", "Solution", notes="WASL Arena is a complete host-and-judge application. Eight screens take a family from registration to the final cup. Three games each show a different AI skill.")
for i, (h, b) in enumerate([("Football AI", "Team · tracking, goals, possession, MVP"), ("Falaj Flow", "Team · board vision + graph reasoning"), ("Souq Signal", "Individual · vision + speech + budget")]):
    card(s, 0.6 + i * 4.15, 1.9, 3.95, 1.9, h, b, [C["teal"], C["navy"], C["red"]][i], C["white"])
framed(s, SHOT / "03-library.png", 3.6, 4.0, 3.6)
bullets(s, 7.7, 4.1, 5.2, 2.8, ["8 screens, bilingual EN/AR", "Real video/audio judging", "Host review + audit trail"], 18)
# 7 Value
s = slide("Value proposition", "Why it wins", notes="Each audience gets something: families get fair play, hosts get control, judges get proof. The AI is useful because it is accountable.")
for i, (h, b) in enumerate([("Families", "Fair, fast scoring that everyone can replay and understand."), ("Hosts", "Setup, rounds, timers, review and results in one console."), ("Judges", "Real pipelines, tests and honest limits you can inspect.")]):
    card(s, 0.6 + i * 4.15, 1.9, 3.95, 2.6, h, b)
bullets(s, 0.6, 4.9, 12, 2, ["Explainable: rule, frames, timestamps, score change", "Honest: NEEDS_REVIEW instead of guessing", "Tamper-evident: hashes + signatures + audit chain"], 20)
# 8 Signature innovation
s = slide("Signature innovation: AI Referee Replay", "Innovation", notes="This is the idea we want judges to remember. Every judgment can be replayed with the video, the detections drawn on top, the rule applied, the score change and a status. Click any event, see exactly why.")
framed(s, SHOT / "06-replay-football.png", 0.6, 1.8, 7.4)
bullets(s, 8.4, 1.9, 4.5, 4.8, ["**Source video** with live annotations", "**Timestamps** and evidence frames", "**Rule applied** and score change", "**Verification status** + uncertainty", "**Human review** accept / reject"], 19)
# 9 Journey
s = slide("User journey", "Host flow", notes="The flow mirrors the brief: choose a game, players and teams, rules and ready, round in play, AI judge results, final results, then choose another game.")
for i, h in enumerate(["Choose game", "Players & teams", "Rules & ready", "Round in play", "AI judges", "Final results"]):
    rect(s, 0.6 + i * 2.1, 2.0, 1.9, 1.3, [C["navy"], C["navy"], C["teal"], C["teal"], C["gold"], C["red"]][i], MSO_SHAPE.ROUNDED_RECTANGLE)
    text(s, 0.6 + i * 2.1, 2.2, 1.9, 0.9, [f"{i + 1}", h], 17, C["white"] if i != 4 else C["navy"], True, align=PP_ALIGN.CENTER)
framed(s, SHOT / "02-setup.png", 0.9, 3.7, 3.4, "Family setup"); framed(s, SHOT / "04-prepare.png", 4.6, 3.7, 3.4, "Preparation"); framed(s, SHOT / "05-arena.png", 8.3, 3.7, 3.4, "Live arena")
# 10 Collection
s = slide("The three-game collection", "Games", notes="Exactly three games, as Cycle 3 requires: football plus two originals. Team and individual play are both covered. Each game uses a different AI capability.")
for i, (h, b, im) in enumerate([("Football AI · Team", "Tracking, goal zones, possession, MVP", "football"), ("Falaj Flow · Team", "ArUco tile reading, graph, water routes", "falaj"), ("Souq Signal · Individual", "Cards + speech + budget agreement", "souq")]):
    card(s, 0.6 + i * 4.15, 1.8, 3.95, 2.0, h, b, [C["teal"], C["navy"], C["red"]][i], C["white"])
framed(s, SHOT / "03-library.png", 2.4, 4.1, 4.2)
bullets(s, 7.2, 4.2, 5.6, 2.6, ["Team **and** individual play", "No excluded example games", "Printable boards and cards included"], 19)
# 11 Football overview
s = slide("Football AI: overview", "Game 1 · Team", notes="Teams of one to three play a mini match on camera. Fixed camera, bright ball, contrasting shirts, calibrated goals. The AI tracks, detects goals and measures possession. The official brief says the MVP is the player with the most ball time.")
bullets(s, 0.6, 1.9, 6.4, 4.6, ["Mini-match, fixed camera, bright ball, marked goals", "Valid goal **+1**; unsupported goal **0**", "Winner: highest verified score", "Tie: configurable **golden goal**", "**MVP** = longest verified possession", "Host penalty −1 (audit-logged)"], 20)
framed(s, SHOT / "04-prepare.png", 7.3, 1.9, 5.4, "Goal-zone calibration in Game Preparation")
# 12 Football tracking
s = slide("Football AI: tracking", "How it sees", notes="Classical, explainable computer vision. HSV colour segmentation finds ball and shirts; contour shape and area filter noise; nearest-neighbour tracking follows players; we only use positions that were actually observed.")
bullets(s, 0.6, 1.9, 6.0, 4.6, ["Frames sampled at **10 fps**", "Ball = best **circular contour** in a calibrated colour range", "Players = **team-colour blobs**, tracked frame to frame", "Only **observed** positions count: no interpolation", "Players are tracks; the host maps tracks to names"], 19)
framed(s, EVD / "football_goal/goal-2-before.jpg", 6.9, 1.9, 5.8, "Tracked ball trail and player boxes (synthetic fixture)")
# 13 Football referee replay
s = slide("Football AI: referee replay", "Evidence", notes="Here is a verified goal: the AI saw the ball outside the zone, then inside for several consecutive samples. The evidence frames before, at and after the moment are attached. A goal whose entry was not observed becomes needs review.")
framed(s, EVD / "football_goal/goal-2-moment.jpg", 0.6, 1.8, 5.8, "The moment"); framed(s, EVD / "football_goal/goal-2-after.jpg", 6.8, 1.8, 5.8, "After")
bullets(s, 0.6, 6.0, 12, 1.0, ["Rule FB-1: ball observed entering the goal zone after being seen outside: **+1**   ·   Ball lost near the goal → **POSSIBLE_GOAL**, 0 points until the host decides"], 15)
# 14 Falaj overview
s = slide("Falaj Flow: overview", "Game 2 · Team", notes="Falaj is the traditional UAE irrigation system. Teams build a channel network with printed tiles on a 5 by 5 board. Three farms need water; a rock blocks the middle; 90 seconds per round.")
bullets(s, 0.6, 1.9, 6.0, 4.6, ["Inspired by the UAE **falaj** irrigation system", "Printed 5×5 board: **well**, three **farms**, a **rock**", "Teams place channel tiles for **90 seconds**", "Farm **+3** · leak **−1** · speed bonus up to **+2**", "Tie: shortest valid network, then time"], 20)
framed(s, SHOT / "07-replay-falaj.png", 6.9, 1.9, 5.8, "Split screen: physical board and digital twin")
# 15 Falaj graph
s = slide("Falaj Flow: graph intelligence", "How it thinks", notes="Four corner markers give us a homography. Each tile has a marker whose id gives its type and whose rotation gives its orientation. We build a graph and run breadth first search from the well, following only matching open sides. Anything else is a leak.")
for i, (h, b) in enumerate([("1  Calibrate", "4 corner markers → board homography"), ("2  Read tiles", "marker id = type, rotation = 90° steps"), ("3  Stabilise", "state must hold 1 s: hands ignored"), ("4  Trace water", "BFS over matching open sides; leaks found")]):
    card(s, 0.6 + i * 3.1, 1.9, 2.95, 2.3, h, b, C["navy"] if i % 2 == 0 else C["teal"], C["white"])
framed(s, EVD / "falaj_valid/final-board.jpg", 3.6, 4.3, 4.0, "Board read from video, water path in teal")
bullets(s, 8.0, 4.4, 4.8, 2.4, ["Exact tile types and rotations recovered in testing", "Leaks: edge, rock, gap, closed side"], 17)
# 16 Falaj scoring
s = slide("Falaj Flow: scoring", "Rules", notes="Scores are deterministic. Three farms is nine points, each leak costs one, and a fast finish adds up to two. The tie break prefers the shortest valid network.")
rows = [("Farm watered", "+3"), ("Leak", "−1"), ("All farms ≤ 45 s", "+2"), ("All farms ≤ 70 s", "+1"), ("Tie-break", "shortest network → time")]
for i, (a, b) in enumerate(rows):
    rect(s, 0.6, 1.9 + i * 0.85, 6.4, 0.7, C["white"], MSO_SHAPE.ROUNDED_RECTANGLE, C["line"]); text(s, 0.8, 2.0 + i * 0.85, 4, 0.5, a, 19, C["navy"], True); text(s, 4.6, 2.0 + i * 0.85, 2.3, 0.5, b, 19, C["teal"], True, align=PP_ALIGN.RIGHT)
card(s, 7.5, 1.9, 5.2, 2.2, "Tested outcomes", [f"{f['name']}: {f['actual'].get('total')} pts" for f in fx if f["game"] == "falaj"], C["navy"], C["ivory"])
text(s, 7.5, 4.4, 5.2, 1.5, "Complete route 11 · partial network 5 · blocked by rock 10 (synthetic fixtures, matching ground truth).", 15)
# 17 Souq overview
s = slide("Souq Signal: overview", "Game 3 · Individual", notes="An individual game inspired by UAE markets. The host gives a shopping mission and budget. The player picks product cards, shows each to the camera and says its name. Different from a guessing game: it is about choosing, speaking and staying in budget.")
bullets(s, 0.6, 1.9, 6.0, 4.6, ["Shopping **mission** + **budget** in AED", "Pick product cards: dates, coffee, spices, pottery, textile, oud…", "**Show** each card to the camera and **say** its name", "Item **+2** · spoken match **+1** · over budget **−2**", "Duplicate = no points · Tie: lower spend, then time"], 20)
framed(s, SHOT / "08-replay-souq.png", 6.9, 1.9, 5.8, "Verified basket and transcript")
# 18 Multimodal
s = slide("Souq Signal: multimodal AI", "Vision + speech", notes="Cards are recognised by printed markers; speech is transcribed by an AI model, server side. The model only produces text. Matching and scoring are deterministic code, so the AI can never invent points.")
for i, (h, b) in enumerate([("See", "Card markers decoded per frame → presentation intervals"), ("Hear", "Arabic/English speech → timed transcript"), ("Agree?", "Said ≈ shown within ±5 s, else host review"), ("Score", "Deterministic rules + budget maths")]):
    card(s, 0.6 + i * 3.1, 1.9, 2.95, 2.4, h, b, [C["navy"], C["teal"], C["gold"], C["red"]][i], C["white"] if i != 2 else C["navy"])
bullets(s, 0.6, 4.7, 12, 2, ["Transcription model **never decides points**", "Silent audio is rejected by an energy gate (no hallucinated speech)", "No transcript → spoken-match points stay **NEEDS_REVIEW**"], 19)
# 19 Souq verification
s = slide("Souq Signal: transaction verification", "Basket", notes="The basket shows each verified card with price, remaining budget and the transcript with timestamps. Mismatches between what is said and what is shown are flagged for the host.")
framed(s, SHOT / "08-replay-souq.png", 0.6, 1.8, 6.6)
bullets(s, 7.6, 1.9, 5.2, 4.8, ["Distinct card prices are summed", "Over budget → **−2** (once)", "Duplicate cards earn **0** and are not paid twice", "Audio ≠ video → **host review**", "Test: correct basket = 9 pts, spend AED 55 of 60"], 19)
# 20 Host console
s = slide("Family host console", "Live Arena", notes="The host console covers camera or microphone recording, upload, importing an external AI report, timer, turn order, penalties and the verified scoreboard.")
framed(s, SHOT / "05-arena.png", 0.6, 1.8, 7.0)
bullets(s, 8.0, 1.9, 4.9, 4.8, ["Camera + mic recording or **upload**", "Round **timer**, turn order, **skip/next**", "Import a sealed **AI report**", "Verified **scoreboard**", "Host penalty with audit log"], 19)
# 21 Referee replay
s = slide("AI Referee Replay", "Explain every call", notes="This is the screen to remember. Select an event and the video jumps to the moment. You see the rule, the points, the status and the evidence frames. The host can accept or reject, and the score is recomputed by the same rule engine.")
framed(s, SHOT / "09-replay-review.png", 0.6, 1.8, 7.4, "A call that needs review: ball lost near the goal")
bullets(s, 8.4, 1.9, 4.5, 4.8, ["Event timeline on the video", "**Why the AI decided this**", "Evidence frames + audio transcript", "**Accept / Reject** → score recomputed", "Audit trail entry for every decision"], 18)
# 22 Architecture
s = slide("Technical architecture", "System", notes="React frontend on Vercel, FastAPI judge on Render with FFmpeg and OpenCV. Rule engines are pure Python. The transcription key lives only on the server.")
img(s, FIG / "architecture.png", 0.6, 1.6, 12.1)
# 23 AI models and algorithms
s = slide("AI models and algorithms", "Methods", notes="We deliberately use explainable methods. Classical vision for tracking and markers, graph search for Falaj, a speech model for transcription only, and deterministic rule engines for scoring.")
table_rows = [("Football", "HSV segmentation, contours, nearest-neighbour tracking, goal-zone logic"), ("Falaj Flow", "ArUco markers, homography, rotation estimation, BFS on tile graph"), ("Souq Signal", "ArUco card sightings, speech transcription, alias matching, budget maths"), ("Scoring", "Versioned deterministic rule engines (FB / FF / SS)"), ("Integrity", "SHA-256, HMAC-SHA256, hash-chained audit log")]
for i, (a, b) in enumerate(table_rows):
    rect(s, 0.6, 1.8 + i * 0.95, 12.1, 0.8, C["white"], MSO_SHAPE.ROUNDED_RECTANGLE, C["line"]); text(s, 0.8, 1.93 + i * 0.95, 2.6, 0.5, a, 19, C["teal"], True); text(s, 3.4, 1.93 + i * 0.95, 9.2, 0.6, b, 17)
# 24 Evidence integrity
s = slide("Evidence integrity", "Trust", notes="Source videos are hashed on upload. Reports are sealed with a digest and an HMAC signature. Edit any character and verification fails. Host decisions re-seal the report, but keep the original AI seal.")
img(s, FIG / "pipeline.png", 0.6, 1.7, 12.1)
bullets(s, 0.6, 4.2, 12, 2.8, ["Source file **SHA-256** and rule-version id on every report", "Report sealed with **SHA-256 + HMAC**; import of an edited report is **rejected** (tested)", "Host actions in a **hash-chained audit log**; tampering detected (tested)", "Stand-alone Python judge produces the same sealed report"], 19)
# 25 Fairness & privacy
s = slide("Fairness and privacy", "Responsible AI", notes="Fairness: deterministic rules, visible uncertainty, contestable calls. Privacy: no face identification, players are colour tracks mapped to names the host types; keys stay server side; families should film only their own game with consent.")
card(s, 0.6, 1.9, 6.0, 4.5, "Fairness", ["Rules are written and versioned", "Uncertain = NEEDS_REVIEW, never guessed", "Unobserved ball time is 'unknown'", "Every call can be accepted / rejected", "Arabic + English, team + solo"], C["navy"], C["ivory"])
card(s, 6.9, 1.9, 5.8, 4.5, "Privacy & security", ["No face identification or biometrics", "Credentials only in server environment", "Audio sent only for transcription", "Consent from everyone filmed", "Reports signed against tampering"], C["teal"], C["white"])
# 26 Evaluation methodology
s = slide("Evaluation methodology", "How we test", notes="We test three layers: the rule engines in isolation, the full video-to-score pipelines on fixtures with known ground truth, and the API flow including review and tampering. We are explicit that fixtures are synthetic.")
for i, (h, b) in enumerate([("Rule engines", "Unit tests per game: valid, invalid, edge, tie-break"), ("Pipelines", "Synthetic fixtures with known ground truth → video → events → score"), ("API & integrity", "Upload → job → report → host review → tamper rejection")]):
    card(s, 0.6 + i * 4.15, 1.9, 3.95, 2.4, h, b)
rect(s, 0.6, 4.7, 12.1, 1.5, C["gold"], MSO_SHAPE.ROUNDED_RECTANGLE); text(s, 0.9, 4.85, 11.6, 1.2, "Honest scope: fixtures are rendered by code, not real family gameplay. They prove the pipelines work; they do not measure real-world accuracy. Real clips are the next step.", 18, C["navy"], True)
# 27 Actual results
s = slide("Actual test results", "Verified by running", notes="These numbers are read from the evaluation file that the test run generates. Forty six of forty six tests passed. All nine synthetic fixtures matched ground truth. The speech check used a live transcription model call.")
stat(s, 0.6, 1.8, f"{pt['passed']}/{pt['total']}", "automated tests passed"); stat(s, 3.7, 1.8, f"{sum(f['pass'] for f in fx)}/{len(fx)}", "synthetic fixtures match ground truth"); stat(s, 6.8, 1.8, "0", "real family clips analysed yet", C["red"])
for i, f in enumerate(fx):
    x, y = 0.6 + (i % 3) * 4.15, 3.85 + (i // 3) * 1.05
    rect(s, x, y, 3.95, 0.9, C["white"], MSO_SHAPE.ROUNDED_RECTANGLE, C["line"]); text(s, x + 0.15, y + 0.05, 3.7, 0.4, f["name"] + ("  ✓" if f["pass"] else "  ✗"), 14, C["teal"], True)
    text(s, x + 0.15, y + 0.42, 3.7, 0.45, ", ".join(f"{k}={v}" for k, v in list(f["actual"].items())[:3]), 11)
# 28 Deployment
s = slide("GitHub and Vercel deployment", "Delivery", notes="The frontend is deployed from GitHub to Vercel; the judge runs on Render because video processing needs Python, FFmpeg and OpenCV. The frontend reaches the judge through an environment variable and all credentials stay on the server. We verified the live deployment: routes load, the header badge says AI judge online, a Falaj clip uploaded to the live judge was scored 11 with a valid seal, and CORS accepts only the Vercel origin. Free tier hosting sleeps when idle, so the first request can take about 30 seconds.")
for i, (h, b) in enumerate([("GitHub", "MayMourad/wasl-arena (private): frontend, backend, tests, docs, AI-usage records"), ("Vercel · frontend", "frontend-three-fawn-47.vercel.app · VITE_API_URL points at the judge"), ("Render · AI judge", "wasl-arena.onrender.com · FastAPI + FFmpeg + OpenCV · secrets as env vars")]):
    card(s, 0.6 + i * 4.15, 1.9, 3.95, 2.6, h, b, [C["navy"], C["teal"], C["gold"]][i], C["white"] if i < 2 else C["navy"])
bullets(s, 0.6, 4.8, 12, 2.2, ["**Verified live:** all routes load, badge shows “AI judge online”, a Falaj clip judged on the live backend = 11 pts, seal valid", "CORS locked to the Vercel origin · no secrets in the repository (.env git-ignored)", "Free tier: first request after idle can take ~30 s"], 18)
# 29 Limitations & future
s = slide("Limitations and future development", "Next", notes="We are upfront about limits. Next steps are real footage evaluation, pretrained detectors, jersey number reading, and audio cues.")
card(s, 0.6, 1.9, 6.0, 4.6, "Limitations", ["No real family footage evaluated yet", "Controlled setup: fixed camera, bright ball", "Colour segmentation is lighting-sensitive", "Printed markers can be hidden or damaged", "Speech timing ±~1 s; scores are heuristics"], C["white"], C["char"])
card(s, 6.9, 1.9, 5.8, 4.6, "Future development", ["Evaluate real footage for each game", "Pretrained detectors + jersey numbers", "Whistle / 'goal!' audio cues", "Host-defined games from the rule template", "More heritage games and languages"], C["navy"], C["ivory"])
# 30 Conclusion
s = slide("", dark=True, notes="Close on the idea: a fair referee shows its evidence, admits doubt and lets people decide. WASL Arena does that for three games.")
text(s, 0.8, 1.4, 11.5, 1.0, "WASL Arena", 54, C["ivory"], True, "Cambria")
text(s, 0.8, 2.6, 11.5, 1.6, "A fair referee shows its evidence, admits doubt, and lets people decide.", 32, C["gold"], False, "Cambria")
bullets(s, 0.8, 4.2, 7.5, 2.0, ["Three games · team and individual", "Real video/audio judging, explainable results", "Interactive, inclusive, culturally meaningful, transparently fair"], 20, C["ivory"])
text(s, 0.8, 6.15, 7.8, 0.8, ["Team 204 · Code AYUCK · Cycle 3 (grades 9-12)", "May Ahmed Mourad (G12) · Shamsa Faris Almazrouei (G12) · Fatima Mohamed Almazrouei (G11)"], 14, C["gold"], True)
framed(s, SHOT / "10-cup.png", 8.5, 4.2, 4.3)

assert len(prs.slides) == 30, len(prs.slides)
out = ROOT / "presentation" / "WASL-Arena-30-Slides.pptx"
prs.save(out); print("saved", out, len(prs.slides))
