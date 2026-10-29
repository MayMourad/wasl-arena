"""Record a REAL walkthrough of the live WASL Arena site (Chrome via Playwright) and capture full-page screenshots.
Includes a live upload judged by the production backend (a clearly named synthetic fixture).
usage: python tools/record_tour.py [BASE_URL]
Outputs: docs/tour/website-tour.mp4, docs/tour/website-tour.gif, docs/fullpage/*.png"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = sys.argv[1] if len(sys.argv) > 1 else "https://frontend-three-fawn-47.vercel.app"
RAW = ROOT / "docs" / "tour" / "_raw"; OUT = ROOT / "docs" / "tour"; FULL = ROOT / "docs" / "fullpage"
for d in (RAW, OUT, FULL): d.mkdir(parents=True, exist_ok=True)
FF = subprocess.check_output([sys.executable, "-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"], text=True).strip()
CURSOR_JS = """
(() => { const c = document.createElement('div'); c.id='__cur';
 c.style.cssText='position:fixed;z-index:99999;width:22px;height:22px;border-radius:50%;background:rgba(198,163,107,.55);border:2px solid #C6A36B;pointer-events:none;left:-40px;top:-40px;transform:translate(-50%,-50%);transition:transform .08s';
 document.addEventListener('DOMContentLoaded',()=>document.body.appendChild(c));
 addEventListener('mousemove',e=>{c.style.left=e.clientX+'px';c.style.top=e.clientY+'px'});
 addEventListener('mousedown',()=>c.style.transform='translate(-50%,-50%) scale(.6)'); addEventListener('mouseup',()=>c.style.transform='translate(-50%,-50%)'); })();
