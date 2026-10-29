"""Generate print-ready HTML (Save as PDF) for Falaj Flow and Souq Signal. Markers are the exact ArUco
patterns the AI reads (DICT_4X4_100), embedded as crisp SVG so they print at any size."""
from __future__ import annotations

import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app.rules import falaj as F, souq as S  # noqa: E402

OUT = ROOT / "frontend" / "public" / "printables"
OUT.mkdir(parents=True, exist_ok=True)
D = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)


def marker_svg(mid: int, size: str = "100%") -> str:
    img = cv2.aruco.generateImageMarker(D, mid, 6)  # 6x6 modules incl. border
    rects = "".join(f'<rect x="{x}" y="{y}" width="1" height="1"/>' for y in range(6) for x in range(6) if img[y, x] == 0)
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 8 8" width="{size}" height="{size}" shape-rendering="crispEdges"><rect x="-1" y="-1" width="8" height="8" fill="#fff"/><g fill="#000">{rects}</g></svg>'


CSS = """
@page { size: A4 landscape; margin: 10mm; }
*{box-sizing:border-box} body{font-family:Inter,Arial,sans-serif;color:#12243A;margin:0;background:#fff}
.bar{padding:12px 16px;background:#12243A;color:#F7F3EB;display:flex;gap:12px;align-items:center;justify-content:space-between}
.bar button{background:#C6A36B;border:0;border-radius:999px;padding:8px 18px;font-weight:700;cursor:pointer}
.page{padding:8mm} h1{font-family:Georgia,serif;margin:0 0 4px} p{margin:2px 0 8px;font-size:12px}
@media print{.bar{display:none}}
"""


def page(title: str, body: str, note: str) -> str:
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{title} · WASL Arena</title><meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head>
<body><div class="bar"><span><b>WASL Arena</b> · {title}</span><button onclick="window.print()">Print / Save as PDF</button></div>
<div class="page"><h1>{title}</h1><p style="color:#167E80;font-weight:700">Team 204 · Code AYUCK · Cycle 3: grades 9-12 · May Ahmed Mourad (G12), Shamsa Faris Almazrouei (G12), Fatima Mohamed Almazrouei (G11)</p><p>{note} Print at <b>100% scale</b> (no “fit to page”). Keep markers clean and flat.</p>{body}</div></body></html>"""


def board() -> str:
    cell = 36  # mm
    pad = 24
    n = 5
    total = n * cell + 2 * pad
    L = F.LAYOUTS["oasis-1"]
    parts = [f'<div style="position:relative;width:{total}mm;height:{total}mm;margin:0 auto;border:1px solid #12243A;background:#F7F3EB">']
    for cid, (px, py) in {0: (-0.6, -0.6), 1: (5.6, -0.6), 2: (5.6, 5.6), 3: (-0.6, 5.6)}.items():
        size = 24
        cx, cy = pad + px * cell, pad + py * cell
        parts.append(f'<div style="position:absolute;left:{cx - size / 2}mm;top:{cy - size / 2}mm;width:{size}mm;height:{size}mm">{marker_svg(cid)}</div>')
    for r in range(n):
        for c in range(n):
            parts.append(f'<div style="position:absolute;left:{pad + c * cell}mm;top:{pad + r * cell}mm;width:{cell}mm;height:{cell}mm;border:0.4mm solid #B9AE95"></div>')

    def disc(r, c, color, label, fg="#fff"):
        x, y = pad + (c + 0.5) * cell, pad + (r + 0.5) * cell
        return (f'<div style="position:absolute;left:{x - 13}mm;top:{y - 13}mm;width:26mm;height:26mm;border-radius:50%;background:{color};color:{fg};'
                f'display:grid;place-items:center;font-weight:800;font-size:11px;text-align:center;line-height:1.1">{label}</div>')
    s = L["source"]["cell"]
    parts.append(disc(s[0], s[1], "#167E80", "WELL<br>بئر"))
    for i, d in enumerate(L["destinations"]):
        parts.append(disc(d[0], d[1], "#C6A36B", f"FARM {i + 1}<br>مزرعة", "#12243A"))
    for r in L["rocks"]:
        parts.append(disc(r[0], r[1], "#6B7280", "ROCK<br>صخرة"))
    parts.append("</div>")
    return "".join(parts)


def tiles() -> str:
    names = {"STRAIGHT": "Straight", "ELBOW": "Elbow", "TEE": "Tee", "CROSS": "Cross"}
    cells = []
    for tid, ttype in sorted(F.TILE_IDS.items()):
        mid = 25
        arms = "".join(
            f'<line x1="{mid}" y1="{mid}" x2="{mid + dx * 25}" y2="{mid + dy * 25}" stroke="#A9885A" stroke-width="12" stroke-linecap="round"/>'
            for s, (dx, dy) in zip(range(4), [(0, -1), (1, 0), (0, 1), (-1, 0)]) if s in F.BASE_OPEN[ttype])
        cells.append(
            f'<div style="width:62mm;height:62mm;border:0.4mm dashed #999;position:relative;margin:2mm;display:inline-block;background:#F1E8D4">'
            f'<svg viewBox="0 0 50 50" style="position:absolute;inset:0;width:100%;height:100%">{arms}</svg>'
            f'<div style="position:absolute;left:19mm;top:19mm;width:24mm;height:24mm">{marker_svg(tid)}</div>'
            f'<span style="position:absolute;left:2mm;top:1mm;font-size:9px;font-weight:700">{names[ttype]} #{tid}</span>'
            f'<span style="position:absolute;right:2mm;bottom:1mm;font-size:8px">marker up = ↑</span></div>')
    return "".join(cells)


def cards() -> str:
    out = []
    for key, info in S.CATALOG.items():
        for mid in info["marker_ids"]:
            out.append(
                f'<div style="width:60mm;height:84mm;border:0.5mm solid #12243A;border-radius:4mm;display:inline-flex;flex-direction:column;align-items:center;justify-content:space-between;margin:2mm;padding:4mm;background:#fff;vertical-align:top">'
                f'<div style="width:44mm;height:44mm">{marker_svg(mid)}</div>'
                f'<div style="text-align:center"><div style="font-family:Georgia,serif;font-size:18px;font-weight:700">{info["en"]}</div>'
                f'<div dir="rtl" style="font-size:20px;font-weight:700;color:#B92D39">{info["ar"]}</div></div>'
                f'<div style="font-weight:800;font-size:16px;background:#C6A36B;border-radius:999px;padding:2px 14px">AED {info["price"]}</div>'
                f'<div style="font-size:8px;color:#666">card #{mid}</div></div>')
    return "".join(out)


(OUT / "falaj-board.html").write_text(page("Falaj Flow — game board", board(), "The AI finds the four corner markers to map the board. Keep all four visible to the camera."), encoding="utf-8")
(OUT / "falaj-tiles.html").write_text(page("Falaj Flow — channel tiles", tiles(), "Cut along the dashed lines. Each tile's marker tells the AI its type; turn the tile (in 90° steps) to rotate the channel."), encoding="utf-8")
(OUT / "souq-cards.html").write_text(page("Souq Signal — product cards", cards(), "Two copies of each product (a second copy lets you test the duplicate rule). Prices are fixed."), encoding="utf-8")
print("wrote", [p.name for p in OUT.iterdir()])
