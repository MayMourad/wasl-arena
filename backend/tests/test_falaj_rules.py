from app.rules import falaj as ff

L = ff.LAYOUTS["oasis-1"]


def t(ttype, rot, i=0):
    return {"type": ttype, "rot": rot, "id": i}


VALID = {
    (2, 1): t("TEE", 2), (1, 1): t("ELBOW", 1), (1, 2): t("STRAIGHT", 1), (1, 3): t("STRAIGHT", 1), (1, 4): t("TEE", 2),
    (3, 1): t("ELBOW", 0), (3, 2): t("STRAIGHT", 1), (3, 3): t("ELBOW", 2), (4, 3): t("ELBOW", 0),
}


def test_complete_valid_route():
    a = ff.analyze(L, VALID)
    assert a["all_connected"] and len(a["reached_destinations"]) == 3 and a["leaks"] == []
    s = ff.score_round(a, 11.0)
    assert s["total"] == 3 * 3 + 0 + 2


def test_partial_network_leaks_and_misses_destination():
    tiles = {k: v for k, v in VALID.items() if k not in {(3, 3), (4, 3)}}
    a = ff.analyze(L, tiles)
    assert len(a["reached_destinations"]) == 2 and not a["all_connected"]
    assert len(a["leaks"]) == 1 and a["leaks"][0]["cell"] == [3, 2]
    assert ff.score_round(a, None)["total"] == 2 * 3 - 1


def test_blocked_route_closed_side_breaks_upper_branch():
    tiles = dict(VALID)
    tiles[(1, 2)] = t("STRAIGHT", 0)  # vertical channel: does not accept water from the west
    a = ff.analyze(L, tiles)
    assert [4, 4] in a["reached_destinations"] and [0, 4] not in a["reached_destinations"]
    assert any(lk["reason"].startswith("neighbouring tile does not connect") for lk in a["leaks"])
    assert ff.score_round(a, None)["total"] == 3 - 1


def test_invalid_connection_into_rock_is_a_leak():
    tiles = dict(VALID)
    tiles[(2, 1)] = t("CROSS", 0)
    a = ff.analyze(L, tiles)
    assert a["all_connected"]
    assert any("rock" in lk["reason"] for lk in a["leaks"])
    assert ff.score_round(a, 20)["total"] == 9 - 1 + 2


def test_edge_leak_and_illegal_placement():
    a = ff.analyze(L, {(2, 1): t("CROSS", 0), (0, 1): t("STRAIGHT", 0)})
    assert any("edge" in lk["reason"] or "no tile" in lk["reason"] for lk in a["leaks"])
    b = ff.analyze(L, {(2, 2): t("CROSS", 0)})
    assert b["illegal_placements"]


def test_empty_board_scores_zero():
    a = ff.analyze(L, {})
    assert ff.score_round(a, None)["total"] == -1  # the well's open end leaks onto bare ground
    assert a["reached_destinations"] == []


def test_time_bonus_tiers():
    assert ff.time_bonus(True, 30) == 2 and ff.time_bonus(True, 60) == 1 and ff.time_bonus(True, 85) == 0
    assert ff.time_bonus(False, 10) == 0


def test_tie_break_shortest_network_then_time():
    a = ff.analyze(L, VALID)
    longer = dict(a, network_size=a["network_size"] + 2)
    assert ff.rank_key(11, a, 30) < ff.rank_key(11, longer, 20)
    assert ff.rank_key(11, a, 20) < ff.rank_key(11, a, 30)
    assert ff.rank_key(12, longer, 80) < ff.rank_key(11, a, 10)


def test_rotation_semantics():
    assert ff.open_sides("ELBOW", 1) == {ff.E, ff.S}
    assert ff.open_sides("STRAIGHT", 1) == {ff.E, ff.W}
    assert ff.open_sides("TEE", 2) == {ff.S, ff.W, ff.N}
