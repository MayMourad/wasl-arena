"""Falaj Flow AI judge: reads the physical 5x5 board from video, rebuilds the channel network as a
graph and validates the water route with the deterministic rule engine.

Board: 4 corner ArUco markers (ids 0-3) give a homography to board cell coordinates. Each channel
tile carries one ArUco marker (ids 10-25): its id gives the tile type, its in-plane rotation gives
the tile rotation (90 degree steps). Nothing is assumed - a tile exists only if its marker is seen
in a stable state for >= stable_seconds.
"""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from ..rules import falaj as rules
from ..rules.common import counted
from . import markers, video
from .report import check, finish, new_report, save_evidence

CORNER_IDS = {0: (-0.6, -0.6), 1: (5.6, -0.6), 2: (5.6, 5.6), 3: (-0.6, 5.6)}  # canonical cell units (TL,TR,BR,BL)

DEFAULT_CONFIG = {
    "sample_fps": 4,
    "work_width": 1280,
    "layout": "oasis-1",
    "round_seconds": rules.ROUND_SECONDS,
    "round_start_s": 0.0,
    "stable_seconds": 1.0,
}


def _homography(dets_by_sample: list[list[dict]]) -> np.ndarray | None:
    hs = []
    for dets in dets_by_sample:
        found = {d["id"]: d["center"] for d in dets if d["id"] in CORNER_IDS}
        if len(found) == 4:
            src = np.array([found[i] for i in (0, 1, 2, 3)], np.float32)
            dst = np.array([CORNER_IDS[i] for i in (0, 1, 2, 3)], np.float32)
            hs.append(cv2.getPerspectiveTransform(src, dst))
    if not hs:
        return None
    H = np.median(np.stack([h / h[2, 2] for h in hs]), axis=0)
    return H


def _project(H: np.ndarray, pts: np.ndarray) -> np.ndarray:
    p = cv2.perspectiveTransform(pts.reshape(-1, 1, 2).astype(np.float32), H)
    return p.reshape(-1, 2)


def read_tiles(H: np.ndarray, dets: list[dict], size: int) -> tuple[dict, list[str]]:
    tiles: dict[tuple[int, int], dict] = {}
    issues: list[str] = []
    for d in dets:
        if d["id"] not in rules.TILE_IDS:
            continue
        c = _project(H, d["corners"])
        cx, cy = c.mean(axis=0)
        cell = (int(math.floor(cy)), int(math.floor(cx)))
        if not (0 <= cell[0] < size and 0 <= cell[1] < size):
            issues.append(f"tile marker {d['id']} outside the board grid")
            continue
        v = c[1] - c[0]  # TL -> TR in board plane; +x right, +y down
        angle = math.degrees(math.atan2(v[1], v[0]))
        rot = int(round(angle / 90.0)) % 4
        if cell in tiles:
            issues.append(f"two tile markers in cell {list(cell)}")
            continue
        tiles[cell] = {"type": rules.TILE_IDS[d["id"]], "rot": rot, "id": d["id"]}
    return tiles, issues


def _signature(tiles: dict) -> tuple:
    return tuple(sorted((c, t["id"], t["rot"]) for c, t in tiles.items()))


def _stable_states(timeline: list[dict], dt: float, stable_s: float) -> list[dict]:
    runs = []
    i = 0
    while i < len(timeline):
        j = i
        while j + 1 < len(timeline) and timeline[j + 1]["sig"] == timeline[i]["sig"]:
            j += 1
        dur = timeline[j]["t"] - timeline[i]["t"] + dt
        if dur >= stable_s - 1e-9:
            runs.append({"t_start": timeline[i]["t"], "t_end": timeline[j]["t"] + dt, "tiles": timeline[i]["tiles"], "sig": timeline[i]["sig"],
                         "issues": timeline[i]["issues"]})
        i = j + 1
    merged: list[dict] = []
    for r in runs:  # merge equal states separated only by short blips (hand occlusion)
        if merged and merged[-1]["sig"] == r["sig"]:
            merged[-1]["t_end"] = r["t_end"]
        else:
            merged.append(r)
    return merged


