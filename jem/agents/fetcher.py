"""Fetcher agent — extract staging records from source text via Anthropic API."""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional

from agents.prompts import load_prompt

DEFAULT_MODEL = "claude-sonnet-4-6"
CONFIDENCE_REVIEW_THRESHOLD = 0.85


def _default_client():
    import anthropic

    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def extract_from_text(
    source_text: str,
    *,
    client: Any = None,
    create_message: Optional[Callable] = None,
) -> list[dict]:
    """Run extraction prompt against source text. Returns list of staging dicts."""
    system_prompt = load_prompt("extraction_v1.md")

    if create_message is not None:
        response = create_message(system=system_prompt, user=source_text)
        raw = response
    else:
        api = client or _default_client()
        msg = api.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": source_text}],
        )
        raw = msg.content[0].text

    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    items = json.loads(text)
    if not isinstance(items, list):
        raise ValueError("Extraction output must be a JSON array")

    return [item for item in items if isinstance(item, dict)]


def to_staging_records(items: list[dict], source_url: str = "") -> list[dict]:
    """Convert extraction items to staging_records-shaped dicts."""
    records = []
    for item in items:
        confidence = float(item.get("confidence", 0))
        status = "needs_review" if confidence < CONFIDENCE_REVIEW_THRESHOLD else "pending"
        records.append(
            {
                "entity_name": item["entity_name"],
                "position": item.get("position"),
                "event_type": item["event_type"],
                "event_date": item.get("event_date"),
                "reference_number": item.get("reference_number"),
                "verbatim_excerpt": item["verbatim_excerpt"],
                "confidence": confidence,
                "source_url": source_url,
                "status": status,
            }
        )
    return records
