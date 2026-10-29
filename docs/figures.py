"""Architecture + pipeline diagrams (PIL) used by the report and deck."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
OUT = Path(__file__).parent / "figures"; OUT.mkdir(exist_ok=True)
NAVY, TEAL, GOLD, RED, IVORY, CH = "#12243A", "#167E80", "#C6A36B", "#B92D39", "#F7F3EB", "#26313C"
def F(sz, bold=False): return ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf", sz)
def box(d, xy, text, fill, fg="#fff", sub=None, r=18):
    d.rounded_rectangle(xy, r, fill=fill); x0, y0, x1, y1 = xy
    f = F(26, True); w = d.textlength(text, font=f); cy = (y0 + y1) / 2 - (14 if sub else 0)
    d.text(((x0 + x1 - w) / 2, cy - 16), text, font=f, fill=fg)
    if sub:
        fs = F(19); 
        for i, line in enumerate(sub.split("\n")):
            w2 = d.textlength(line, font=fs); d.text(((x0 + x1 - w2) / 2, cy + 20 + i * 24), line, font=fs, fill=fg)
def arrow(d, a, b, col=GOLD):
    d.line([a, b], fill=col, width=5); import math
    ang = math.atan2(b[1]-a[1], b[0]-a[0]); L = 16
    d.polygon([b, (b[0]-L*math.cos(ang-.4), b[1]-L*math.sin(ang-.4)), (b[0]-L*math.cos(ang+.4), b[1]-L*math.sin(ang+.4))], fill=col)

# 1. pipeline
img = Image.new("RGB", (2000, 330), IVORY); d = ImageDraw.Draw(img)
steps = [("Gameplay", "camera + mic\nor upload", NAVY), ("Media extraction", "FFmpeg decode\nframes + audio", NAVY), ("Detection", "OpenCV tracking\nmarkers, speech", TEAL),
         ("Structured events", "timestamps +\nbounding boxes", TEAL), ("Rule validation", "deterministic\nrule engines", GOLD), ("Evidence report", "SHA-256 +\nHMAC seal", GOLD), ("Host review", "accept / reject\nuncertain calls", RED), ("Verified score", "audit-logged\nscoreboard", NAVY)]
w, g = 208, 32
for i, (t, s, c) in enumerate(steps):
    x = 20 + i * (w + g); box(d, (x, 70, x + w, 260), t, c, "#fff" if c != GOLD else NAVY, s)
    if i < len(steps) - 1: arrow(d, (x + w + 4, 165), (x + w + g - 4, 165))
d.text((20, 15), "AI judging pipeline: every stage leaves evidence", font=F(28, True), fill=NAVY)
img.save(OUT / "pipeline.png")

# 2. architecture
img = Image.new("RGB", (2000, 760), IVORY); d = ImageDraw.Draw(img)
d.text((20, 10), "System architecture", font=F(30, True), fill=NAVY)
box(d, (20, 110, 520, 330), "React + TypeScript (Vercel)", NAVY, sub="8 screens · Tailwind · Three.js orb\nMediaRecorder · Canvas overlays")
box(d, (20, 420, 520, 640), "Host & family", TEAL, sub="camera + microphone\nvideo upload · host review")
box(d, (700, 60, 1300, 700), "FastAPI judge (Render)", TEAL, sub="")
for i, (t, s) in enumerate([("Football CV", "colour tracking · goal zones"), ("Falaj reader", "ArUco board → graph"), ("Souq reader", "cards + speech match")]):
    box(d, (730, 140 + i * 105, 1270, 225 + i * 105), t, NAVY, sub=s, r=12)
box(d, (730, 465, 1270, 550), "Rule engines (pure Python)", GOLD, NAVY, sub="versioned · deterministic", r=12)
box(d, (730, 575, 1270, 665), "Integrity + audit", RED, sub="SHA-256 · HMAC · hash chain", r=12)
box(d, (1480, 110, 1980, 270), "FFmpeg / OpenCV", NAVY, sub="decode · markers · tracking")
box(d, (1480, 330, 1980, 490), "Gemini API (server-side)", GOLD, NAVY, sub="speech transcription ONLY\nnever scores")
box(d, (1480, 550, 1980, 710), "GitHub → Vercel", TEAL, sub="frontend CI/CD\nbackend env secrets")
arrow(d, (520, 220), (700, 220)); arrow(d, (700, 280), (520, 280), TEAL); arrow(d, (270, 420), (270, 340)); arrow(d, (1300, 190), (1480, 190)); arrow(d, (1300, 410), (1480, 410)); arrow(d, (1300, 630), (1480, 630))
img.save(OUT / "architecture.png")
print("figures ok")