def _draw_board(frame: np.ndarray, H: np.ndarray, layout: dict, tiles: dict, analysis: dict, label: str) -> np.ndarray:
    img = frame.copy()
    Hi = np.linalg.inv(H)

    def pj(pts):
        return [tuple(int(v) for v in p) for p in _project(Hi, np.array(pts, np.float32))]

    for k in range(6):
        cv2.polylines(img, [np.array(pj([(k, 0), (k, 5)]), np.int32)], False, (200, 200, 200), 1)
        cv2.polylines(img, [np.array(pj([(0, k), (5, k)]), np.int32)], False, (200, 200, 200), 1)
    for (r, c), t in tiles.items():
        q = np.array(pj([(c, r), (c + 1, r), (c + 1, r + 1), (c, r + 1)]), np.int32)
        reached = [r, c] in analysis["reached_tiles"]
        cv2.polylines(img, [q], True, (160, 128, 22) if reached else (120, 120, 120), 3)
        x, y = pj([(c + 0.5, r + 0.5)])[0]
        cv2.putText(img, f"{t['type'][:3]}{t['rot'] * 90}", (x - 28, y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    for e in analysis["edges"]:
        a = pj([(e["from"][1] + 0.5, e["from"][0] + 0.5)])[0]
        b = pj([(e["to"][1] + 0.5, e["to"][0] + 0.5)])[0]
        cv2.line(img, a, b, (200, 170, 20), 6)
    for d in layout["destinations"]:
        ok = d in analysis["reached_destinations"]
        cv2.circle(img, pj([(d[1] + 0.5, d[0] + 0.5)])[0], 18, (107, 163, 198) if ok else (57, 45, 185), 4)
    for lk in analysis["leaks"]:
        dr, dc = rules.DELTA[{"north": 0, "east": 1, "south": 2, "west": 3}[lk["side"]]]
        p = pj([(lk["cell"][1] + 0.5 + dc * 0.5, lk["cell"][0] + 0.5 + dr * 0.5)])[0]
        cv2.circle(img, p, 14, (57, 45, 185), -1)
    cv2.rectangle(img, (0, 0), (img.shape[1], 30), (58, 36, 18), -1)
    cv2.putText(img, label, (10, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (235, 243, 247), 2)
    return img


def judge(video_path: Path, original_sha: str, original_name: str, user_cfg: dict | None, progress, report_id: str | None = None) -> dict:
    cfg = {**DEFAULT_CONFIG, **(user_cfg or {})}
    layout = rules.LAYOUTS[cfg["layout"]]
    info = video.probe(video_path)
    report = new_report("falaj", rules.RULE_VERSION, video_path, original_sha, original_name, info, cfg, report_id)
    rid = report["report_id"]
    progress("extracting", 0.02, "sampling frames and finding printed markers")
    dets_all: list[tuple[float, list[dict]]] = []
    total = max(1, int(info["duration_s"] * cfg["sample_fps"]))
    for n, t, frame in video.iter_samples(video_path, cfg["sample_fps"], cfg["work_width"]):
        dets_all.append((t, markers.detect(frame)))
        if n % 5 == 0:
            progress("detecting", min(0.99, n / total), f"marker scan {n}/{total}")
    dt = 1.0 / cfg["sample_fps"]
    H = _homography([d for _, d in dets_all])
    check(report, "board_calibrated", H is not None, "all four corner markers seen together" if H is not None else "corner markers 0-3 never all visible")
    if H is None:
        report["summary"] = {"error": "Board could not be calibrated", "score": None}
        report["limitations"].append("Corner markers not visible - cannot reconstruct the board.")
        return finish(report)

    timeline = []
    for t, dets in dets_all:
        tiles, issues = read_tiles(H, dets, layout["size"])
        timeline.append({"t": t, "tiles": tiles, "sig": _signature(tiles), "issues": issues})
    states = _stable_states(timeline, dt, cfg["stable_seconds"])
    progress("events", 0.5, "validating networks")
    round_end = cfg["round_start_s"] + cfg["round_seconds"]
    snapshots = []
    for s in states:
        an = rules.analyze(layout, s["tiles"])
        sc = rules.score_round(an, None)
        snapshots.append({"t_start": round(s["t_start"], 2), "t_end": round(s["t_end"], 2),
                          "tiles": [{"cell": list(c), **t} for c, t in sorted(s["tiles"].items())], "analysis": an, "score_no_bonus": sc["total"],
                          "issues": s["issues"]})
    report["metrics"] = {"layout": layout, "snapshots": snapshots, "samples": len(dets_all)}
    valid = [i for i, s in enumerate(states) if s["t_start"] <= round_end]
    events: list[dict] = []
    if not valid:
        report["summary"] = {"score": {"total": 0}, "note": "No stable board state detected"}
        check(report, "stable_state_found", False, "no board state held for the required stable time")
        report["limitations"].append("No stable tile arrangement was observed.")
        return finish(report)
    fi = valid[-1]
    final, fsnap = states[fi], snapshots[fi]
    an = fsnap["analysis"]
    completion = None
    if an["all_connected"]:
        k = fi
        while k - 1 >= 0 and snapshots[k - 1]["analysis"]["all_connected"] and states[k - 1]["t_start"] <= round_end:
            k -= 1
        completion = round(states[k]["t_start"] - cfg["round_start_s"], 2)
    sc = rules.score_round(an, completion)
    certain = (final["t_end"] - final["t_start"]) >= cfg["stable_seconds"] and not final["issues"] and not an["illegal_placements"]

    def evidence(state, snap, tag):
        frame = video.frame_at(video_path, (state["t_start"] + state["t_end"]) / 2 - dt / 2)
        out = []
        if frame is not None:
            f = cv2.resize(frame, (cfg["work_width"], int(frame.shape[0] * cfg["work_width"] / frame.shape[1]))) if frame.shape[1] > cfg["work_width"] else frame
            img = _draw_board(f, H, layout, state["tiles"], snap["analysis"], f"{tag}  stable {state['t_start']:.1f}-{state['t_end']:.1f}s")
            t_mid = round((state["t_start"] + state["t_end"]) / 2, 2)
            out.append({"t": t_mid, "kind": "board", "thumb": save_evidence(rid, f"{tag.lower().replace(' ', '-')}.jpg", img),
                        "note": "Board with detected tiles, water path (teal) and leaks (red)"})
        return out

    final_evidence = evidence(final, fsnap, "Final board")
    n = 0
    for d in layout["destinations"]:
        n += 1
        ok = d in an["reached_destinations"]
        if ok:
            events.append({"id": f"dest-{n}", "type": "DEST_CONNECTED", "rule_id": "FF-1", "team": None, "player": None, "points": rules.POINTS_DEST,
                           "t_start": completion if completion is not None else round(final["t_start"], 2), "t_end": round(final["t_end"], 2),
                           "confidence": None, "status": "VERIFIED" if certain else "NEEDS_REVIEW",
                           "reason": f"Water traced from the well through matching open tile sides to farm {d}.",
                           "cell": d, "review": None, "evidence": final_evidence})
    for lk in an["leaks"]:
        n += 1
        events.append({"id": f"leak-{n}", "type": "LEAK", "rule_id": "FF-2", "team": None, "player": None, "points": rules.POINTS_LEAK,
                       "t_start": round(final["t_start"], 2), "t_end": round(final["t_end"], 2), "confidence": None,
                       "status": "VERIFIED" if certain else "NEEDS_REVIEW",
                       "reason": f"Leak at cell {lk['cell']} ({lk['side']} side): {lk['reason']}.", "cell": lk["cell"], "review": None, "evidence": final_evidence})
    if sc["time_bonus"]:
        n += 1
        events.append({"id": f"bonus-{n}", "type": "TIME_BONUS", "rule_id": "FF-3", "team": None, "player": None, "points": sc["time_bonus"],
                       "t_start": completion, "t_end": completion, "confidence": None, "status": "VERIFIED" if certain else "NEEDS_REVIEW",
                       "reason": f"All three farms watered after {completion:.1f}s (round {cfg['round_seconds']}s).", "review": None, "evidence": final_evidence})
    for ill in an["illegal_placements"] + [{"cell": None, "reason": i} for i in final["issues"]]:
        n += 1
        events.append({"id": f"issue-{n}", "type": "PLACEMENT_ISSUE", "rule_id": "FF-0", "team": None, "player": None, "points": 0,
                       "t_start": round(final["t_start"], 2), "t_end": round(final["t_end"], 2), "confidence": None, "status": "NEEDS_REVIEW",
                       "reason": f"Placement issue: {ill['reason']}", "cell": ill["cell"], "review": None, "evidence": final_evidence})
    report["events"] = events
    report["summary"] = summarise_from(report)
    report["summary"]["completion_s"] = completion
    report["summary"]["network_size"] = an["network_size"]
    report["summary"]["final_state_index"] = fi
    check(report, "stable_state_found", True, f"{len(states)} stable board states; final stable for {final['t_end'] - final['t_start']:.1f}s")
    check(report, "no_marker_conflicts", not final["issues"], "no duplicate / off-board tile markers" if not final["issues"] else "; ".join(final["issues"]))
    check(report, "no_illegal_placements", not an["illegal_placements"], "tiles only on playable cells")
    report["limitations"] = [
        "Requires the printed WASL board with four corner markers fully visible at least once.",
        "Tile type comes from the printed marker id; a damaged or hidden marker is treated as no tile.",
        "A tile arrangement must hold for 1 s to count - brief hand occlusion is ignored, not scored.",
    ]
    progress("rules", 1.0, "rules applied")
    return finish(report)


def summarise_from(report: dict) -> dict:
    ev = report["events"]
    total = sum(e["points"] for e in ev if counted(e))
    d = sum(1 for e in ev if e["type"] == "DEST_CONNECTED" and counted(e))
    lk = sum(1 for e in ev if e["type"] == "LEAK" and counted(e))
    bonus = sum(e["points"] for e in ev if e["type"] == "TIME_BONUS" and counted(e))
    return {"score": {"total": total, "destinations": d, "leaks": lk, "time_bonus": bonus}}


def summarise(report: dict) -> dict:
    prev = report.get("summary", {})
    new = summarise_from(report)
    return {**prev, **new}
