"""Football rule engine (deterministic).  Rule set WASL-FOOTBALL-R1.0

FB-1  Valid goal: +1 for the attacking team. A goal needs a VERIFIED event.
FB-2  Invalid / unsupported / NEEDS_REVIEW goal: 0 until the host accepts it.
FB-3  Winner: highest verified regulation score.
FB-4  Tie: golden-goal extension (configurable) - first verified extension goal wins, else DRAW.
FB-5  Possession: team / player with the longest *observed* possession. Unobserved time is
      reported as "unknown" and never credited to anyone.
FB-6  MVP: the player with the longest verified possession (official brief). Ties need a host decision.
FB-7  Host penalty: a host-applied penalty subtracts from the team score (audit-logged).
"""
from __future__ import annotations

from .common import counted

RULE_VERSION = "WASL-FOOTBALL-R1.0"
MIN_MVP_SECONDS = 1.0


def tally(events: list[dict], penalties: dict[str, int] | None = None) -> dict:
    score = {"A": 0, "B": 0}
    extension = {"A": 0, "B": 0}
    first_extension: str | None = None
    # a POSSIBLE_GOAL (e.g. ball occluded) only scores after the host accepts it (FB-2)
    for ev in sorted((e for e in events if e["type"] in ("GOAL", "POSSIBLE_GOAL") and counted(e)), key=lambda e: e["t_start"]):
        team = ev.get("team")
        if team not in score:
            continue
        if ev.get("phase") == "EXTENSION":
            extension[team] += 1
            first_extension = first_extension or team
        else:
            score[team] += ev["points"]
    for team, p in (penalties or {}).items():
        if team in score:
            score[team] -= abs(p)
    return {"regulation": score, "extension": extension, "first_extension_goal": first_extension}


def decide(tally_result: dict, tie_break: str = "golden_goal") -> dict:
    a, b = tally_result["regulation"]["A"], tally_result["regulation"]["B"]
    if a != b:
        w = "A" if a > b else "B"
        return {"winner": w, "decided_by": "REGULATION_SCORE", "score": {"A": a, "B": b}}
    if tie_break == "golden_goal" and tally_result["first_extension_goal"]:
        return {"winner": tally_result["first_extension_goal"], "decided_by": "GOLDEN_GOAL", "score": {"A": a, "B": b}}
    return {"winner": None, "decided_by": "DRAW", "score": {"A": a, "B": b}}


def possession_summary(seconds_by_team: dict[str, float], unknown: float) -> dict:
    total = sum(seconds_by_team.values())
    pct = {t: (round(100 * s / total, 1) if total else 0.0) for t, s in seconds_by_team.items()}
    leader = None
    if total > 0:
        ranked = sorted(seconds_by_team.items(), key=lambda kv: kv[1], reverse=True)
        if len(ranked) == 1 or ranked[0][1] - ranked[1][1] > 1e-9:
            leader = ranked[0][0]
    return {"seconds": seconds_by_team, "percent_of_observed": pct, "unknown_seconds": round(unknown, 2), "leader": leader}


def pick_mvp(seconds_by_player: dict[str, float]) -> dict:
    ranked = sorted(seconds_by_player.items(), key=lambda kv: kv[1], reverse=True)
    if not ranked or ranked[0][1] < MIN_MVP_SECONDS:
        return {"mvp": None, "reason": "No player has enough verified possession time.", "needs_host": True}
    if len(ranked) > 1 and abs(ranked[0][1] - ranked[1][1]) < 1e-9:
        return {"mvp": None, "reason": f"Tie between {ranked[0][0]} and {ranked[1][0]} - host decides.", "needs_host": True}
    return {"mvp": ranked[0][0], "seconds": round(ranked[0][1], 2), "reason": "Longest verified possession time (FB-6).", "needs_host": False}
