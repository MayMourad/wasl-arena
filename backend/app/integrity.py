"""Evidence integrity: source hashes, canonical report hashes and HMAC signatures.

A report is sealed by the AI judge. The app (or any verifier holding the signing key)
can detect any later modification of the report body.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

from . import config


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _body(report: dict) -> dict:
    return {k: v for k, v in report.items() if k not in ("integrity", "host_integrity", "ai_integrity")}


def _sign(digest: str) -> str:
    return hmac.new(config.SIGNING_KEY.encode(), digest.encode(), hashlib.sha256).hexdigest()


def seal(report: dict, field: str = "integrity") -> dict:
    """Attach hash + signature of the report body (everything except integrity fields)."""
    digest = sha256_bytes(canonical(_body(report)))
    report[field] = {
        "algorithm": "SHA-256 / HMAC-SHA256",
        "report_sha256": digest,
        "signature": _sign(digest),
        "key_id": config.SIGNING_KEY_ID,
    }
    return report


def verify(report: dict, field: str = "integrity") -> dict:
    """Return {ok, reasons}. ok is True only when hash and signature both match."""
    block = report.get(field)
    if not block:
        return {"ok": False, "reasons": ["missing integrity block"]}
    reasons = []
    digest = sha256_bytes(canonical(_body(report)))
    if digest != block.get("report_sha256"):
        reasons.append("report body hash does not match (report was modified)")
    if not hmac.compare_digest(_sign(block.get("report_sha256", "")), block.get("signature", "")):
        reasons.append("signature invalid (not produced by this AI judge key)")
    return {"ok": not reasons, "reasons": reasons, "key_id": block.get("key_id")}
