"""Final 2-minute script (voiceover + image-generation prompts + animation prompts) -> .docx -> PDF via Word."""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_video as bv  # noqa: E402  (CLIPS only; main is guarded)
from script_data import DATA, MUSIC, STYLE, VO_DIRECTION  # noqa: E402

CLIPS = bv.CLIPS
NAVY, TEAL, GOLD, RED = RGBColor(0x12, 0x24, 0x3A), RGBColor(0x16, 0x7E, 0x80), RGBColor(0xC6, 0xA3, 0x6B), RGBColor(0xB9, 0x2D, 0x39)
doc = Document(); sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7); sec.left_margin = sec.right_margin = Cm(1.7); sec.top_margin, sec.bottom_margin = Cm(1.5), Cm(1.3)
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(9.5); st.paragraph_format.space_after = Pt(3)
hp = sec.header.paragraphs[0]; r = hp.add_run("WASL Arena · 2-minute video script · Team 204 · Code AYUCK · Cycle 3 (grades 9-12)"); r.font.size = Pt(8); r.font.color.rgb = TEAL


def shade(cell, hex_):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_); tcPr.append(shd)


def para(text, size=None, bold=False, color=None, italic=False, after=None):
    p = doc.add_paragraph()
    for i, part in enumerate(text.split("**")):
        if not part: continue
        r = p.add_run(part); r.bold = bold or i % 2 == 1; r.italic = italic
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = color
    if after is not None: p.paragraph_format.space_after = Pt(after)
    return p


def h1(text):
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(4); p.paragraph_format.keep_with_next = True
    r = p.add_run(text); r.bold = True; r.font.size = Pt(17); r.font.color.rgb = NAVY; r.font.name = "Cambria"
    pPr = p._p.get_or_add_pPr(); b = OxmlElement("w:pBdr"); bt = OxmlElement("w:bottom")
    for k, v in (("val", "single"), ("sz", "10"), ("space", "2"), ("color", "167E80")): bt.set(qn(f"w:{k}"), v)
    b.append(bt); pPr.append(b)


def table(rows, widths, size=9, head=True):
    t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.width = Cm(widths[j]); c.text = ""; p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(v).replace('**', '')); r.font.size = Pt(size); r.bold = head and i == 0
            if head and i == 0: shade(c, "12243A"); r.font.color.rgb = RGBColor(255, 255, 255)
            elif i % 2 == 0: shade(c, "F7F3EB")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def card(i):
    c = CLIPS[i]; d = DATA[i]; t0 = i * 5
    t = doc.add_table(rows=1, cols=1); cell = t.cell(0, 0); shade(cell, "12243A"); cell.text = ""
    p = cell.paragraphs[0]; p.paragraph_format.space_after = Pt(1)
    r = p.add_run(f"CLIP {i + 1:02d}  ·  {c[0]}"); r.bold = True; r.font.size = Pt(11.5); r.font.color.rgb = RGBColor(0xF7, 0xF3, 0xEB)
    r = p.add_run(f"     {t0 // 60}:{t0 % 60:02d} – {(t0 + 5) // 60}:{(t0 + 5) % 60:02d}  ·  {d['kind']}"); r.font.size = Pt(9); r.font.color.rgb = GOLD
    rows = [("Scene (5.0 s)", c[1]), ("Voiceover", f"“{d['vo']}”  ({len(re.findall(chr(39) + r'?[A-Za-z]+' + chr(39) + '?', d['vo']))} words)"),
            ("Image-generation prompt", d["img"]), ("Animation prompt", d["anim"]), ("Camera / framing", c[3]),
            ("On-screen text", c[7].replace("\n", "  /  ") or "(none)"), ("Sound / music", c[8]), ("Transition out", c[9])]
    t2 = doc.add_table(rows=len(rows), cols=2); t2.style = "Table Grid"
    for k, (a, b) in enumerate(rows):
        c0, c1 = t2.cell(k, 0), t2.cell(k, 1); c0.width, c1.width = Cm(3.3), Cm(14.3); c0.text = c1.text = ""
        r0 = c0.paragraphs[0].add_run(a); r0.bold = True; r0.font.size = Pt(8.5); r0.font.color.rgb = TEAL; shade(c0, "F7F3EB")
        r1 = c1.paragraphs[0].add_run(b); r1.font.size = Pt(8.8)
        if a == "Voiceover": r1.bold = True; r1.font.color.rgb = NAVY; r1.font.size = Pt(10)
        c0.paragraphs[0].paragraph_format.space_after = Pt(0); c1.paragraphs[0].paragraph_format.space_after = Pt(0)
    for tb in (t, t2):  # keep each clip card on one page
        for row in tb.rows:
            trPr = row._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trPr.append(cs)
            for cl in row.cells:
                for pp in cl.paragraphs: pp.paragraph_format.keep_with_next = True
    doc.add_paragraph().paragraph_format.space_after = Pt(3)


# ---------------- cover
t = doc.add_table(rows=1, cols=1); c = t.cell(0, 0); shade(c, "12243A"); c.text = ""
p = c.paragraphs[0]; p.paragraph_format.space_before = Pt(8)
r = p.add_run("WASL Arena"); r.font.size = Pt(30); r.bold = True; r.font.name = "Cambria"; r.font.color.rgb = RGBColor(0xF7, 0xF3, 0xEB)
for text, size, col, bold in [("Two-minute video: final script", 15, GOLD, False), ("Voiceover · image-generation prompts · animation prompts · shot list", 11, RGBColor(0xDD, 0xE6, 0xEA), False),
                              ("Team 204  ·  Team code AYUCK  ·  Track: Cycle 3 (grades 9-12)", 11.5, GOLD, True),
                              ("May Ahmed Mourad (G12)  ·  Shamsa Faris Almazrouei (G12)  ·  Fatima Mohamed Almazrouei (G11)", 10.5, RGBColor(0xF7, 0xF3, 0xEB), False)]:
    q = c.add_paragraph(); q.paragraph_format.space_after = Pt(4); rr = q.add_run(text); rr.font.size = Pt(size); rr.font.color.rgb = col; rr.bold = bold; rr.font.name = "Cambria" if size > 12 else "Calibri"
