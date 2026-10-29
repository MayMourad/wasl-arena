"""Run the REAL judging pipelines on the synthetic fixtures and export:
  frontend/public/samples/<name>.json|.mp4 + evidence images   (static replays that work without a backend)
  frontend/public/evaluation.json                               (actual vs expected + pytest results)
Nothing here is hand-written: every number comes from the pipeline / pytest run.
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))
from app import config, integrity  # noqa: E402
from app.vision import falaj_cv, football_cv, souq_cv  # noqa: E402

FIX = ROOT / "fixtures"
PUB = ROOT / "frontend" / "public"
SAMPLES = PUB / "samples"
SAMPLES.mkdir(parents=True, exist_ok=True)
manifest = json.loads((FIX / "manifest.json").read_text(encoding="utf-8"))
JUDGE = {"football": football_cv.judge, "falaj": falaj_cv.judge, "souq": souq_cv.judge}


def run(name: str, cfg: dict | None, out_name: str | None = None) -> dict:
    out_name = out_name or name
    game = manifest[name]["game"]
    p = FIX / f"{name}.mp4"
    rep = JUDGE[game](p, integrity.sha256_file(p), p.name, cfg, lambda s, pr, d: None, out_name)
    shutil.copy(p, SAMPLES / f"{out_name}.mp4")
    ev_src = config.DATA / "evidence" / out_name
    ev_dst = SAMPLES / "evidence" / out_name
    if ev_dst.exists():
        shutil.rmtree(ev_dst)
    if ev_src.exists():
        shutil.copytree(ev_src, ev_dst)
    for e in rep["events"]:
        for ev in e.get("evidence", []):
            if ev.get("thumb"):
                ev["thumb"] = ev["thumb"].replace("/api/evidence/", "/samples/evidence/")
    rep["sample"] = out_name
    rep["synthetic_fixture"] = True
    rep.pop("integrity", None)
    integrity.seal(rep)
    rep["integrity_check"] = integrity.verify(rep)
    (SAMPLES / f"{out_name}.json").write_text(json.dumps(rep, ensure_ascii=False), encoding="utf-8")
    return rep


def actual(game: str, r: dict) -> dict:
    s = r["summary"]
    if game == "football":
        goals = [e for e in r["events"] if e["type"] == "GOAL" and e["status"] == "VERIFIED"]
        poss = [e for e in r["events"] if e["type"] == "POSSIBLE_GOAL"]
        return {"goals_A": s["score"]["A"], "goals_B": s["score"]["B"], "verified_goal_events": len(goals),
                "possible_goal": poss[0]["status"] if poss else None, "possession_leader": s["possession"]["leader"]}
    if game == "falaj":
        sc = s["score"]
        return {"destinations": sc["destinations"], "leaks": sc["leaks"], "time_bonus": sc["time_bonus"], "total": sc["total"]}
    kinds = [e["type"] for e in r["events"]]
    return {"total": s["score"]["total"], "spend": s["spend"], "mismatch": "AUDIO_VIDEO_MISMATCH" in kinds,
            "duplicate": "DUPLICATE_ITEM" in kinds, "budget_exceeded": "BUDGET_EXCEEDED" in kinds}


def matches(exp: dict, act: dict) -> bool:
    for k, v in exp.items():
        if k == "status":
            continue
        if k == "possible_goal":
            if act.get("possible_goal") != v:
                return False
        elif k in ("mismatch", "duplicate", "budget_exceeded"):
            if act.get(k) != v:
                return False
        elif act.get(k) != v:
            return False
    return True


def main() -> None:
    cases = []
    for name, m in manifest.items():
        cfg = None
        if m["game"] == "souq":
            cfg = {"mission": m["mission"], "transcript_override": m["transcript_script"]}
        r = run(name, cfg)
        act = actual(m["game"], r)
        cases.append({"name": name, "game": m["game"], "synthetic": True, "expected": m["expect"], "actual": act, "pass": matches(m["expect"], act),
                      "report": f"sample-{name}", "transcript_source": r["metrics"].get("transcript", {}).get("source") if m["game"] == "souq" else None,
                      "events": len(r["events"]), "needs_review": r["summary"].get("needs_review", sum(1 for e in r["events"] if e["status"] == "NEEDS_REVIEW"))})
        print(name, "->", act, "PASS" if cases[-1]["pass"] else "FAIL")

    # real speech transcription of the synthetic TTS audio (Gemini, transcription only; rules stay deterministic)
    gem = None
    try:
        m = manifest["souq_correct"]
        r = run("souq_correct", {"mission": m["mission"]}, "souq_correct_gemini")
        tr = r["metrics"]["transcript"]
        gem = {"status": tr["status"], "source": tr.get("source"), "segments": tr["segments"], "reason": tr.get("reason"),
               "total": r["summary"]["score"]["total"], "expected_total": m["expect"]["total"], "report": "sample-souq_correct_gemini"}
        print("gemini transcription:", tr["status"], tr["segments"][:3], "score", r["summary"]["score"])
    except Exception as exc:  # noqa: BLE001
        gem = {"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}"}

    junit = ROOT / "backend" / "pytest-report.xml"
    subprocess.run([sys.executable, "-m", "pytest", "-q", f"--junitxml={junit}", "-p", "no:cacheprovider"], cwd=ROOT / "backend", capture_output=True)
    root = ET.parse(junit).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    py = [{"name": tc.get("name"), "file": tc.get("classname", "").split(".")[-1],
           "status": "failed" if tc.find("failure") is not None or tc.find("error") is not None else ("skipped" if tc.find("skipped") is not None else "passed"),
           "seconds": round(float(tc.get("time", 0)), 2)} for tc in suite.iter("testcase")]
    out = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "pytest": {"total": len(py), "passed": sum(c["status"] == "passed" for c in py), "failed": sum(c["status"] == "failed" for c in py),
                   "skipped": sum(c["status"] == "skipped" for c in py), "cases": py},
        "fixtures": cases,
        "transcription_check": gem,
        "real_footage": {"status": "pending", "note": "No real recorded family gameplay has been analysed yet. All fixtures above are SYNTHETIC renders with known ground truth."},
    }
    (PUB / "evaluation.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print("pytest:", out["pytest"]["passed"], "/", out["pytest"]["total"], "passed")


if __name__ == "__main__":
    main()
