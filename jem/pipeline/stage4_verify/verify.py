# Stage 4 — Verify, deterministic (spec §5). Claims -> verified + rejected.
from __future__ import annotations
from pathlib import Path


def verify(claims_path: Path, out_dir: Path) -> tuple[Path, Path]:
    """Deterministic span match; no LLM. Returns (verified_claims, rejected) paths.

    Per claim: exact str.find(quote); else fuzzy rapidfuzz.partial_ratio>=95 in a
    window around char_start; else reject. Plus cross_checks.py: sanctioned>=working,
    vacancies=sanctioned-working, non-negative pendency, enum/state-code validity,
    staleness flags. Cross-source contradiction -> data_quality: contested, keep both.
    """
    raise NotImplementedError("Stage 4 not built — see spec §5 (Verify)")
