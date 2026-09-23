# Stage 2 — Normalize (spec §5). Raw evidence bytes -> text + offset->location map.
from __future__ import annotations
from pathlib import Path

from pipeline.stage1_fetch import EVIDENCE


def normalize(sha: str) -> tuple[Path, Path]:
    """Dispatch by stored ext -> write {sha}.txt + {sha}.locmap.json, return their paths.

    pdf  -> pdf_text.py  (pdfplumber + OCR fallback; OCR-derived = lower trust)
    html -> html_text.py (trafilatura/selectolax + DOM-path locmap)
    json -> json_text.py (flatten to "dotted.path: value" lines)
    """
    raise NotImplementedError("Stage 2 not built — see spec §5 (Normalize)")