doc.add_paragraph()
h1("1. Overview")
para("**One line:** a fair referee shows its evidence, admits doubt, and lets people decide. The film moves from a relatable family argument, to the WASL Arena reveal, through real demonstrations of all three games, to the explainable AI Referee Replay, the test evidence and the Family Cup.")
table([["Item", "Specification"],
       ["Length", "24 clips × exactly 5.0 s = **120.0 s** (maximum allowed: 2 minutes). Transitions happen inside each clip; no extra runtime."],
       ["Format", STYLE["format"] + ", H.264 MP4, AAC audio."],
       ["Structure", "Clips 01-04 hook and reveal · 05-08 the app · 09-12 Football · 13-16 Falaj Flow · 17-20 Souq Signal · 21-22 evidence and testing · 23-24 results and close."],
       ["Voiceover", "24 lines, 7-12 words each (about 2.2 words per second), final text below. One line per clip so each can be re-recorded independently."],
       ["Live product", "App: https://frontend-three-fawn-47.vercel.app · AI judge: https://wasl-arena.onrender.com · Code: github.com/MayMourad/wasl-arena"]], [3.0, 14.6])
h1("2. Authenticity rules (what the video must not do)")
for b in ["**Use real captures of the finished app** for every interface shot (clips 04-08, 10-12, 14-16, 18-23). Never ask an AI image or video model to draw the interface, the detections or the scores; it would invent them.",
          "**Use genuine gameplay** for the scoring demonstrations (clips 09, 13, 17). The animatic marks these with a red SYNTHETIC FIXTURE banner because real footage still has to be recorded; replace those frames before submission.",
          "AI-generated imagery is allowed only for **atmosphere**: clips 01-03 and 24 (family B-roll, abstract plates). Label it as AI-generated in the AI usage report.",
          "Say only numbers that appear on screen from a real run. The 46 tests / 9 fixtures figures are from the current run; update them if the test count changes.",
          "Everyone filmed must give consent. Fictional AI-generated people must not resemble real individuals."]:
    para("•  " + b, after=1)
h1("3. Style bible and prompt conventions")
table([["Element", "Direction"],
       ["Palette", STYLE["palette"]], ["Look", STYLE["look"]], ["Family (AI B-roll)", STYLE["people"]],
       ["Typography (editor)", "Fraunces for titles, Inter for supporting text; ivory on navy; gold for small labels; generous margins."],
       ["Negative prompt (append to every image prompt)", STYLE["global_negative"]],
       ["Consistency", "Generate clips 01, 02 and 24 in one session with the same seed and the same family description; reuse the first frame of clip 01 as the reference image for clip 02."],
       ["Voice direction", VO_DIRECTION], ["Music", MUSIC]], [4.0, 13.6])
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
h1("4. Final voiceover script (read straight through = 120 s)")
rows = [["Clip", "Time", "Voiceover"]]
for i, d in enumerate(DATA):
    rows.append([f"{i + 1:02d}", f"{(i * 5) // 60}:{(i * 5) % 60:02d}", d["vo"]])
table(rows, [1.3, 1.6, 14.7], size=10)
para("Total spoken words: " + str(sum(len(re.findall(r"[A-Za-z']+", d["vo"])) for d in DATA)) + ". Read at a calm pace, each line ends before its clip does, leaving room for the transition.", italic=True, size=9)
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
h1("5. Shot-by-shot: scene, prompts, voiceover, sound")
para("Image prompt = still or background plate (for AI-generated clips) or a storyboard/plate only (for real-capture clips). Animation prompt = image-to-video prompt for generated clips, or the exact editor motion and recording instructions for real captures.", italic=True, size=9)
for i in range(24):
    card(i)
h1("6. Asset checklist before final export")
table([["Need", "Clips", "Status"],
       ["Real football footage (fixed camera, goal scored)", "09", "TO RECORD"], ["Real Falaj footage (top-down, board + tiles)", "13", "TO RECORD"], ["Real Souq footage (cards + voice)", "17", "TO RECORD"],
       ["Screen recording of a real upload through the judging stages", "10", "TO RECORD (live site)"], ["Other app captures (setup, library, console, replays, lab, cup)", "04-08, 11-12, 14-16, 18-23", "Screenshots done; re-record as video for motion"],
       ["AI-generated B-roll and plates", "01-03, 24", "TO GENERATE with prompts above"], ["Final voiceover (24 takes)", "all", "TO RECORD (draft TTS animatic exists)"], ["Music track", "all", "TO LICENSE / compose"]], [9.2, 4.0, 4.4])
h1("7. Export settings")
para("MP4 (H.264 High, yuv420p) · 1920×1080 · 30 fps constant · 12-16 Mbps · AAC 192 kbps 48 kHz stereo · integrated loudness −14 LUFS · total duration ≤ 120.0 s · burned-in captions recommended · file name: WASL-Arena-Team204-AYUCK.mp4.")
out = Path(__file__).resolve().parent / "WASL-Arena-Video-Script-Final.docx"; doc.save(out); print("saved", out)
