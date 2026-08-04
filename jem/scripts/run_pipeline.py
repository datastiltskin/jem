#!/usr/bin/env python3
"""Orchestrate Stage 1->6 for one run (spec §1). Stages 2-6 are stubs today —
this wires the interfaces so the flow is runnable end to end as they land.

    python3 scripts/run_pipeline.py <run_id> <url> [<url> ...]
"""
from __future__ import annotations
import sys, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root on path

from pipeline.stage1_fetch import fetch
from pipeline.stage2_normalize import normalize
from pipeline.stage3_extract import extract
from pipeline.stage4_verify import verify
from pipeline.stage5_emit import emit
from pipeline.stage6_gate import run_gate


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id")
    ap.add_argument("urls", nargs="+")
    args = ap.parse_args()

    run_dir = Path("artifacts") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. FETCH — the only stage that touches the network.
    results = [fetch(u) for u in args.urls]
    ok = [r for r in results if r.ok()]
    print(f"[1] fetch: {len(ok)}/{len(results)} OK")
    if not ok:
        print("no evidence fetched — stopping", file=sys.stderr)
        return 1
    shas = [r.sha256 for r in ok]

    # 2. NORMALIZE — bytes -> text + locmap, per sha.
    for sha in shas:
        normalize(sha)

    # 3. EXTRACT (LLM #1) -> claims.jsonl
    claims = extract(shas, run_dir / "claims.jsonl")

    # 4. VERIFY (deterministic) -> verified + rejected
    verified, _rejected = verify(claims, run_dir)

    # 5. EMIT -> entity draft YAML
    entity = emit(verified, run_dir / "entity_draft.yaml")

    # 6. GATE -> hard exit code
    return run_gate(entity)


if __name__ == "__main__":
    sys.exit(main())
