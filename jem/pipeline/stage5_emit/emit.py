# Stage 5 — Emit (spec §5). Verified claims -> entity YAML. Prefer pure Jinja.
from __future__ import annotations
from pathlib import Path


def emit(verified_path: Path, out_path: Path) -> Path:
    """Verified claims -> entity.yaml. null + data_quality_note for unbacked fields.

    sources[] is populated FROM claim records (not authored) so citation and fact
    cannot drift. Use templates/entity.yaml.j2; no LLM if field placement is mechanical.
    """
    raise NotImplementedError("Stage 5 not built — see spec §5 (Emit)")
