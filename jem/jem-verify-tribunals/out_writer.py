#!/usr/bin/env python3
"""
out_writer.py — agent-side helper for the Prajna/DeepSeek verify-trib-01 pass.

The harness agent decides verdicts from live web evidence, then this module
appends rows to the canonical output CSV through run.py's normalize_rows /
apply_mechanical machinery, so the emitted rows are byte-identical in format
and deterministic enforcement to what run.py would produce.

Canonical outputs (one table per rater, per RUN_SETUP.md):
    out/deepseek__verify-trib-01__prajna__20260831_131656.csv
    out/deepseek__verify-trib-01__prajna__20260831_131656.meta.json
    out/fetch_log/

Usage (import only):
    import out_writer as W
    W.append_entity("aft", [ {"field": "pending_cases", "verdict": "UNSOURCED", ...}, ... ])
    W.update_meta()
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402

OUT = os.path.join(HERE, "out")
CANON_STEM = "deepseek__verify-trib-01__prajna__20260831_131656"
CSV_PATH = os.path.join(OUT, CANON_STEM + ".csv")
META_PATH = os.path.join(OUT, CANON_STEM + ".meta.json")

_claims, _by_entity = run.load_claims(run.CLAIMS_DEFAULT)

DONE = set()


def _existing_pairs():
    if not os.path.exists(CSV_PATH):
        return set()
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return {(r["entity_id"], r["field"]) for r in csv.DictReader(f)}


def append_entity(eid, raw_rows, label=""):
    """raw_rows: list of dicts with 'field' + decided verdict fields
    (verdict, verified_value, verified_as_of, source_class, source_title,
    source_url, table_or_section, verbatim_excerpt, primary_count,
    independent_secondary_count, confidence_tier, notes). Missing keys become
    empty/0 defaults via normalize_rows."""
    if eid not in _by_entity:
        raise KeyError(f"unknown entity {eid}")
    claims = _by_entity[eid]
    norm = run.normalize_rows(eid, claims, raw_rows)
    with open(CSV_PATH, "a", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=run.OUTPUT_HEADER, extrasaction="ignore")
        for r in norm:
            w.writerow(r)
    DONE.add(eid)
    print(f"[out_writer] appended {len(norm)} rows for {eid} "
          f"({[r['verdict'] for r in norm]}){(' ' + label) if label else ''}",
          file=sys.stderr, flush=True)
    return norm


def update_meta(sat_result="PASS", note=""):
    """Rewrite meta.json reflecting current CSV state."""
    rows_n = len(_existing_pairs())
    entities = sorted({e for e, _ in _existing_pairs()})
    meta = {
        "rater": "prajna",
        "model": "deepseek",
        "model_version": "deepseek-v4-flash (DeepSeek-V4-Flash-0731) via DeepSeek Harness Web GUI agent",
        "context": "provided-files + web_search_on, temp 0.2",
        "web_search": True,
        "temperature": 0.2,
        "prompt_version": "verify-trib-v1",
        "batch_id": "verify-trib-01",
        "timestamp_utc": run.now_utc().isoformat(),
        "entities_n": 44,
        "rows_n": rows_n,
        "tokens_in": 0,
        "tokens_out": 0,
        "cost_estimate": "$0.00 (harness agent run — no external LLM API; agent inference not billable)",
        "sat_anchor_check": sat_result,
        "search_backend": "harness web_search + web_fetch + bash curl (pypdf PDF extraction)",
        "entities_processed": entities,
        "run_note": ("agent-driven verifier pass (prajna/deepseek arm). temperature knob not settable "
                     "by harness agent (harness default); recorded 0.2 per card. "
                     + (note or "")),
        "primary_source": "https://www.sebi.gov.in/reports-and-statistics/publications/aug-2026/Chapter%2010.pdf",
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")
    print(f"[out_writer] meta updated: {rows_n} rows, {len(entities)} entities", file=sys.stderr)
    return meta


if __name__ == "__main__":
    print("rows so far:", len(_existing_pairs()))
    print("entities so far:", sorted({e for e, _ in _existing_pairs()}))
