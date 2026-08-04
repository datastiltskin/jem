# Stage 6 — Gate, deterministic hard exit codes (spec §5). Wire into CI.
from __future__ import annotations
from pathlib import Path


def run_gate(entity_path: Path) -> int:
    """Return 0 iff all gates pass; non-zero on any violation.

    1. JEM validate.py --strict.
    2. Convention lint: id never renamed; contributor emits no rel_* YAML;
       data_quality != verified unless every field's source is a non-OCR primary
       host; never set derived.scores_validated; path _generated/states/{code}/.
    3. Source-integrity: every sources[] URL has a status:OK line in manifest.jsonl.
    4. Round-trip: every non-null field maps to a verified=True claim.
    """
    raise NotImplementedError("Stage 6 not built — see spec §5 (Gate)")
