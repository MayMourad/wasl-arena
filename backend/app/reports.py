"""Report storage, host review and audit history."""
from __future__ import annotations

import copy
import re
import datetime as dt
import json
from pathlib import Path

from . import config, integrity
from .rules.football import RULE_VERSION as FB_V  # noqa: F401
from .vision import falaj_cv, football_cv, souq_cv

SUMMARISERS = {"football": football_cv.summarise, "falaj": falaj_cv.summarise, "souq": souq_cv.summarise}


def path(rid: str) -> Path:
    if not re.fullmatch(r"[\w\-]{1,64}", rid):
        raise FileNotFoundError(rid)
    return config.DATA / "reports" / f"{rid}.json"


def load(rid: str) -> dict:
    return json.loads(path(rid).read_text(encoding="utf-8"))


def save(report: dict) -> None:
    path(report["report_id"]).write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _log(report: dict, action: str, detail: dict) -> None:
    prev = report["audit"][-1]["hash"] if report["audit"] else report["integrity"]["report_sha256"]
    entry = {"at": _now(), "action": action, "detail": detail, "prev": prev}
    entry["hash"] = integrity.sha256_bytes(integrity.canonical(entry))
    report["audit"].append(entry)


def apply_review(report: dict, event_id: str, decision: str, by: str, note: str = "") -> dict:
    """Host accepts / rejects an event; the score is recomputed by the deterministic rule engine.
    The original AI seal is preserved; a second host seal covers the reviewed state."""
    if decision not in ("ACCEPTED", "REJECTED", "CLEARED"):
        raise ValueError("decision must be ACCEPTED, REJECTED or CLEARED")
    ev = next((e for e in report["events"] if e["id"] == event_id), None)
    if ev is None:
        raise KeyError(event_id)
    ev["review"] = None if decision == "CLEARED" else {"decision": decision, "by": by, "note": note, "at": _now()}
    report["summary"] = SUMMARISERS[report["game"]](report)
    _log(report, f"review:{decision}", {"event": event_id, "by": by, "note": note})
    return _reseal(report)


def apply_assignments(report: dict, assignments: dict[str, str], by: str) -> dict:
    if report["game"] != "football":
        raise ValueError("assignments apply to football only")
    report["config"]["assignments"] = {k: v for k, v in assignments.items() if v}
    report["summary"] = football_cv.summarise(report)
    _log(report, "assign_players", {"assignments": report["config"]["assignments"], "by": by})
    return _reseal(report)


def apply_transcript(report: dict, text: str, by: str) -> dict:
    """Host types the transcript when automatic transcription was unavailable (flagged host_entered)."""
    if report["game"] != "souq":
        raise ValueError("transcript applies to souq only")
    from .rules import souq as srules
    dur = report["source"].get("duration_s") or 0
    seg = [{"start": 0.0, "end": float(dur), "text": text}]
    # host transcript has no timing: place each product mention at the time the card was shown
    mentions = []
    for p in report["metrics"]["presentations"]:
        for m in srules.find_mentions([{"start": p["t_first"], "end": p["t_first"] + 1.0, "text": text}]):
            if m["product"] == p["product"]:
                mentions.append({**m, "t": p["t_first"]})
    for m in srules.find_mentions(seg):
        if m["product"] not in {x["product"] for x in report["metrics"]["presentations"]}:
            mentions.append(m)
    tr = {"status": "OK", "source": "host_entered", "segments": seg}
    ev = srules.evaluate(report["config"]["mission"], report["metrics"]["presentations"], mentions, True)
    old = {e["id"]: e for e in report["events"]}
    for e in ev["events"]:
        prev = old.get(e["id"])
        e["evidence"] = prev["evidence"] if prev else []
        e["review"] = prev["review"] if prev else None
    report["events"] = ev["events"]
    report["metrics"]["transcript"] = tr
    report["metrics"]["mentions"] = mentions
    report["summary"] = souq_cv.summarise(report)
    _log(report, "host_transcript", {"by": by, "chars": len(text)})
    return _reseal(report)


def _reseal(report: dict) -> dict:
    ai_seal = report.get("ai_integrity") or copy.deepcopy(report["integrity"])
    report.pop("integrity", None)
    report.pop("host_integrity", None)
    integrity.seal(report, "host_integrity")
    report["ai_integrity"] = ai_seal
    report["integrity"] = report["host_integrity"]
    report["integrity"]["note"] = "re-sealed after host review; original AI seal kept in ai_integrity"
    save(report)
    return report
