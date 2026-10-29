"""End-to-end pipeline tests on SYNTHETIC fixtures (rendered by tools/make_fixtures.py).
They verify the CV + rules chain against known ground truth. They are not real gameplay."""
from pathlib import Path

import pytest

from app import integrity
from app.vision import falaj_cv, football_cv, souq_cv

from .conftest import noop


def run(judge, fixtures, name, cfg=None):
    p = fixtures / f"{name}.mp4"
    return judge(p, integrity.sha256_file(p), p.name, cfg, noop)


# ------------------------------------------------------------- football
def test_football_valid_goal(fixtures):
    r = run(football_cv.judge, fixtures, "football_goal")
    goals = [e for e in r["events"] if e["type"] == "GOAL"]
    assert len(goals) == 1 and goals[0]["team"] == "A" and goals[0]["status"] == "VERIFIED"
    assert r["summary"]["score"] == {"A": 1, "B": 0} and r["summary"]["winner"] == "A"
    assert goals[0]["evidence"], "goal must carry frame evidence"
    assert r["summary"]["possession"]["leader"] == "A"
    assert r["integrity"]["report_sha256"] and integrity.verify(r)["ok"]


def test_football_no_goal(fixtures):
    r = run(football_cv.judge, fixtures, "football_nogoal")
    assert [e for e in r["events"] if e["type"] in ("GOAL", "POSSIBLE_GOAL")] == []
    assert r["summary"]["score"] == {"A": 0, "B": 0} and r["summary"]["decided_by"] == "DRAW"


def test_football_uncertain_detection_is_not_scored(fixtures):
    r = run(football_cv.judge, fixtures, "football_uncertain")
    flagged = [e for e in r["events"] if e["type"] in ("GOAL", "POSSIBLE_GOAL")]
    assert flagged and all(e["status"] == "NEEDS_REVIEW" for e in flagged)
    assert r["summary"]["score"] == {"A": 0, "B": 0}


def test_football_mvp_from_longest_possession(fixtures):
    r = run(football_cv.judge, fixtures, "football_goal")
    top = max(r["metrics"]["possession"]["by_track"], key=r["metrics"]["possession"]["by_track"].get)
    assert top.startswith("A")
    r["config"]["assignments"] = {top: "Sara"}
    assert football_cv.summarise(r)["mvp"]["mvp"] == "Sara"


# ------------------------------------------------------------- falaj
@pytest.mark.parametrize("name,total,dests,leaks,bonus", [
    ("falaj_valid", 11, 3, 0, 2),
    ("falaj_partial", 5, 2, 1, 0),
    ("falaj_rock", 10, 3, 1, 2),
])
def test_falaj_video_scoring(fixtures, name, total, dests, leaks, bonus):
    r = run(falaj_cv.judge, fixtures, name)
    s = r["summary"]["score"]
    assert (s["total"], s["destinations"], s["leaks"], s["time_bonus"]) == (total, dests, leaks, bonus)
    assert all(e["status"] == "VERIFIED" for e in r["events"])
    assert all(e["evidence"] for e in r["events"])


def test_falaj_reconstructs_exact_tiles(fixtures):
    from .tools_fixture_truth import SOLUTION_TILES
    r = run(falaj_cv.judge, fixtures, "falaj_valid")
    snap = r["metrics"]["snapshots"][r["summary"]["final_state_index"]]
    got = {(t["cell"][0], t["cell"][1]): (t["type"], t["rot"]) for t in snap["tiles"]}
    assert got == SOLUTION_TILES


# ------------------------------------------------------------- souq
def run_souq(fixtures, manifest, name):
    m = manifest[name]
    return run(souq_cv.judge, fixtures, name, {"mission": m["mission"], "transcript_override": m["transcript_script"]})


def test_souq_correct_selection(fixtures, manifest):
    r = run_souq(fixtures, manifest, "souq_correct")
    assert r["summary"]["score"]["total"] == 9 and r["summary"]["spend"] == 55
    assert r["summary"]["remaining_budget"] == 5


def test_souq_audio_video_mismatch(fixtures, manifest):
    r = run_souq(fixtures, manifest, "souq_mismatch")
    assert any(e["type"] == "AUDIO_VIDEO_MISMATCH" and e["status"] == "NEEDS_REVIEW" for e in r["events"])
    assert r["summary"]["score"]["total"] == 2


def test_souq_budget_and_duplicate(fixtures, manifest):
    r = run_souq(fixtures, manifest, "souq_budget_dup")
    kinds = [e["type"] for e in r["events"]]
    assert "DUPLICATE_ITEM" in kinds and "BUDGET_EXCEEDED" in kinds
    assert r["summary"]["score"]["total"] == 7


def test_souq_without_transcript_is_review_not_credit(fixtures, manifest):
    m = manifest["souq_correct"]
    p = fixtures / "souq_correct.mp4"
    r = souq_cv.judge(p, integrity.sha256_file(p), p.name, {"mission": m["mission"], "transcript_override": {"status": "UNAVAILABLE"}}, noop)
    assert r["summary"]["score"]["total"] == 6  # visual points only; no spoken bonus without a transcript
    pending = [e for e in r["events"] if e["type"] == "SPOKEN_MATCH"]
    assert len(pending) == 3 and all(e["status"] == "NEEDS_REVIEW" for e in pending)
