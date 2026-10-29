"""WASL Arena API - upload/record -> real judging pipelines -> sealed, explainable reports."""
from __future__ import annotations

import json
import re
import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import config, integrity, jobs, reports
from .rules import falaj as falaj_rules
from .rules import football as football_rules
from .rules import souq as souq_rules
from .vision import falaj_cv, football_cv, souq_cv, video

app = FastAPI(title="WASL Arena AI Referee", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

JUDGES = {"football": football_cv.judge, "falaj": falaj_cv.judge, "souq": souq_cv.judge}
RULESETS = {"football": football_rules.RULE_VERSION, "falaj": falaj_rules.RULE_VERSION, "souq": souq_rules.RULE_VERSION}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "judge": "WASL AI Referee 1.0.0", "rule_versions": RULESETS,
            "transcription": "configured" if config.GEMINI_API_KEY else "not configured", "signing_key_id": config.SIGNING_KEY_ID}


@app.get("/api/catalog")
def catalog() -> dict:
    return {"souq": {k: {"en": v["en"], "ar": v["ar"], "price": v["price"], "marker_ids": v["marker_ids"]} for k, v in souq_rules.CATALOG.items()},
            "falaj": {"layouts": falaj_rules.LAYOUTS, "tile_ids": falaj_rules.TILE_IDS},
            "football": {"color_presets": list(football_cv.COLOR_PRESETS), "defaults": football_cv.DEFAULT_CONFIG},
            "rule_versions": RULESETS}


@app.post("/api/judge/{game}")
async def judge(game: str, file: UploadFile = File(...), config_json: str = Form("{}")) -> dict:
    if game not in JUDGES:
        raise HTTPException(404, "unknown game")
    try:
        cfg = json.loads(config_json or "{}")
    except json.JSONDecodeError:
        raise HTTPException(400, "config_json must be valid JSON")
    jid = jobs.create(game)
    rid = uuid.uuid4().hex[:12]
    raw = config.DATA / "uploads" / f"{rid}.upload"
    size = 0
    with raw.open("wb") as f:
        while chunk := await file.read(1 << 20):
            size += len(chunk)
            if size > config.MAX_UPLOAD_MB * 1024 * 1024:
                f.close()
                raw.unlink(missing_ok=True)
                raise HTTPException(413, f"file larger than {config.MAX_UPLOAD_MB} MB")
            f.write(chunk)
    original_sha = integrity.sha256_file(raw)
    name = re.sub(r"[^\w.\- ]", "_", file.filename or "upload")

    def work(progress):
        progress("extracting", 0.01, "normalising video to H.264 / constant frame rate")
        norm = config.DATA / "uploads" / f"{rid}.mp4"
        if not video.normalize(raw, norm):
            raise RuntimeError("could not decode this video file")
        return JUDGES[game](norm, original_sha, name, cfg, progress, rid)

    jobs.run(jid, work)
    return {"job_id": jid, "report_id": rid}


@app.get("/api/jobs/{jid}")
def job(jid: str) -> dict:
    j = jobs.get(jid)
    if not j:
        raise HTTPException(404, "unknown job")
    return j


@app.get("/api/reports/{rid}")
def get_report(rid: str) -> dict:
    try:
        r = reports.load(rid)
    except FileNotFoundError:
        raise HTTPException(404, "report not found")
    r["integrity_check"] = integrity.verify(r)
    return r


@app.get("/api/media/{rid}")
def media(rid: str):
    p = config.DATA / "uploads" / f"{rid}.mp4"
    if not re.fullmatch(r"[\w\-]{1,64}", rid) or not p.exists():
        raise HTTPException(404, "media not found")
    return FileResponse(p, media_type="video/mp4")


@app.get("/api/evidence/{rid}/{name}")
def evidence(rid: str, name: str):
    p = config.DATA / "evidence" / rid / name
    if not re.fullmatch(r"[\w\-]{1,64}", rid) or not re.fullmatch(r"[\w.\-]+", name) or not p.exists():
        raise HTTPException(404, "evidence not found")
    return FileResponse(p, media_type="image/jpeg")


