"""Verifier agent — confirm staging records against source text."""

from __future__ import annotations

import json
import os
from typing import Any, Callable, Optional

from agents.prompts import load_prompt

DEFAULT_MODEL = "claude-sonnet-4-6"


def verify_record(
    staging_record: dict,
    source_text: str,
    *,
    client: Any = None,
    create_message: Optional[Callable] = None,
) -> dict:
    """Verify a staging record. Returns verification result dict."""
    system_prompt = load_prompt("verification_v1.md")
    user_content = json.dumps(
        {"staging_record": staging_record, "source_text": source_text},
        ensure_ascii=False,
    )

    if create_message is not None:
        raw = create_message(system=system_prompt, user=user_content)
    else:
        import anthropic

        api = client or anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        msg = api.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        raw = msg.content[0].text

    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    result = json.loads(text)
    extraction_confidence = float(staging_record.get("confidence", 0))
    if float(result.get("confidence", extraction_confidence)) > extraction_confidence:
        result["confidence"] = extraction_confidence
    return result
