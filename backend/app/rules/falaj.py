"""Falaj Flow rule engine (deterministic graph validation).  Rule set WASL-FALAJ-R1.0

The 5x5 board is printed with a well (water source), three farms (destinations) and rocks.
Players place channel tiles; the AI reads each tile (type + rotation) and this engine traces
the water from the well through open, matching tile sides.

FF-1  Each destination reached by water: +3.
FF-2  Each leak (water reaches an open tile end that has no matching neighbour): -1.
FF-3  Time bonus, only when all three farms are watered: <=45 s +2, <=70 s +1, else 0 (round = 90 s).
FF-4  Tie-break: shortest valid network (fewest water-carrying tiles), then earliest completion time.
"""
from __future__ import annotations

from collections import deque

RULE_VERSION = "WASL-FALAJ-R1.0"
N, E, S, W = 0, 1, 2, 3
DELTA = {N: (-1, 0), E: (0, 1), S: (1, 0), W: (0, -1)}
SIDE_NAME = {N: "north", E: "east", S: "south", W: "west"}
BASE_OPEN = {"STRAIGHT": {N, S}, "ELBOW": {N, E}, "TEE": {N, E, S}, "CROSS": {N, E, S, W}}
ROUND_SECONDS = 90
POINTS_DEST, POINTS_LEAK = 3, -1

# Marker id -> tile type (printed tile sheet, see tools/make_printables.py)
TILE_IDS: dict[int, str] = {}
for _i in range(10, 16):
    TILE_IDS[_i] = "STRAIGHT"
for _i in range(16, 22):
    TILE_IDS[_i] = "ELBOW"
for _i in range(22, 25):
    TILE_IDS[_i] = "TEE"
TILE_IDS[25] = "CROSS"

LAYOUTS = {
    "oasis-1": {
        "id": "oasis-1",
        "name": "Oasis crossing",
        "size": 5,
        "source": {"cell": [2, 0], "side": E},
        "destinations": [[0, 4], [2, 4], [4, 4]],
        "rocks": [[2, 2]],
    }
}


def open_sides(ttype: str, rot: int) -> set[int]:
    return {(s + rot) % 4 for s in BASE_OPEN[ttype]}


def analyze(layout: dict, tiles: dict[tuple[int, int], dict]) -> dict:
    """tiles: {(row, col): {"type": str, "rot": int, "id": int}} -> network analysis."""
    size = layout["size"]
    src = tuple(layout["source"]["cell"])
    dests = {tuple(d) for d in layout["destinations"]}
    rocks = {tuple(r) for r in layout["rocks"]}
    illegal = [
        {"cell": list(c), "reason": "tile placed on a printed well, farm or rock cell"}
        for c in tiles
        if c == src or c in dests or c in rocks
    ]
    reached: set[tuple[int, int]] = set()
    reached_dests: set[tuple[int, int]] = set()
    edges: list[dict] = []
    leaks: dict[tuple, dict] = {}
    queue: deque = deque()

    def flow(frm: tuple[int, int], side: int) -> None:
        dr, dc = DELTA[side]
        nxt = (frm[0] + dr, frm[1] + dc)
        opp = (side + 2) % 4
        key = (frm, side)
        if not (0 <= nxt[0] < size and 0 <= nxt[1] < size):
            leaks[key] = {"cell": list(frm), "side": SIDE_NAME[side], "reason": "water runs off the board edge"}
            return
        if nxt in rocks:
            leaks[key] = {"cell": list(frm), "side": SIDE_NAME[side], "reason": "channel blocked by a rock"}
            return
        if nxt in dests:
            edges.append({"from": list(frm), "to": list(nxt)})
            reached_dests.add(nxt)
            return
        if nxt == src:
            sdr, sdc = DELTA[layout["source"]["side"]]
            if (src[0] + sdr, src[1] + sdc) == frm:
                return  # this is the well's own outlet: the open side facing the well is the inlet, not a leak
            leaks[key] = {"cell": list(frm), "side": SIDE_NAME[side], "reason": "channel points into the closed side of the well"}
            return
        tile = tiles.get(nxt)
        if tile is None:
            leaks[key] = {"cell": list(frm), "side": SIDE_NAME[side], "reason": "open channel end, no tile placed"}
            return
        if opp in open_sides(tile["type"], tile["rot"]):
            edges.append({"from": list(frm), "to": list(nxt)})
            if nxt not in reached:
                reached.add(nxt)
                queue.append(nxt)
        else:
            leaks[key] = {"cell": list(frm), "side": SIDE_NAME[side], "reason": "neighbouring tile does not connect (closed side)"}

    flow(src, layout["source"]["side"])
    while queue:
        cell = queue.popleft()
        t = tiles[cell]
        for side in sorted(open_sides(t["type"], t["rot"])):
            flow(cell, side)

    return {
        "reached_tiles": sorted([list(c) for c in reached]),
        "reached_destinations": sorted([list(d) for d in reached_dests]),
        "destinations_total": len(dests),
        "leaks": list(leaks.values()),
        "edges": edges,
        "network_size": len(reached),
        "illegal_placements": illegal,
        "all_connected": len(reached_dests) == len(dests),
    }


def time_bonus(all_connected: bool, completion_s: float | None) -> int:
    if not all_connected or completion_s is None:
        return 0
    if completion_s <= 45:
        return 2
    if completion_s <= 70:
        return 1
    return 0


def score_round(analysis: dict, completion_s: float | None) -> dict:
    d = len(analysis["reached_destinations"])
    lk = len(analysis["leaks"])
    bonus = time_bonus(analysis["all_connected"], completion_s)
    return {
        "destinations_points": d * POINTS_DEST,
        "leak_points": lk * POINTS_LEAK,
        "time_bonus": bonus,
        "total": d * POINTS_DEST + lk * POINTS_LEAK + bonus,
    }


def rank_key(total: int, analysis: dict, completion_s: float | None) -> tuple:
    """Sort ascending: higher score first, then shorter valid network, then earlier completion."""
    size = analysis["network_size"] if analysis["all_connected"] else 10**6
    return (-total, size, completion_s if completion_s is not None else 10**6)
