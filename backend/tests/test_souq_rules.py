from app.rules import souq as sq

MISSION = {"requested": ["dates", "coffee", "pottery"], "budget": 60}


def show(product, t, cid=None):
    cid = cid or sq.CATALOG[product]["marker_ids"][0]
    return {"product": product, "card_id": cid, "t_first": t, "t_last": t + 2}


def say(product, t):
    return {"product": product, "t": t, "text": product, "alias": product}


def types(ev):
    return [e["type"] for e in ev["events"]]


def test_correct_selection_scores_item_plus_spoken_match():
    ev = sq.evaluate(MISSION, [show("dates", 1), show("coffee", 5), show("pottery", 9)],
                     [say("dates", 1.5), say("coffee", 5.5), say("pottery", 9.5)], True)
    assert sq.score(ev["events"]) == 3 * 2 + 3 * 1
    assert ev["spend"] == 55 and "BUDGET_EXCEEDED" not in types(ev)


def test_incorrect_selection_earns_no_points_but_costs_budget():
    ev = sq.evaluate(MISSION, [show("oud", 1)], [say("oud", 1.2)], True)
    assert sq.score(ev["events"]) == 0 and ev["spend"] == 40 and "EXTRA_ITEM" in types(ev)


def test_audio_video_mismatch_needs_review_and_scores_nothing_extra():
    ev = sq.evaluate(MISSION, [show("dates", 1)], [say("honey", 1.5)], True)
    mm = [e for e in ev["events"] if e["type"] == "AUDIO_VIDEO_MISMATCH"]
    assert len(mm) == 1 and mm[0]["status"] == "NEEDS_REVIEW"
    assert sq.score(ev["events"]) == 2  # only the visual selection counts; no spoken bonus


def test_spoken_but_not_shown_is_flagged():
    ev = sq.evaluate(MISSION, [], [say("coffee", 2)], True)
    assert types(ev) == ["AUDIO_VIDEO_MISMATCH"] and sq.score(ev["events"]) == 0


def test_budget_violation_penalty_once():
    m = {"requested": ["dates", "pottery", "coffee"], "budget": 50}
    ev = sq.evaluate(m, [show("dates", 1), show("pottery", 5), show("coffee", 9)], [], True)
    assert ev["spend"] == 55 and types(ev).count("BUDGET_EXCEEDED") == 1
    assert sq.score(ev["events"]) == 6 - 2


def test_duplicate_selection_gives_no_additional_points():
    ev = sq.evaluate(MISSION, [show("dates", 1), show("dates", 10)], [say("dates", 1.3)], True)
    assert types(ev).count("DUPLICATE_ITEM") == 1
    assert sq.score(ev["events"]) == 2 + 1
    assert ev["spend"] == 12  # a duplicate is not paid for twice


def test_second_card_of_same_product_is_duplicate():
    ev = sq.evaluate(MISSION, [show("dates", 1, 60), show("dates", 1.5, 70)], [], True)
    assert "DUPLICATE_ITEM" in types(ev)


def test_no_transcript_never_credits_spoken_match():
    ev = sq.evaluate(MISSION, [show("dates", 1)], [], False)
    sm = [e for e in ev["events"] if e["type"] == "SPOKEN_MATCH"]
    assert sm and sm[0]["status"] == "NEEDS_REVIEW" and sq.score(ev["events"]) == 2


def test_arabic_and_english_keyword_matching():
    segs = [{"start": 0, "end": 4, "text": "أريد القهوة و التمر ثم Pottery"}]
    found = {m["product"] for m in sq.find_mentions(segs)}
    assert {"coffee", "dates", "pottery"} <= found


def test_tie_break_lower_spend_then_time():
    assert sq.rank_key(9, 45, 20) < sq.rank_key(9, 55, 10)
    assert sq.rank_key(9, 45, 10) < sq.rank_key(9, 45, 20)
