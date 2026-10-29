"""Background judging jobs with real stage reporting (uploaded -> extracting -> detecting -> events -> rules -> verified)."""
from __future__ import annotations

import json
import threading
import time
import traceback
import uuid
from typing import Callable

from . import config

STAGES = ["uploaded", "extracting", "detecting", "events", "rules", "verified"]
_JOBS: dict[str, dict] = {}
_LOCK = threading.Lock()


def create(kind: str) -> str:
    jid = uuid.uuid4().hex[:12]
    with _LOCK:
        _JOBS[jid] = {"id": jid, "kind": kind, "stage": "uploaded", "progress": 0.0, "detail": "upload received", "status": "running",
                      "report_id": None, "error": None, "started": time.time(), "log": [{"t": 0.0, "stage": "uploaded", "detail": "upload received"}]}
    return jid


def update(jid: str, stage: str, progress: float, detail: str) -> None:
    with _LOCK:
        j = _JOBS[jid]
        if stage != j["stage"]:
            j["log"].append({"t": round(time.time() - j["started"], 2), "stage": stage, "detail": detail})
        j.update(stage=stage, progress=round(progress, 3), detail=detail)


def get(jid: str) -> dict | None:
    with _LOCK:
        j = _JOBS.get(jid)
        return dict(j) if j else None


def run(jid: str, fn: Callable[[Callable], dict]) -> None:
    def progress(stage: str, p: float, detail: str) -> None:
        update(jid, stage, p, detail)

    def target() -> None:
        try:
            report = fn(progress)
            (config.DATA / "reports" / f"{report['report_id']}.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
            with _LOCK:
                _JOBS[jid].update(stage="verified", progress=1.0, status="done", report_id=report["report_id"], detail="report sealed")
                _JOBS[jid]["log"].append({"t": round(time.time() - _JOBS[jid]["started"], 2), "stage": "verified", "detail": "report sealed"})
        except Exception as exc:  # surface the real failure, never fake a result
            traceback.print_exc()
            with _LOCK:
                _JOBS[jid].update(status="error", error=f"{type(exc).__name__}: {exc}", detail="judging failed")

    threading.Thread(target=target, daemon=True).start()
