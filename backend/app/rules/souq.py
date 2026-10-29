"""Souq Signal rule engine (deterministic).  Rule set WASL-SOUQ-R1.0

A player receives a shopping mission (requested products + a budget in AED), selects physical
product cards, shows them to the camera and names them aloud.

SS-1  Requested product shown to the camera: +2.
SS-2  The same requested product announced aloud within the matching window: +1.
SS-3  Budget exceeded (valid expenditure > budget): -2 (once).
SS-4  Duplicate (same product presented again or two cards of one product): no additional points.
SS-5  Product named but never shown, or shown while a different product is named: flagged
      AUDIO_VIDEO_MISMATCH and sent to host review (0 points until accepted).
SS-6  Tie-break: lower valid expenditure, then earlier finish time.
If no transcript is available, spoken-match events are NEEDS_REVIEW (never silently credited).
"""
from __future__ import annotations

import re
import unicodedata

from .common import counted

RULE_VERSION = "WASL-SOUQ-R1.0"
MATCH_WINDOW_S = 5.0

# marker ids: card A = 60..67, duplicate card B = 70..77 (same product order)
CATALOG: dict[str, dict] = {
    "dates":     {"en": "Dates",      "ar": "تمر",       "price": 12, "marker_ids": [60, 70], "aliases": ["dates", "date", "tamr", "tamar", "تمر", "تمور", "تمرة"]},
    "coffee":    {"en": "Coffee",     "ar": "قهوة",      "price": 18, "marker_ids": [61, 71], "aliases": ["coffee", "gahwa", "qahwa", "قهوة", "القهوة", "قهوه"]},
    "spices":    {"en": "Spices",     "ar": "بهارات",    "price": 15, "marker_ids": [62, 72], "aliases": ["spice", "spices", "baharat", "بهارات", "البهارات"]},
    "pottery":   {"en": "Pottery",    "ar": "فخار",      "price": 25, "marker_ids": [63, 73], "aliases": ["pottery", "pot", "fakhar", "فخار", "الفخار"]},
    "textile":   {"en": "Textile",    "ar": "قماش",      "price": 30, "marker_ids": [64, 74], "aliases": ["textile", "textiles", "fabric", "cloth", "qumash", "قماش", "القماش", "اقمشة"]},
    "oud":       {"en": "Oud",        "ar": "عود",       "price": 40, "marker_ids": [65, 75], "aliases": ["oud", "oudh", "عود", "العود"]},
    "honey":     {"en": "Honey",      "ar": "عسل",       "price": 20, "marker_ids": [66, 76], "aliases": ["honey", "asal", "عسل", "العسل"]},
    "rosewater": {"en": "Rose water", "ar": "ماء الورد", "price": 10, "marker_ids": [67, 77], "aliases": ["rose water", "rosewater", "ماء الورد", "ماء ورد"]},
}
MARKER_TO_PRODUCT = {mid: p for p, v in CATALOG.items() for mid in v["marker_ids"]}


def normalize_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ة", "ه").replace("ى", "ي")
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def find_mentions(segments: list[dict]) -> list[dict]:
    """Keyword match over transcript segments -> [{product, t, text, alias}]. Time is interpolated
    inside the segment by character position (transcript timing is approximate)."""
    out = []
    for seg in segments:
        text = normalize_text(seg["text"])
        if not text:
            continue
        for product, info in CATALOG.items():
            for alias in info["aliases"]:
                a = normalize_text(alias)
                # optional Arabic prefixes: definite article (ال) and conjunction (و)
                for m in re.finditer(r"(?<!\w)(?:وال|ال|و)?" + re.escape(a) + r"(?!\w)", text):
                    frac = m.start() / max(len(text), 1)
                    t = seg["start"] + frac * max(seg["end"] - seg["start"], 0)
                    out.append({"product": product, "t": round(t, 2), "text": seg["text"], "alias": alias})
                    break
    out.sort(key=lambda m: m["t"])
    dedup: list[dict] = []
    for m in out:  # collapse repeats of the same product within 1.5 s
        if dedup and dedup[-1]["product"] == m["product"] and m["t"] - dedup[-1]["t"] < 1.5:
            continue
        dedup.append(m)
    return dedup


