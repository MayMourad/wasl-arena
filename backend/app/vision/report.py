"""Judging report assembly shared by all three games."""
from __future__ import annotations

import datetime as dt
import shutil
import uuid
from pathlib import Path

from .. import config, integrity
from . import video

JUDGE = {"name": "WASL AI Referee", "version": "1.0.0"}


def new_report(game: str, rule_version: str, source_path: Path, original_sha: str, original_name: str,
               info: dict, cfg: dict, report_id: str | None = None) -> dict:
    rid = report_id or uuid.uuid4().hex[:12]
    return {
        "report_id": rid,
        "game": game,
        "rule_version": rule_version,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "judge": JUDGE,
        "source": {
            "filename": original_name,
            "sha256_original": original_sha,
            "sha256_analyzed": integrity.sha256_file(source_path),
            "analyzed_file": source_path.name,
            **info,
        },
        "config": cfg,
        "events": [],
        "overlay": [],
        "metrics": {},
        "summary": {},
        "validation": {"checks": []},
        "limitations": [],
        "audit": [],
    }


def check(report: dict, name: str, ok: bool, detail: str) -> None:
    report["validation"]["checks"].append({"name": name, "ok": bool(ok), "detail": detail})


def finish(report: dict) -> dict:
    checks = report["validation"]["checks"]
    report["validation"]["passed"] = all(c["ok"] for c in checks)
    report["summary"]["needs_review"] = sum(1 for e in report["events"] if e.get("status") == "NEEDS_REVIEW")
    return integrity.seal(report)


def evidence_dir(report_id: str) -> Path:
    d = config.DATA / "evidence" / report_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_evidence(report_id: str, name: str, frame) -> str:
    video.save_jpg(frame, evidence_dir(report_id) / name)
    return f"/api/evidence/{report_id}/{name}"


def clean(report_id: str) -> None:
    shutil.rmtree(config.DATA / "evidence" / report_id, ignore_errors=True)
