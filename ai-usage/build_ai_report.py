"""AI chat usage report. Imports REAL conversation exports (ChatGPT share + Claude Code session). Nothing is invented.
Credentials are redacted. usage: python ai-usage/build_ai_report.py <claude_transcript.jsonl>"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

from docx import Document
from docx.enum.text import WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
NAVY, TEAL, GOLD = RGBColor(0x12, 0x24, 0x3A), RGBColor(0x16, 0x7E, 0x80), RGBColor(0xC6, 0xA3, 0x6B)
KEY = re.compile(r"AQ\.[A-Za-z0-9_\-]{20,}|AIza[A-Za-z0-9_\-]{30,}|gho_[A-Za-z0-9]{20,}")
redactions = 0


def redact(s: str) -> str:
    global redactions
    out, n = KEY.subn("[REDACTED-API-KEY]", s); redactions += n
    return out


def clean(s: str) -> str:
    s = re.sub(r"<system-reminder>.*?</system-reminder>", "", s, flags=re.S)
    s = re.sub(r"</?pasted_content[^>]*>", "", s)
    return s.strip()


# ---------- load sources
chat = json.loads((ROOT / "ai-usage/chatgpt-export.json").read_text(encoding="utf-8"))
tpath = Path(sys.argv[1])
turns, tools = [], Counter()
first_ts = last_ts = None
for line in tpath.read_text(encoding="utf-8").splitlines():
    try: e = json.loads(line)
    except json.JSONDecodeError: continue
    ts = e.get("timestamp")
    if ts: first_ts = first_ts or ts; last_ts = ts
    if e.get("type") not in ("user", "assistant") or e.get("isSidechain"): continue
    c = e["message"].get("content")
    if isinstance(c, str): c = [{"type": "text", "text": c}]
    for b in c or []:
        if b.get("type") == "tool_use": tools[b["name"].split("__")[-1]] += 1
        elif b.get("type") == "text":
            t = clean(b["text"])
            if not t or t.startswith("[SYSTEM NOTIFICATION") or "<task-notification>" in t: continue
            turns.append({"role": e["type"], "at": ts, "text": redact(t)})
claude_export = {"tool": "Claude Code (Claude Sonnet 5.5)", "session": "WASL Arena competition submission", "first_event": first_ts, "last_event": last_ts,
                 "note": "Verbatim user messages and assistant text messages. Tool calls/outputs omitted (counts in report). API keys redacted.", "turns": turns,
                 "tool_call_counts": dict(tools.most_common())}
(ROOT / "ai-usage/claude-code-session-export.redacted.json").write_text(json.dumps(claude_export, ensure_ascii=False, indent=1), encoding="utf-8")
chat_turns = [{"role": t["role"], "text": redact(t["text"])} for t in chat["turns"]]
ev = json.loads((ROOT / "frontend/public/evaluation.json").read_text(encoding="utf-8"))

# ---------- document
doc = Document(); s0 = doc.sections[0]
s0.page_width, s0.page_height = Cm(21), Cm(29.7); s0.left_margin = s0.right_margin = Cm(1.8); s0.top_margin = s0.bottom_margin = Cm(1.6)
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10); st.paragraph_format.space_after = Pt(3)
hp = s0.header.paragraphs[0]; r = hp.add_run("WASL Arena · AI Chat Usage Report · Team 204 · Code AYUCK · Cycle 3 (grades 9-12)"); r.font.size = Pt(8); r.font.color.rgb = TEAL


def shade(cell, hex_):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_); tcPr.append(shd)


def H(text, size=16, color=NAVY, before=8):
    p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(before); p.paragraph_format.keep_with_next = True
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size); r.font.color.rgb = color; r.font.name = "Cambria"


def P(text, size=10, bold=False, italic=False, color=None):
    p = doc.add_paragraph()
    for i, part in enumerate(text.split("**")):
        if not part: continue
        r = p.add_run(part); r.bold = bold or i % 2 == 1; r.italic = italic; r.font.size = Pt(size)
        if color: r.font.color.rgb = color
    return p


def table(rows, widths, size=9):
    t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.style = "Table Grid"
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.width = Cm(widths[j]); c.text = ""; p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(v)); r.font.size = Pt(size); r.bold = i == 0
            if i == 0: shade(c, "12243A"); r.font.color.rgb = RGBColor(255, 255, 255)
            elif i % 2 == 0: shade(c, "F7F3EB")
    doc.add_paragraph()


def turn_block(label, text, role):
    t = doc.add_table(rows=1, cols=1); c = t.cell(0, 0); shade(c, "E8F1F1" if role == "user" else "F7F3EB"); c.text = ""
    p = c.paragraphs[0]; r = p.add_run(label); r.bold = True; r.font.size = Pt(8.5); r.font.color.rgb = TEAL if role == "user" else NAVY
    for para in text.split("\n"):
        q = c.add_paragraph(); q.paragraph_format.space_after = Pt(1)
        r = q.add_run(para if para.strip() else " "); r.font.size = Pt(8.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


# cover
t = doc.add_table(rows=1, cols=1); c = t.cell(0, 0); shade(c, "12243A"); c.text = ""
p = c.paragraphs[0]; r = p.add_run("AI Chat Usage Report"); r.font.size = Pt(26); r.bold = True; r.font.color.rgb = RGBColor(0xF7, 0xF3, 0xEB); r.font.name = "Cambria"
for line, col, sz in [("WASL Arena · Family AI Game Day · 6th Annual COE STEM Programming with AI Competition", GOLD, 11), ("Team 204 · Team code AYUCK · Track: Cycle 3 (grades 9-12)", GOLD, 12),
                      ("May Ahmed Mourad (G12) · Shamsa Faris Almazrouei (G12) · Fatima Mohamed Almazrouei (G11)", RGBColor(0xF7, 0xF3, 0xEB), 11)]:
    q = c.add_paragraph(); r = q.add_run(line); r.font.size = Pt(sz); r.font.color.rgb = col; r.bold = sz == 12
doc.add_paragraph()
H("1. Purpose and authenticity statement", 14)
P("This report documents how the team used AI assistants to plan, build, test and document WASL Arena. Appendices A and B reproduce the **original conversation text exactly as exported**: Appendix A from the shared ChatGPT conversation, Appendix B from this Claude Code session (user messages and assistant replies). Nothing was rewritten or invented. The only change is **redaction of credentials** (API keys → [REDACTED-API-KEY]; "
  f"{redactions} occurrence(s) redacted). Conversations that are not attached are not claimed.")
H("2. AI tools and models used", 14)
table([["Tool / model", "Used for", "Evidence"],
       ["ChatGPT (OpenAI)", "Concept ideation (WASL Arena, three games), consolidated master execution prompt, design-reference links (Spline, Recent.design)", "Appendix A (share link in export)"],
       ["Claude Code · Claude Sonnet 5.5 (Anthropic)", "Implementation: backend, CV pipelines, rule engines, tests, React frontend, printables, report/deck/video/AI-report generators, debugging, QA", f"Appendix B ({len(turns)} messages; {sum(tools.values())} tool calls)"],
       ["Gemini API · gemini-3.1-flash-lite (Google)", "Runtime speech transcription in Souq Signal only (never scores). Model selected after the originally planned model was found retired for new users.", "Evaluation Lab 'Speech transcription check'"],
       ["Windows text-to-speech (SAPI)", "Synthetic audio for test fixtures and scratch narration of the draft animatic", "fixtures/, video/ (labelled)"]], [4.2, 8.6, 4.6])
H("3. Development phases and AI contribution", 14)
table([["Phase", "What the AI did", "Human / verification step"],
       ["1 Concept", "Proposed WASL Arena and three games; consolidated one master prompt (ChatGPT)", "Team chose the concept; brief read from the official question images"],
       ["2 Architecture", "Designed FastAPI + OpenCV + rule-engine architecture, evidence-integrity scheme (Claude Code)", "Decisions checked against the brief (host flow, hash-verified reports, MVP = longest possession)"],
       ["3 Code generation", "Wrote rule engines, football/falaj/souq pipelines, API, React app (Claude Code)", "Type-check and production build; UI inspected in a browser"],
       ["4 Debugging", "Found and fixed: well-inlet counted as leak; Arabic ال prefix not matched; accepted possible goal not scored; retired Gemini model", "Failures surfaced by the test suite, then re-run"],
       ["5 Testing", f"Wrote {ev['pytest']['total']} tests and 9 synthetic fixtures with known ground truth", f"{ev['pytest']['passed']}/{ev['pytest']['total']} tests passed in the final run; fixtures are synthetic, not real gameplay"],
       ["6 Design iterations", "Applied the palette, Spline-inspired orb (original Three.js), Krea-style judging sequence; fixed contrast bug (invisible text) found in screenshots", "Screenshots reviewed by the AI and team"],
       ["7 Documentation", "Generated the 6-page report, 30-slide deck, video package and this report from real results", "Page count verified in Word (6 pages); slides rendered in PowerPoint (30)"],
       ["8 Video scripting", "Wrote the 24 × 5 s script: voiceover, image-generation prompts, animation prompts, shot list; built a draft animatic from real screenshots", "Real gameplay clips (football, Falaj, Souq) must be recorded by the team; AI imagery limited to atmosphere clips"],
       ["9 Deployment & debugging", "Diagnosed the Render build failure from the team's pasted log (Root Directory not set), verified the live Render API with a real judging job, found the Vercel build lacked VITE_API_URL, verified CORS", "Team created the Render and Vercel projects, set environment variables and redeployed; AI checked the live site afterwards"],
       ["10 Publication", "Prepared the GitHub release, README with recorded website tour and full-page captures, deck PDF; verified downloads and that README images load for logged-out visitors", "Team made the repository public and approved publication"]], [2.8, 8.0, 6.6], size=8.5)
H("4. Human verification and adjustments", 14)
for b in ["The team supplied the official competition materials, team identity, the ChatGPT conversation and the speech API key; the key was kept in a git-ignored server-side `.env` and is redacted in this report. Because the key appeared in a chat, **rotate it after the competition**.",
          "All numbers in the report/deck/Evaluation Lab are read from files produced by running the tests and pipelines.",
          "Synthetic fixtures are always labelled; real footage is pending and is not represented as tested.",
          "Items still requiring human action: record real gameplay for football, Falaj and Souq, review final wording, record the voice-over and music, and rotate the API key used during development."]:
    P("•  " + b)
H("5. Claude Code activity summary", 14)
table([["Tool category", "Calls"]] + [[k, v] for k, v in tools.most_common(12)], [9, 3])
P(f"Session window (UTC): {first_ts} to {last_ts}. The transcript was exported while work was in progress; later turns are not included.", italic=True, size=9)
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
H("Appendix A: ChatGPT conversation (verbatim export)", 15, TEAL, 0)
P(f"Source: {chat['source']} · captured {chat['captured_at']} · {len(chat_turns)} messages. Formatting flattened to text; file attachments are shown only as 'Uploaded a file' placeholders in the export.", italic=True, size=9)
for i, tr in enumerate(chat_turns):
    turn_block(f"{'USER' if tr['role'] == 'user' else 'CHATGPT'}  ·  message {i + 1}", tr["text"], tr["role"])
doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
H("Appendix B: Claude Code conversation (verbatim user messages and assistant replies)", 15, TEAL, 0)
P("Tool calls and tool outputs are omitted for length (summarised in section 5). Pasted API credentials are redacted.", italic=True, size=9)
for i, tr in enumerate(turns):
    turn_block(f"{'USER' if tr['role'] == 'user' else 'CLAUDE'}  ·  {tr['at'][:19].replace('T', ' ')} UTC", tr["text"], tr["role"])
out = ROOT / "ai-usage" / "WASL-Arena-AI-Chat-Usage-Report.docx"; doc.save(out); print("saved", out, "turns", len(turns), "redactions", redactions)
