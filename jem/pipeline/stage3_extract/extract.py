# Stage 3 — Extract, LLM call #1 (spec §5). Normalized text -> claims.jsonl.
from __future__ import annotations
from pathlib import Path


def extract(shas: list[str], out_path: Path) -> Path:
    """LLM proposes claims from normalized evidence ONLY; never the open web / memory.

    Writes one JSON object per line to out_path:
        {field, value, source_sha, quote, char_start}
    `quote` must be an exact substring of the evidence text; omit fields not
    literally present (do not invent). Prompt lives in prompts/extract.txt.
    """
    raise NotImplementedError("Stage 3 not built — see spec §5 (Extract)")