"""
marks = {}
t0 = time.time()
def mark(name): marks[name] = round(time.time() - t0, 2); print(f"[{marks[name]:6.1f}s] {name}")


def glide(page, x, y, steps=22): page.mouse.move(x, y, steps=steps)
def click(page, locator, wait=0.5):
    box = locator.first.bounding_box()
    if box: glide(page, box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    locator.first.click(); page.wait_for_timeout(int(wait * 1000))
def smooth(page, y, ms=1400):
    page.evaluate("""([y, ms]) => new Promise(res => { const s = scrollY, d = y - s, t0 = performance.now();
      const f = t => { const p = Math.min(1, (t - t0) / ms), e = p < .5 ? 2*p*p : 1 - Math.pow(-2*p + 2, 2)/2; scrollTo(0, s + d*e); p < 1 ? requestAnimationFrame(f) : res(); }; requestAnimationFrame(f); })""", [y, ms])
    page.wait_for_timeout(250)
def scroll_through(page, stops, ms=1500, hold=0.6):
    for y in stops: smooth(page, y, ms); page.wait_for_timeout(int(hold * 1000))
def height(page): return page.evaluate("document.documentElement.scrollHeight")
def full(page, name):
    page.evaluate("scrollTo(0,0)"); page.wait_for_timeout(700)
    page.screenshot(path=str(FULL / f"{name}.png"), full_page=True)


with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True, args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required"])
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=str(RAW), record_video_size={"width": 1440, "height": 900})
    ctx.add_init_script(CURSOR_JS)
    page = ctx.new_page(); errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    t0 = time.time()

    # 1 LAUNCH
    mark("launch"); page.goto(BASE + "/", wait_until="networkidle"); page.wait_for_timeout(2500)
    for label in ["Watching play", "Processing evidence", "Evidence verified", "Review required", "Idle"]:
        click(page, page.get_by_role("button", name=label, exact=True), 1.3)
    full(page, "01-launch")
    h = height(page); scroll_through(page, [h * 0.28, h * 0.55, h * 0.82, h], 1700, 0.7); smooth(page, 0, 1400)
    click(page, page.get_by_role("link", name="Start Family Game Day"), 1.0)

    # 2 SETUP
    mark("setup"); page.wait_for_url("**/setup"); page.wait_for_timeout(900)
    click(page, page.locator("#fam"), 0.2); page.keyboard.type("Al Mansoori Family", delay=55); page.wait_for_timeout(500)
    click(page, page.get_by_role("button", name="Continue"), 0.8)
    for i, n in enumerate(["Sara", "Omar", "Mariam", "Khalid"], 1):
        click(page, page.get_by_label(f"Player {i} name"), 0.1); page.keyboard.type(n, delay=60)
    page.wait_for_timeout(500); full(page, "02-setup-players"); click(page, page.get_by_role("button", name="Continue"), 1.0)
    click(page, page.locator("button[aria-label='purple']").nth(1), 0.8); page.wait_for_timeout(500); full(page, "02-setup-teams")
    click(page, page.get_by_role("button", name="Continue"), 1.0)
    click(page, page.locator("input#rounds"), 0.3); page.wait_for_timeout(600)
    full(page, "02-setup-match"); click(page, page.get_by_role("button", name="Save & choose a game"), 1.2)

    # 3 LIBRARY
    mark("library"); page.wait_for_url("**/games"); page.wait_for_timeout(900)
    for art in page.locator("article").all(): glide(page, art.bounding_box()["x"] + 150, art.bounding_box()["y"] + 120); page.wait_for_timeout(700)
    full(page, "03-library"); click(page, page.get_by_role("button", name="Play Football AI →"), 1.0)

    # 4 PREPARE
    mark("prepare"); page.wait_for_url("**/prepare"); page.wait_for_timeout(900); full(page, "04-prepare-football")
    scroll_through(page, [400, 800], 1400, 0.6); smooth(page, 0, 900)
    click(page, page.get_by_role("button", name="Falaj Flow", exact=True), 1.4); full(page, "04-prepare-falaj")
    click(page, page.get_by_role("button", name="Souq Signal", exact=True), 1.4); full(page, "04-prepare-souq")
    click(page, page.get_by_role("button", name="Football AI", exact=True), 0.8)
    for cb in page.locator("input[type=checkbox]").all(): click(page, cb, 0.25)
    click(page, page.get_by_role("button", name="Everyone ready → Live Arena"), 1.0)

    # 5 ARENA + LIVE JUDGING (synthetic fixture, named as such)
    mark("arena"); page.wait_for_url("**/arena"); page.wait_for_timeout(900); full(page, "05-arena")
    click(page, page.get_by_role("button", name="▶ Start match"), 2.5)
    fx = ROOT / "fixtures" / "football_uncertain.mp4"
    page.locator("input[type=file][accept='video/*']").set_input_files({"name": "SYNTHETIC-football-uncertain.mp4", "mimeType": "video/mp4", "buffer": fx.read_bytes()})
    page.wait_for_timeout(1200); full(page, "05-arena-clip-ready")
    click(page, page.get_by_role("button", name="Send to AI Referee →"), 0.5)
    mark("judging_start"); page.wait_for_timeout(2500); page.screenshot(path=str(FULL / "05-judging-stages.png"))
    page.wait_for_url("**/replay**", timeout=180000); mark("judging_end"); page.wait_for_timeout(2500)

    # 6 REPLAY (live report): review a NEEDS_REVIEW call
    mark("replay"); page.wait_for_selector("text=Why the AI decided this", timeout=30000); full(page, "06-replay-needs-review")
    page.evaluate("scrollTo(0, 0)")
    page.locator("video").first.evaluate("v => { v.muted = true; v.play(); }"); page.wait_for_timeout(3500)
    click(page, page.get_by_role("button", name="Accept", exact=True), 2.2); full(page, "06-replay-accepted")
    smooth(page, 700, 1600); page.wait_for_timeout(900); smooth(page, 0, 1200)
    click(page, page.get_by_role("button", name=lambda n: n.startswith("Apply")) if False else page.locator("button:has-text('Apply')").first, 1.5)

    # 7 CUP
    mark("cup"); page.wait_for_url("**/cup"); page.wait_for_timeout(1500); full(page, "07-cup-live-result")
    # 8 sample replays: Falaj twin and Souq transcript
    mark("falaj"); page.goto(BASE + "/replay?report=sample-falaj_valid", wait_until="networkidle"); page.wait_for_timeout(1500)
    page.locator("video").first.evaluate("v => { v.muted = true; v.currentTime = 1; v.play(); }"); page.wait_for_timeout(9000); full(page, "08-replay-falaj")
    scroll_through(page, [650], 1500, 1.0); smooth(page, 0, 900)
    mark("souq"); page.goto(BASE + "/replay?report=sample-souq_correct_gemini", wait_until="networkidle"); page.wait_for_timeout(2000); full(page, "09-replay-souq")
    scroll_through(page, [600], 1500, 1.2); smooth(page, 0, 900)
    mark("football"); page.goto(BASE + "/replay?report=sample-football_goal", wait_until="networkidle"); page.wait_for_timeout(2500); full(page, "10-replay-football")
    scroll_through(page, [600], 1500, 1.2)
    mark("lab"); page.goto(BASE + "/lab", wait_until="networkidle"); page.wait_for_timeout(1500); full(page, "11-lab")
    h = height(page); scroll_through(page, [h * 0.3, h * 0.6, h], 1800, 0.8)
    mark("home_again"); page.goto(BASE + "/", wait_until="networkidle"); page.wait_for_timeout(1800)
    video_path = page.video.path()
    ctx.close(); b.close()

print("console errors:", errors[:5] if errors else "none")
raw = Path(video_path)
j0, j1 = marks["judging_start"] + 2.0, marks["judging_end"] - 0.5
speed = 6
filt = (f"[0:v]trim=0:{j0},setpts=PTS-STARTPTS[a];[0:v]trim={j0}:{j1},setpts=(PTS-STARTPTS)/{speed}[b];[0:v]trim={j1},setpts=PTS-STARTPTS[c];[a][b][c]concat=n=3:v=1:a=0,fps=30,format=yuv420p[v]")
mp4 = OUT / "website-tour.mp4"
subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw), "-filter_complex", filt, "-map", "[v]", "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-movflags", "+faststart", str(mp4)], check=True)
gif = OUT / "website-tour.gif"
subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error", "-t", "34", "-i", str(mp4), "-vf", "fps=8,scale=860:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96[p];[s1][p]paletteuse=dither=bayer:bayer_scale=4", str(gif)], check=True)
shutil.rmtree(RAW, ignore_errors=True)
print("mp4", mp4.stat().st_size // 1024, "KB; gif", gif.stat().st_size // 1024, "KB; marks", marks)