class Review(BaseModel):
    event_id: str
    decision: str
    by: str = "host"
    note: str = ""


@app.post("/api/reports/{rid}/review")
def review(rid: str, body: Review) -> dict:
    try:
        r = reports.apply_review(reports.load(rid), body.event_id, body.decision, body.by, body.note)
    except FileNotFoundError:
        raise HTTPException(404, "report not found")
    except (KeyError, ValueError) as exc:
        raise HTTPException(400, str(exc))
    r["integrity_check"] = integrity.verify(r)
    return r


class Assign(BaseModel):
    assignments: dict[str, str]
    by: str = "host"


@app.post("/api/reports/{rid}/assignments")
def assign(rid: str, body: Assign) -> dict:
    try:
        r = reports.apply_assignments(reports.load(rid), body.assignments, body.by)
    except FileNotFoundError:
        raise HTTPException(404, "report not found")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    r["integrity_check"] = integrity.verify(r)
    return r


class Transcript(BaseModel):
    text: str
    by: str = "host"


@app.post("/api/reports/{rid}/transcript")
def transcript(rid: str, body: Transcript) -> dict:
    try:
        r = reports.apply_transcript(reports.load(rid), body.text, body.by)
    except FileNotFoundError:
        raise HTTPException(404, "report not found")
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    r["integrity_check"] = integrity.verify(r)
    return r


@app.post("/api/reports/verify")
async def verify_uploaded(file: UploadFile = File(...)) -> dict:
    """Verify a report produced by the stand-alone judge CLI (hash + signature)."""
    try:
        rep = json.loads((await file.read()).decode("utf-8"))
    except Exception:
        raise HTTPException(400, "not a JSON report")
    res = integrity.verify(rep)
    if res["ok"]:
        reports.save(rep)  # make it available to the app
    return {**res, "report_id": rep.get("report_id") if res["ok"] else None}


@app.post("/api/falaj/analyze")
def falaj_analyze(body: dict) -> dict:
    """Pure rule check for a hand-entered / preview board (no video): used by the digital twin preview."""
    layout = falaj_rules.LAYOUTS[body.get("layout", "oasis-1")]
    tiles = {(t["cell"][0], t["cell"][1]): {"type": t["type"], "rot": t["rot"], "id": t.get("id", 0)} for t in body.get("tiles", [])}
    an = falaj_rules.analyze(layout, tiles)
    return {"analysis": an, "score": falaj_rules.score_round(an, body.get("completion_s"))}


class AuditEntry(BaseModel):
    action: str
    detail: dict = {}


@app.post("/api/audit/{session}")
def audit_append(session: str, entry: AuditEntry) -> dict:
    if not re.fullmatch(r"[\w\-]{4,64}", session):
        raise HTTPException(400, "bad session id")
    p = config.DATA / "audit" / f"{session}.jsonl"
    prev = "GENESIS"
    if p.exists():
        lines = p.read_text(encoding="utf-8").strip().splitlines()
        if lines:
            prev = json.loads(lines[-1])["hash"]
    rec = {"n": (len(p.read_text(encoding="utf-8").splitlines()) if p.exists() else 0) + 1, "at": reports._now(), "action": entry.action,
           "detail": entry.detail, "prev": prev}
    rec["hash"] = integrity.sha256_bytes(integrity.canonical(rec))
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


@app.get("/api/audit/{session}")
def audit_get(session: str) -> dict:
    p = config.DATA / "audit" / f"{session}.jsonl"
    if not re.fullmatch(r"[\w\-]{4,64}", session) or not p.exists():
        return {"entries": [], "chain_ok": True}
    entries = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    ok, prev = True, "GENESIS"
    for e in entries:
        body = {k: v for k, v in e.items() if k != "hash"}
        if e["prev"] != prev or integrity.sha256_bytes(integrity.canonical(body)) != e["hash"]:
            ok = False
        prev = e["hash"]
    return {"entries": entries, "chain_ok": ok}
