"""Football AI judge: OpenCV colour segmentation + tracking, goal-zone events, conservative possession.

Controlled-setup assumptions (documented limitation): fixed camera, bright single-colour ball,
two contrasting shirt colours, goal zones calibrated as polygons in normalised image coordinates.
Only *observed* ball positions are used - nothing is interpolated into a verified event.
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from ..rules import football as rules
from ..rules.common import counted
from . import video
from .report import check, evidence_dir, finish, new_report, save_evidence

COLOR_PRESETS = {
    "red": [[[0, 120, 70], [8, 255, 255]], [[172, 120, 70], [180, 255, 255]]],
    "blue": [[[100, 120, 50], [128, 255, 255]]],
    "purple": [[[129, 80, 50], [160, 255, 255]]],
    "orange": [[[9, 150, 120], [18, 255, 255]]],
    "yellow": [[[22, 110, 150], [38, 255, 255]]],
    "teal": [[[80, 100, 50], [98, 255, 255]]],
    "white": [[[0, 0, 205], [180, 40, 255]]],
}

DEFAULT_CONFIG = {
    "sample_fps": 10,
    "work_width": 640,
    "teams": {"A": {"name": "Team A", "color": "red"}, "B": {"name": "Team B", "color": "blue"}},
    "ball": {"color": "yellow", "min_area": 10, "max_area": 1400, "min_circularity": 0.55},
    # polygons in normalised (x, y); the ball inside "A_attacks" scores for team A
    "goals": {
        "A_attacks": [[0.90, 0.30], [1.0, 0.30], [1.0, 0.70], [0.90, 0.70]],
        "B_attacks": [[0.0, 0.30], [0.10, 0.30], [0.10, 0.70], [0.0, 0.70]],
    },
    "players_per_team": 3,
    "regulation_seconds": 60,
    "tie_break": "golden_goal",
    "goal_min_frames": 3,
    "goal_cooldown_s": 3.0,
    "lost_frames": 4,
    "near_goal_margin": 0.10,
    "min_possession_frames": 3,
    "possession_scale": 0.45,
    "assignments": {},      # track id -> registered player name (host confirms in review)
    "penalties": {},        # team -> points (host-applied)
}


def _merge(base: dict, over: dict | None) -> dict:
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
    for k, v in (over or {}).items():
        out[k] = {**out[k], **v} if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def _ranges(spec: dict) -> list:
    return spec.get("ranges") or COLOR_PRESETS[spec.get("color", "red")]


def _in_ranges(hsv: np.ndarray, ranges: list) -> np.ndarray:
    mask = np.zeros(hsv.shape[:2], np.uint8)
    for lo, hi in ranges:
        mask |= cv2.inRange(hsv, np.array(lo, np.uint8), np.array(hi, np.uint8))
    return mask


class PlayerTracker:
    def __init__(self, team: str, max_players: int, max_dist: float, ttl: float):
        self.team, self.max_players, self.max_dist, self.ttl = team, max_players, max_dist, ttl
        self.tracks: dict[str, dict] = {}
        self.n = 0

    def update(self, t: float, blobs: list[dict]) -> list[dict]:
        pairs = sorted(
            ((math.hypot(b["cx"] - tr["cx"], b["cy"] - tr["cy"]), i, tid)
             for i, b in enumerate(blobs) for tid, tr in self.tracks.items()), key=lambda p: p[0])
        used_b, used_t, out = set(), set(), []
        for d, i, tid in pairs:
            if d > self.max_dist or i in used_b or tid in used_t:
                continue
            used_b.add(i), used_t.add(tid)
            self.tracks[tid].update(cx=blobs[i]["cx"], cy=blobs[i]["cy"], seen=t)
            out.append({**blobs[i], "id": tid, "team": self.team})
        for i, b in enumerate(blobs):
            if i in used_b:
                continue
            for tid in [k for k, v in self.tracks.items() if t - v["seen"] > self.ttl]:
                del self.tracks[tid]
            if len(self.tracks) >= self.max_players:
                continue  # more blobs than players: treat as noise (conservative)
            self.n += 1
            tid = f"{self.team}{self.n}"
            self.tracks[tid] = {"cx": b["cx"], "cy": b["cy"], "seen": t}
            out.append({**b, "id": tid, "team": self.team})
        return out


def _blobs(mask: np.ndarray, min_area: float, w: int, h: int) -> list[dict]:
    m = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 13), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for c in cnts:
        if cv2.contourArea(c) < min_area:
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        out.append({"cx": (x + bw / 2) / w, "cy": (y + bh / 2) / h, "bbox": [x / w, y / h, (x + bw) / w, (y + bh) / h]})
    return out


def _detect_ball(mask: np.ndarray, cfg: dict, w: int, h: int, pred: tuple | None) -> dict | None:
    m = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best, best_score = None, 0.0
    for c in cnts:
        a = cv2.contourArea(c)
        if a < cfg["min_area"] or a > cfg["max_area"]:
            continue
        p = cv2.arcLength(c, True)
        circ = 4 * math.pi * a / (p * p + 1e-6)
        if circ < cfg["min_circularity"]:
            continue
        (x, y), r = cv2.minEnclosingCircle(c)
        score = circ
        if pred is not None and math.hypot(x / w - pred[0], y / h - pred[1]) > 0.3:
            score *= 0.4
        if score > best_score:
            best, best_score = {"x": x / w, "y": y / h, "r": r / w, "score": round(circ, 3)}, score
    return best


def _inside(poly: np.ndarray, x: float, y: float) -> bool:
    return cv2.pointPolygonTest(poly, (float(x), float(y)), False) >= 0


def _dist_to_poly(poly: np.ndarray, x: float, y: float) -> float:
    return -cv2.pointPolygonTest(poly, (float(x), float(y)), True)  # >0 outside


def _rect_dist(px: float, py: float, box: list[float]) -> float:
    dx = max(box[0] - px, 0, px - box[2])
    dy = max(box[1] - py, 0, py - box[3])
    return math.hypot(dx, dy)


def analyse(video_path: Path, cfg: dict, progress) -> tuple[list[dict], list[dict]]:
    """Returns (samples, per-sample detections). samples: [{t, ball|None, players[]}]"""
    ball_cfg = cfg["ball"]
    ball_ranges = _ranges(ball_cfg)
    team_ranges = {k: _ranges(v) for k, v in cfg["teams"].items()}
    trackers: dict[str, PlayerTracker] = {}
    samples: list[dict] = []
    info = video.probe(video_path)
    total = max(1, int(info["duration_s"] * cfg["sample_fps"]))
    pred = None
    last_ball = None
    for n, t, frame in video.iter_samples(video_path, cfg["sample_fps"], cfg["work_width"]):
        h, w = frame.shape[:2]
        hsv = cv2.cvtColor(cv2.GaussianBlur(frame, (5, 5), 0), cv2.COLOR_BGR2HSV)
        ball = _detect_ball(_in_ranges(hsv, ball_ranges), ball_cfg, w, h, pred)
        if ball:
            if last_ball and n > 0:
                pred = (ball["x"] + (ball["x"] - last_ball["x"]), ball["y"] + (ball["y"] - last_ball["y"]))
            else:
                pred = (ball["x"], ball["y"])
            last_ball = ball
        else:
            pred = None if last_ball is None else pred
        players = []
        for team, rng in team_ranges.items():
            tr = trackers.setdefault(team, PlayerTracker(team, cfg["players_per_team"], 0.14, 3.0))
            blobs = _blobs(_in_ranges(hsv, rng), 0.0006 * w * h, w, h)
            players += tr.update(t, blobs)
        samples.append({"t": round(t, 3), "ball": ball, "players": players})
        if n % 10 == 0:
            progress("detecting", min(0.99, n / total), f"frame sample {n}/{total}")
    return samples, []


def find_goals(samples: list[dict], cfg: dict) -> list[dict]:
    fps = cfg["sample_fps"]
    min_f = cfg["goal_min_frames"]
    events: list[dict] = []
    for team, key in (("A", "A_attacks"), ("B", "B_attacks")):
        poly = np.array(cfg["goals"][key], np.float32)
        inside = [None if s["ball"] is None else _inside(poly, s["ball"]["x"], s["ball"]["y"]) for s in samples]
        i = 0
        last_t = -1e9
        while i < len(samples):
            if inside[i] is not True:
                i += 1
                continue
            j = i
            while j + 1 < len(samples) and inside[j + 1] is True:
                j += 1
            run = j - i + 1
            t0 = samples[i]["t"]
            entry_ok = any(inside[k] is False for k in range(max(0, i - int(fps)), i))
            if t0 - last_t >= cfg["goal_cooldown_s"]:
                scores = [samples[k]["ball"]["score"] for k in range(i, j + 1)]
                conf = round(min(1.0, run / (2 * min_f)) * 0.5 + (0.3 if entry_ok else 0.0) + 0.2 * (sum(scores) / len(scores)), 2)
                verified = run >= min_f and entry_ok and conf >= 0.75
                why = (f"Ball observed inside the {cfg['teams'][team]['name']} attacking goal zone for {run} consecutive observed samples "
                       f"({run / fps:.1f}s) after being seen outside it.")
                if not entry_ok:
                    why = "Ball first appears already inside the goal zone - its entry was not observed, so this goal is not verified."
                elif run < min_f:
                    why = f"Ball observed inside the goal zone for only {run} sample(s) (< {min_f} required) - possible touch, needs review."
                events.append({
                    "type": "GOAL", "rule_id": "FB-1", "team": team, "player": None, "points": 1,
                    "t_start": round(t0, 2), "t_end": round(samples[j]["t"], 2), "confidence": conf,
                    "status": "VERIFIED" if verified else "NEEDS_REVIEW", "reason": why,
                    "phase": "EXTENSION" if t0 > cfg["regulation_seconds"] else "REGULATION",
                    "ball_at": [round(samples[i]["ball"]["x"], 3), round(samples[i]["ball"]["y"], 3)],
                })
                last_t = t0
            i = j + 1
    # ball lost right next to a goal, moving toward it -> possible goal (never auto-verified)
    lost_f, margin = cfg["lost_frames"], cfg["near_goal_margin"]
    k = 0
    while k < len(samples) - 1:
        if samples[k]["ball"] and samples[k + 1]["ball"] is None:
            g = k + 1
            while g < len(samples) and samples[g]["ball"] is None:
                g += 1
            gap = g - (k + 1)
            if gap >= lost_f or g >= len(samples):
                bx, by = samples[k]["ball"]["x"], samples[k]["ball"]["y"]
                prev = samples[k - 2]["ball"] if k >= 2 and samples[k - 2]["ball"] else None
                for team, key in (("A", "A_attacks"), ("B", "B_attacks")):
                    poly = np.array(cfg["goals"][key], np.float32)
                    d = _dist_to_poly(poly, bx, by)
                    toward = prev is None or _dist_to_poly(poly, prev["x"], prev["y"]) > d
                    t = samples[k]["t"]
                    close_goal = any(e["type"] == "GOAL" and e["team"] == team and abs(e["t_start"] - t) < 2.0 for e in events)
                    if 0 < d <= margin and toward and not close_goal:
                        events.append({
                            "type": "POSSIBLE_GOAL", "rule_id": "FB-2", "team": team, "player": None, "points": 1,
                            "t_start": round(t, 2), "t_end": round(samples[min(g, len(samples) - 1)]["t"], 2), "confidence": 0.35,
                            "status": "NEEDS_REVIEW",
                            "reason": f"Ball was heading for the {cfg['teams'][team]['name']} goal and then not detected for {gap * 1.0 / cfg['sample_fps']:.1f}s. "
                                      "The AI cannot confirm the ball crossed the line - host review required.",
                            "phase": "EXTENSION" if t > cfg["regulation_seconds"] else "REGULATION",
                            "ball_at": [round(bx, 3), round(by, 3)],
                        })
            k = g
        else:
            k += 1
    events.sort(key=lambda e: e["t_start"])
    return events


def possession(samples: list[dict], cfg: dict) -> dict:
    fps = cfg["sample_fps"]
    dt = 1.0 / fps
    holder: list[str | None] = []
    for s in samples:
        b = s["ball"]
        if not b:
            holder.append("?")
            continue
        cands = []
        for p in s["players"]:
            size = max(p["bbox"][2] - p["bbox"][0], p["bbox"][3] - p["bbox"][1])
            d = _rect_dist(b["x"], b["y"], p["bbox"])
            if d <= cfg["possession_scale"] * size:
                cands.append((d / max(size, 1e-6), p["id"]))
        cands.sort()
        if not cands:
            holder.append(None)
        elif len(cands) > 1 and cands[0][1][0] != cands[1][1][0] and cands[1][0] - cands[0][0] < 0.15:
            holder.append(None)  # contested between teams -> nobody credited
        else:
            holder.append(cands[0][1])
    # persistence filter
    seg: list[dict] = []
    i = 0
    while i < len(holder):
        j = i
        while j + 1 < len(holder) and holder[j + 1] == holder[i]:
            j += 1
        if holder[i] not in (None, "?") and (j - i + 1) >= cfg["min_possession_frames"]:
            seg.append({"track": holder[i], "t_start": samples[i]["t"], "t_end": round(samples[j]["t"] + dt, 3), "frames": j - i + 1})
        i = j + 1
    by_track: dict[str, float] = {}
    for s_ in seg:
        by_track[s_["track"]] = by_track.get(s_["track"], 0.0) + s_["frames"] * dt
    team_sec = {"A": 0.0, "B": 0.0}
    for tid, sec in by_track.items():
        team_sec[tid[0]] += sec
    total = len(samples) * dt
    unknown = max(0.0, total - sum(team_sec.values()))
    return {"segments": seg, "by_track": {k: round(v, 2) for k, v in by_track.items()},
            "teams": rules.possession_summary({k: round(v, 2) for k, v in team_sec.items()}, unknown)}


def summarise(report: dict) -> dict:
    """Deterministic summary from events + metrics + host assignments (also used after host review)."""
    cfg = report["config"]
    tally = rules.tally(report["events"], cfg.get("penalties"))
    decision = rules.decide(tally, cfg.get("tie_break", "golden_goal"))
    pos = report["metrics"]["possession"]
    assign = cfg.get("assignments") or {}
    by_player: dict[str, float] = {}
    for tid, sec in pos["by_track"].items():
        by_player[assign.get(tid, f"Unassigned {tid}")] = by_player.get(assign.get(tid, f"Unassigned {tid}"), 0.0) + sec
    mvp = rules.pick_mvp(by_player)
    if mvp.get("mvp") and str(mvp["mvp"]).startswith("Unassigned"):
        mvp = {**mvp, "needs_host": True, "reason": "Longest possession belongs to an unassigned track - host must assign it to a registered player."}
    return {
        "score": tally["regulation"], "extension_goals": tally["extension"], "winner": decision["winner"],
        "decided_by": decision["decided_by"], "possession": pos["teams"], "possession_by_player": {k: round(v, 2) for k, v in by_player.items()},
        "mvp": mvp, "events_counted": sum(1 for e in report["events"] if e["type"] == "GOAL" and counted(e)),
    }


def _annotate(frame: np.ndarray, sample: dict, trail: list, cfg: dict, label: str) -> np.ndarray:
    h, w = frame.shape[:2]
    img = frame.copy()
    for key, colr in (("A_attacks", (60, 60, 230)), ("B_attacks", (230, 140, 40))):
        pts = np.array([[int(x * w), int(y * h)] for x, y in cfg["goals"][key]], np.int32)
        cv2.polylines(img, [pts], True, colr, 2)
    for p in sample["players"]:
        b = p["bbox"]
        cv2.rectangle(img, (int(b[0] * w), int(b[1] * h)), (int(b[2] * w), int(b[3] * h)), (60, 60, 230) if p["team"] == "A" else (230, 140, 40), 2)
        cv2.putText(img, p["id"], (int(b[0] * w), max(14, int(b[1] * h) - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    for a, b in zip(trail, trail[1:]):
        cv2.line(img, (int(a[0] * w), int(a[1] * h)), (int(b[0] * w), int(b[1] * h)), (0, 215, 255), 2)
    if sample["ball"]:
        cv2.circle(img, (int(sample["ball"]["x"] * w), int(sample["ball"]["y"] * h)), max(8, int(sample["ball"]["r"] * w * 1.8)), (0, 255, 255), 2)
        cv2.putText(img, "BALL", (int(sample["ball"]["x"] * w) + 10, int(sample["ball"]["y"] * h) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
    cv2.rectangle(img, (0, 0), (w, 30), (58, 36, 18), -1)
    cv2.putText(img, label, (10, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (235, 243, 247), 2)
    return img


def judge(video_path: Path, original_sha: str, original_name: str, user_cfg: dict | None, progress, report_id: str | None = None) -> dict:
    cfg = _merge(DEFAULT_CONFIG, user_cfg)
    info = video.probe(video_path)
    report = new_report("football", rules.RULE_VERSION, video_path, original_sha, original_name, info, cfg, report_id)
    rid = report["report_id"]
    progress("extracting", 0.02, "decoding video and sampling frames")
    samples, _ = analyse(video_path, cfg, progress)
    progress("events", 0.0, "detecting goals and possession")
    events = find_goals(samples, cfg)
    pos = possession(samples, cfg)
    observed = sum(1 for s in samples if s["ball"])
    report["metrics"] = {
        "samples": len(samples), "ball_observed_samples": observed,
        "ball_observed_ratio": round(observed / max(len(samples), 1), 3), "possession": pos, "tracks": sorted(pos["by_track"]),
        "all_tracks": sorted({p["id"] for s in samples for p in s["players"]}),
    }
    for e in pos["segments"]:  # informational possession events (no points)
        events.append({"type": "POSSESSION_SEGMENT", "rule_id": "FB-5", "team": e["track"][0], "player": e["track"], "points": 0,
                       "t_start": e["t_start"], "t_end": e["t_end"], "confidence": None, "status": "VERIFIED",
                       "reason": f"Ball observed within reach of {e['track']} for {e['frames'] / cfg['sample_fps']:.1f}s.", "phase": "REGULATION"})
    events.sort(key=lambda e: (e["t_start"], e["type"]))
    for n, e in enumerate(events):
        e["id"] = f"{e['type'].lower()}-{n + 1}"
        e["review"] = None
        e["evidence"] = []
    # evidence thumbnails for scoring-relevant events
    by_t = {s["t"]: s for s in samples}
    ts = sorted(by_t)
    for e in events:
        if e["type"] == "POSSESSION_SEGMENT":
            continue
        for off, tag in ((-0.5, "before"), (0.0, "moment"), (0.5, "after")):
            t = max(0.0, e["t_start"] + off)
            nearest = min(ts, key=lambda x: abs(x - t)) if ts else None
            if nearest is None:
                continue
            frame = video.frame_at(video_path, nearest)
            if frame is None:
                continue
            trail = [s["ball"] and (s["ball"]["x"], s["ball"]["y"]) for s in samples if nearest - 1.0 <= s["t"] <= nearest and s["ball"]]
            img = _annotate(frame, by_t[nearest], trail, cfg, f"{e['type']} {tag}  t={nearest:.1f}s  rule {e['rule_id']}  {e['status']}")
            url = save_evidence(rid, f"{e['id']}-{tag}.jpg", img)
            e["evidence"].append({"t": nearest, "kind": tag, "thumb": url,
                                  "note": f"{tag}: ball {'observed' if by_t[nearest]['ball'] else 'NOT observed'} at this sample"})
    report["events"] = events
    report["overlay"] = [{"t": s["t"], "ball": s["ball"] and [round(s["ball"]["x"], 4), round(s["ball"]["y"], 4), round(s["ball"]["r"], 4)],
                          "p": [[p["id"], p["team"], *[round(v, 4) for v in p["bbox"]]] for p in s["players"]]} for s in samples]
    report["summary"] = summarise(report)
    check(report, "video_decodable", len(samples) > 0, f"{len(samples)} frame samples analysed at {cfg['sample_fps']} fps")
    check(report, "ball_visibility", report["metrics"]["ball_observed_ratio"] >= 0.3,
          f"ball observed in {report['metrics']['ball_observed_ratio'] * 100:.0f}% of samples")
    check(report, "goal_zones_calibrated", all(len(cfg["goals"][k]) >= 3 for k in cfg["goals"]), "two goal polygons defined")
    check(report, "no_unverified_points", all(e["status"] == "VERIFIED" for e in events if e["type"] == "GOAL" and counted(e)), "only VERIFIED goals counted")
    report["limitations"] = [
        "Controlled setup: fixed camera, single-colour ball, contrasting shirt colours, calibrated goal polygons.",
        "Players are colour-blob tracks; shirt numbers are not read. The host assigns tracks to registered players.",
        "Unobserved ball time is reported as unknown possession and is never credited to a team.",
    ]
    progress("rules", 1.0, "rules applied")
    return finish(report)
