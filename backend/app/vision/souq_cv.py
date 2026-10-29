"""Souq Signal AI judge: product-card recognition (ArUco markers) + speech transcription,
agreement checking, budget maths. Gemini only transcribes; the rules decide.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import numpy as np

from ..rules import souq as rules
from ..rules.common import counted
from . import markers, speech, video
from .report import check, finish, new_report, save_evidence

DEFAULT_CONFIG = {
    "sample_fps": 5,
    "work_width": 1280,
    "mission": {"requested": ["dates", "coffee", "pottery"], "budget": 60},
    "min_display_s": 0.8,
    "rejoin_gap_s": 2.0,
    "transcript_override": None,   # host-entered segments [{start,end,text}] if transcription is unavailable
}


def presentations(dets: list[tuple[float, list[dict]]], dt: float, min_s: float, gap_s: float) -> list[dict]:
    """Merge per-frame card sightings into presentation intervals (same card; gaps <= gap_s are one show)."""
    per_card: dict[int, list[float]] = {}
    for t, ds in dets:
        for d in ds:
            if d["id"] in rules.MARKER_TO_PRODUCT:
                per_card.setdefault(d["id"], []).append(t)
    out = []
    for cid, ts in per_card.items():
        ts.sort()
        start = prev = ts[0]
        for t in ts[1:] + [None]:
            if t is None or t - prev > gap_s:
                if prev - start + dt >= min_s:
                    out.append({"product": rules.MARKER_TO_PRODUCT[cid], "card_id": cid, "t_first": round(start, 2), "t_last": round(prev + dt, 2)})
                if t is not None:
                    start = t
            if t is not None:
                prev = t
    out.sort(key=lambda p: p["t_first"])
    return out


def _annotate(frame: np.ndarray, dets: list[dict], label: str) -> np.ndarray:
    img = frame.copy()
    for d in dets:
        pid = rules.MARKER_TO_PRODUCT.get(d["id"])
        if not pid:
            continue
        pts = d["corners"].astype(np.int32)
        cv2.polylines(img, [pts], True, (160, 128, 22), 4)
        info = rules.CATALOG[pid]
        cv2.putText(img, f"{info['en']} AED {info['price']}", (int(pts[:, 0].min()), max(18, int(pts[:, 1].min()) - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (107, 163, 198), 2)
    cv2.rectangle(img, (0, 0), (img.shape[1], 30), (58, 36, 18), -1)
    cv2.putText(img, label, (10, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (235, 243, 247), 2)
    return img


def judge(video_path: Path, original_sha: str, original_name: str, user_cfg: dict | None, progress, report_id: str | None = None) -> dict:
    cfg = {**DEFAULT_CONFIG, **(user_cfg or {})}
    cfg["mission"] = {**DEFAULT_CONFIG["mission"], **(cfg.get("mission") or {})}
    info = video.probe(video_path)
    report = new_report("souq", rules.RULE_VERSION, video_path, original_sha, original_name, info, cfg, report_id)
    rid = report["report_id"]
    progress("extracting", 0.02, "sampling frames and extracting audio")
    dets: list[tuple[float, list[dict]]] = []
    total = max(1, int(info["duration_s"] * cfg["sample_fps"]))
    for n, t, frame in video.iter_samples(video_path, cfg["sample_fps"], cfg["work_width"]):
        dets.append((t, markers.detect(frame)))
        if n % 5 == 0:
            progress("detecting", min(0.9, n / total), f"card scan {n}/{total}")
    dt = 1.0 / cfg["sample_fps"]
    shows = presentations(dets, dt, cfg["min_display_s"], cfg["rejoin_gap_s"])

    progress("transcribing", 0.0, "transcribing speech")
    tr: dict
    ov = cfg.get("transcript_override")
    if isinstance(ov, dict):  # explicit status (used to test the "transcription unavailable" path)
        tr = {"status": ov.get("status", "UNAVAILABLE"), "source": "override", "segments": ov.get("segments", []), "reason": ov.get("reason", "override")}
    elif ov is not None:
        tr = {"status": "OK", "source": "host_entered", "segments": ov}
    elif info["has_audio"]:
        with tempfile.TemporaryDirectory() as td:
            wav = Path(td) / "a.wav"
            tr = speech.transcribe(wav) if video.extract_audio(video_path, wav) else {"status": "UNAVAILABLE", "source": None, "segments": [], "reason": "audio extraction failed"}
    else:
        tr = {"status": "NO_AUDIO", "source": None, "segments": [], "reason": "video has no audio track"}
    transcript_ok = tr["status"] in ("OK", "NO_SPEECH")
    mentions = rules.find_mentions(tr["segments"])
    progress("events", 0.0, "applying Souq rules")
    ev = rules.evaluate(cfg["mission"], shows, mentions, transcript_ok)
    events = ev["events"]
    by_t = {t: d for t, d in dets}
    ts = sorted(by_t)
    for e in events:
        e["evidence"] = []
        if ts:
            nearest = min(ts, key=lambda x: abs(x - e["t_start"]))
            frame = video.frame_at(video_path, nearest)
            if frame is not None:
                f = cv2.resize(frame, (cfg["work_width"], int(frame.shape[0] * cfg["work_width"] / frame.shape[1]))) if frame.shape[1] > cfg["work_width"] else frame
                img = _annotate(f, by_t[nearest], f"{e['type']}  t={nearest:.1f}s  rule {e['rule_id']}  {e['status']}")
                e["evidence"].append({"t": nearest, "kind": "visual", "thumb": save_evidence(rid, f"{e['id']}.jpg", img), "note": "Detected product cards in this frame"})
        if e.get("transcript"):
            e["evidence"].append({"t": e["t_start"], "kind": "audio", "thumb": None, "note": f"Transcript: “{e['transcript']}”"})
    report["events"] = events
    report["metrics"] = {"presentations": shows, "mentions": mentions, "transcript": tr, "mission": cfg["mission"],
                         "catalog": {k: {"en": v["en"], "ar": v["ar"], "price": v["price"]} for k, v in rules.CATALOG.items()}}
    report["overlay"] = [{"t": t, "cards": [[d["id"], *[round(float(v), 1) for v in d["corners"].flatten()]] for d in ds if d["id"] in rules.MARKER_TO_PRODUCT]}
                         for t, ds in dets if any(d["id"] in rules.MARKER_TO_PRODUCT for d in ds)]
    finish_t = max([s["t_last"] for s in shows], default=None)
    report["summary"] = {**summarise(report), "spend": ev["spend"], "budget": cfg["mission"]["budget"], "finish_s": finish_t, "selected": ev["selected"],
                         "remaining_budget": cfg["mission"]["budget"] - ev["spend"]}
    check(report, "video_decodable", len(dets) > 0, f"{len(dets)} frame samples analysed")
    check(report, "cards_detected", bool(shows), f"{len(shows)} card presentation(s) detected")
    check(report, "transcript_available", transcript_ok, f"{tr['status']} ({tr.get('source') or tr.get('reason')})")
    check(report, "budget_arithmetic", ev["spend"] == sum(rules.CATALOG[p]["price"] for p in ev["selected"]), "expenditure = sum of fixed card prices")
    report["limitations"] = [
        "Cards are recognised by printed ArUco markers, not by product artwork.",
        "Transcript timing from the speech model is approximate (+/- ~1 s); the matching window is 5 s.",
        "If transcription is unavailable, spoken-match points stay NEEDS_REVIEW until the host decides.",
    ]
    progress("rules", 1.0, "rules applied")
    return finish(report)


def summarise(report: dict) -> dict:
    prev = report.get("summary", {})
    return {**prev, "score": {"total": rules.score(report["events"])}}
