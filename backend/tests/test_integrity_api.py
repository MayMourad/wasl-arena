import json
import time

import pytest
from fastapi.testclient import TestClient

from app import integrity
from app.main import app

client = TestClient(app)


def test_seal_verify_and_tamper_detection():
    rep = {"report_id": "abc", "events": [{"id": "g1", "points": 1}], "summary": {"score": 1}}
    integrity.seal(rep)
    assert integrity.verify(rep)["ok"]
    rep["summary"]["score"] = 99
    res = integrity.verify(rep)
    assert not res["ok"] and any("modified" in r for r in res["reasons"])


def test_forged_signature_rejected():
    rep = {"report_id": "abc", "x": 1}
    integrity.seal(rep)
    rep["integrity"]["signature"] = "0" * 64
    assert not integrity.verify(rep)["ok"]


def test_health_and_catalog():
    assert client.get("/api/health").json()["status"] == "ok"
    cat = client.get("/api/catalog").json()
    assert len(cat["souq"]) == 8 and "oasis-1" in cat["falaj"]["layouts"]


def test_falaj_analyze_endpoint():
    tiles = [{"cell": [3, 3], "type": "ELBOW", "rot": 2}]
    r = client.post("/api/falaj/analyze", json={"layout": "oasis-1", "tiles": tiles}).json()
    assert r["analysis"]["all_connected"] is False


def _judge(fixtures, name, cfg=None):
    with open(fixtures / f"{name}.mp4", "rb") as f:
        r = client.post(f"/api/judge/{name.split('_')[0]}", files={"file": (f"{name}.mp4", f, "video/mp4")}, data={"config_json": json.dumps(cfg or {})})
    assert r.status_code == 200
    jid = r.json()["job_id"]
    for _ in range(240):
        j = client.get(f"/api/jobs/{jid}").json()
        if j["status"] != "running":
            break
        time.sleep(0.5)
    assert j["status"] == "done", j
    return client.get(f"/api/reports/{j['report_id']}").json(), j


def test_upload_job_report_review_flow(fixtures):
    rep, job = _judge(fixtures, "football_uncertain")
    assert rep["integrity_check"]["ok"]
    stages = [s["stage"] for s in job["log"]]
    assert stages[0] == "uploaded" and stages[-1] == "verified" and "extracting" in stages and "detecting" in stages
    flagged = next(e for e in rep["events"] if e["status"] == "NEEDS_REVIEW")
    assert rep["summary"]["score"] == {"A": 0, "B": 0}
    r2 = client.post(f"/api/reports/{rep['report_id']}/review", json={"event_id": flagged["id"], "decision": "ACCEPTED", "by": "pytest-host"}).json()
    assert r2["summary"]["score"][flagged["team"]] == 1  # score recomputed after human review
    assert r2["integrity_check"]["ok"] and r2["audit"][-1]["action"] == "review:ACCEPTED"
    assert r2["ai_integrity"]["report_sha256"] == rep["integrity"]["report_sha256"]  # original AI seal preserved


def test_tampered_report_is_rejected_on_import(fixtures, tmp_path):
    rep, _ = _judge(fixtures, "falaj_partial")
    rep.pop("integrity_check", None)
    ok = client.post("/api/reports/verify", files={"file": ("r.json", json.dumps(rep), "application/json")}).json()
    assert ok["ok"] is True
    rep["summary"]["score"]["total"] = 99
    bad = client.post("/api/reports/verify", files={"file": ("r.json", json.dumps(rep), "application/json")}).json()
    assert bad["ok"] is False


def test_audit_chain_detects_tampering():
    sid = "pytest-session-1"
    p = __import__("app.config", fromlist=["DATA"]).DATA / "audit" / f"{sid}.jsonl"
    p.unlink(missing_ok=True)
    for a in ("register", "start", "apply"):
        client.post(f"/api/audit/{sid}", json={"action": a, "detail": {"k": a}})
    assert client.get(f"/api/audit/{sid}").json()["chain_ok"] is True
    lines = p.read_text(encoding="utf-8").splitlines()
    e = json.loads(lines[1])
    e["detail"] = {"k": "forged"}
    lines[1] = json.dumps(e)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    assert client.get(f"/api/audit/{sid}").json()["chain_ok"] is False