def evaluate(mission: dict, presentations: list[dict], mentions: list[dict], transcript_available: bool) -> dict:
    """presentations: [{product, card_id, t_first, t_last}] visual presentation intervals.
    mentions: spoken product mentions. Returns {events, spend, summary}."""
    requested = list(mission["requested"])
    budget = mission["budget"]
    events: list[dict] = []

    def add(type_, rule, product, t, points, status, reason, extra=None):
        events.append({
            "id": f"{type_.lower()}-{len(events) + 1}", "type": type_, "rule_id": rule, "product": product,
            "t_start": round(t, 2), "t_end": round(t, 2), "points": points, "status": status,
            "reason": reason, "review": None, **(extra or {}),
        })

    by_product: dict[str, list[dict]] = {}
    for p in sorted(presentations, key=lambda x: x["t_first"]):
        by_product.setdefault(p["product"], []).append(p)

    selected = list(by_product)
    for product in selected:
        shows = by_product[product]
        first = shows[0]
        info = CATALOG[product]
        is_req = product in requested
        if is_req:
            add("REQUESTED_ITEM", "SS-1", product, first["t_first"], 2, "VERIFIED",
                f"{info['en']} ({info['ar']}) is on the mission list and was shown to the camera (card {first['card_id']}).")
        else:
            add("EXTRA_ITEM", "SS-1", product, first["t_first"], 0, "VERIFIED",
                f"{info['en']} was shown but is not on the mission list: no points, price still counts toward the budget.")
        # duplicates: later presentation of the same product, or a second card id of it
        for dup in shows[1:]:
            add("DUPLICATE_ITEM", "SS-4", product, dup["t_first"], 0, "VERIFIED",
                f"{info['en']} presented again (card {dup['card_id']}): no additional points.")
        # spoken match
        near = [m for m in mentions if m["product"] == product and abs(m["t"] - first["t_first"]) <= MATCH_WINDOW_S]
        if near and is_req:
            add("SPOKEN_MATCH", "SS-2", product, near[0]["t"], 1, "VERIFIED" if transcript_available else "NEEDS_REVIEW",
                f"Player said '{near[0]['alias']}' within {MATCH_WINDOW_S:.0f}s of showing {info['en']}.", {"transcript": near[0]["text"]})
        elif near:
            pass  # spoken correctly but not requested: nothing to award
        else:
            other = [m for m in mentions if abs(m["t"] - first["t_first"]) <= MATCH_WINDOW_S and m["product"] != product]
            if transcript_available and other:
                add("AUDIO_VIDEO_MISMATCH", "SS-5", product, first["t_first"], 0, "NEEDS_REVIEW",
                    f"Showed {info['en']} but said '{other[0]['alias']}' ({CATALOG[other[0]['product']]['en']}).",
                    {"transcript": other[0]["text"], "spoken_product": other[0]["product"]})
            elif not transcript_available and is_req:
                add("SPOKEN_MATCH", "SS-2", product, first["t_first"], 1, "NEEDS_REVIEW",
                    "No transcript available: spoken announcement cannot be verified automatically.")
    # spoken but never shown
    for m in mentions:
        if m["product"] not in by_product and not any(
                e["type"] == "AUDIO_VIDEO_MISMATCH" and m["product"] in (e["product"], e.get("spoken_product")) for e in events):
            add("AUDIO_VIDEO_MISMATCH", "SS-5", m["product"], m["t"], 0, "NEEDS_REVIEW",
                f"Said '{m['alias']}' ({CATALOG[m['product']]['en']}) but no matching card was seen.", {"transcript": m["text"]})

    spend = sum(CATALOG[p]["price"] for p in selected)
    if spend > budget:
        add("BUDGET_EXCEEDED", "SS-3", None, max([s["t_last"] for s in presentations] or [0]), -2, "VERIFIED",
            f"Valid expenditure AED {spend} exceeds the budget of AED {budget}.")
    return {"events": events, "spend": spend, "selected": selected}


def score(events: list[dict]) -> int:
    return sum(e["points"] for e in events if counted(e))


def rank_key(total: int, spend: int, finish_s: float | None) -> tuple:
    return (-total, spend, finish_s if finish_s is not None else 10**6)
