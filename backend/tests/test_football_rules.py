from app.rules import football as fb


def goal(team, status="VERIFIED", t=10.0, phase="REGULATION", review=None):
    return {"type": "GOAL", "team": team, "points": 1, "t_start": t, "status": status, "phase": phase, "review": review}


def test_valid_goal_scores_for_attacking_team():
    t = fb.tally([goal("A")])
    assert t["regulation"] == {"A": 1, "B": 0}
    assert fb.decide(t)["winner"] == "A"


def test_no_goal_is_a_draw_with_zero_points():
    t = fb.tally([])
    d = fb.decide(t)
    assert t["regulation"] == {"A": 0, "B": 0}
    assert d["winner"] is None and d["decided_by"] == "DRAW"


def test_uncertain_detection_is_not_counted_until_host_accepts():
    ev = goal("B", status="NEEDS_REVIEW")
    assert fb.tally([ev])["regulation"]["B"] == 0
    ev["review"] = {"decision": "ACCEPTED"}
    assert fb.tally([ev])["regulation"]["B"] == 1
    ev["review"] = {"decision": "REJECTED"}
    assert fb.tally([ev])["regulation"]["B"] == 0


def test_score_update_across_multiple_goals():
    t = fb.tally([goal("A", t=5), goal("A", t=20), goal("B", t=30)])
    assert t["regulation"] == {"A": 2, "B": 1}
    assert fb.decide(t)["winner"] == "A"


def test_tie_break_golden_goal_and_draw():
    base = [goal("A", t=5), goal("B", t=20)]
    assert fb.decide(fb.tally(base))["decided_by"] == "DRAW"
    ext = base + [goal("B", t=70, phase="EXTENSION")]
    d = fb.decide(fb.tally(ext))
    assert d["winner"] == "B" and d["decided_by"] == "GOLDEN_GOAL"
    assert fb.tally(ext)["regulation"] == {"A": 1, "B": 1}  # extension goal does not change regulation score


def test_host_penalty_reduces_score():
    assert fb.tally([goal("A"), goal("A", t=2)], {"A": 1})["regulation"]["A"] == 1


def test_mvp_is_longest_possession_and_ties_need_host():
    assert fb.pick_mvp({"Sara": 12.0, "Omar": 7.5})["mvp"] == "Sara"
    tie = fb.pick_mvp({"Sara": 5.0, "Omar": 5.0})
    assert tie["mvp"] is None and tie["needs_host"]
    assert fb.pick_mvp({"Sara": 0.2})["mvp"] is None


def test_possession_unknown_time_never_credited():
    p = fb.possession_summary({"A": 6.0, "B": 2.0}, unknown=4.0)
    assert p["leader"] == "A" and p["percent_of_observed"]["A"] == 75.0 and p["unknown_seconds"] == 4.0
