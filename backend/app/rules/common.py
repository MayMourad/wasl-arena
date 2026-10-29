"""Shared helpers for the deterministic rule engines."""
from __future__ import annotations

VERIFIED = "VERIFIED"
NEEDS_REVIEW = "NEEDS_REVIEW"
REJECTED = "REJECTED"


def effective_status(event: dict) -> str:
    """AI status, overridden by an explicit host review decision."""
    decision = (event.get("review") or {}).get("decision")
    if decision == "ACCEPTED":
        return VERIFIED
    if decision == "REJECTED":
        return REJECTED
    return event.get("status", NEEDS_REVIEW)


def counted(event: dict) -> bool:
    return effective_status(event) == VERIFIED
