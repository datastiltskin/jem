"""MCP tool helpers."""

from __future__ import annotations

REFUSAL_KEYWORDS = (
    "legal advice",
    "should i sue",
    "will i win",
    "case outcome",
    "predict outcome",
    "judge name",
    "justice ",
)


def is_refused_query(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in REFUSAL_KEYWORDS)


def refusal_payload() -> dict:
    return {
        "refused": True,
        "reason": "JEM provides structural map data only, not legal advice or case outcomes.",
    }
