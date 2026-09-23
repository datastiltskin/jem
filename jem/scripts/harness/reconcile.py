#!/usr/bin/env python3
"""
Reconcile — stage 4 of the intra-run consensus harness, plus the ledger writer.

Deterministic: no LLM. It merges a researcher entry, a verifier verdict and an
optional critic note into one internal verdict, a capture label and a
confidence tier. Being committed code rather than a judgement call is the point
— the same inputs give the same verdict for everyone, and CI can replay it.

Two ideas do the real work here.

Capture-and-label: nothing is dropped at ingest. Every finding is stored with a
status, and filtering to canon happens only at the promotion boundary. The
honest gap lives in canon while the attempt survives in the ledger, which is
what makes a "no reports found" verdict credible — the ledger shows what was
checked.

Agreement x diversity: confidence is not an agreement count. Diversity is the
number of distinct base-model families that agree, so two runs of one model
count once. Agreement at diversity 1 is shared_bias_risk, not proof.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── capture labels (the ingest boundary) ─────────────────────────────────────

SOURCED = "sourced"
HOMEPAGE_ONLY = "homepage_only"
SECONDARY_ONLY = "secondary_only"
UNSOURCED_CANDIDATE = "unsourced_candidate"
FETCH_FAILED = "fetch_failed"
PARTIAL = "partial"
REFUTED = "refuted"

PROMOTES_TO_CANON = {SOURCED}

# ── confidence tiers (ordered) ───────────────────────────────────────────────

T_UNSOURCED = "unsourced"
T_PARTIAL = "partial"
T_PARTIAL_APPROACHING = "partial_approaching_complete"
T_COMPLETE = "complete"
T_VERIFIED = "verified"

TIER_ORDER = [T_UNSOURCED, T_PARTIAL, T_PARTIAL_APPROACHING, T_COMPLETE, T_VERIFIED]

# Promotion above `partial` requires corroboration from more than one base-model
# family. One model agreeing with itself is one opinion, however often it is asked.
MIN_DIVERSITY_ABOVE_PARTIAL = 2

CONFIRM, REFUTE, UNSOURCED_V, NA = "CONFIRM", "REFUTE", "UNSOURCED", "NA"


@dataclass
class Liveness:
    url: Optional[str] = None
    status: Optional[int] = None
    is_document: bool = False
    ok: bool = False
    reason: Optional[str] = None


@dataclass
class Researcher:
    value: Any = None
    source_url: Optional[str] = None
    source_is_primary: bool = False
    is_goi_primary: bool = False
    independent_secondaries: int = 0
    attempts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Verifier:
    verdict: str = UNSOURCED_V          # CONFIRM | REFUTE | UNSOURCED | NA
    value_present_at_url: bool = False
    researcher_score: Optional[str] = None   # supported | partial | unsupported
    source_url: Optional[str] = None


@dataclass
class Critic:
    ran: bool = False
    challenge: Optional[str] = None
    upheld: bool = True                  # False => the challenge stuck


def model_diversity(model_families: List[str]) -> int:
    """Distinct base-model families in the agreeing set."""
    return len({(f or "").strip().lower() for f in model_families if f})


def _tier(researcher: Researcher, verifier: Verifier, diversity: int) -> str:
    if verifier.verdict != CONFIRM or not researcher.source_is_primary:
        return T_UNSOURCED

    primaries = 1
    secondaries = researcher.independent_secondaries

    if researcher.is_goi_primary and verifier.value_present_at_url:
        tier = T_VERIFIED
    elif primaries >= 2 or secondaries >= 3:
        tier = T_COMPLETE
    elif secondaries >= 1:
        tier = T_PARTIAL_APPROACHING
    else:
        tier = T_PARTIAL

    # Cap anything above `partial` that only one model family vouches for.
    if TIER_ORDER.index(tier) > TIER_ORDER.index(T_PARTIAL) and diversity < MIN_DIVERSITY_ABOVE_PARTIAL:
        return T_PARTIAL
    return tier


def _label(liveness: Liveness, researcher: Researcher, verifier: Verifier) -> str:
    if liveness.url and not liveness.ok:
        if liveness.reason in ("bare_homepage_for_document_claim", "redirects_to_root"):
            return HOMEPAGE_ONLY
        return FETCH_FAILED
    if verifier.verdict == REFUTE:
        return REFUTED
    if researcher.value is None:
        return UNSOURCED_CANDIDATE
    if not researcher.source_is_primary:
        return SECONDARY_ONLY if researcher.independent_secondaries else UNSOURCED_CANDIDATE
    if verifier.verdict == CONFIRM and verifier.value_present_at_url:
        return SOURCED
    return UNSOURCED_CANDIDATE


def reconcile(liveness: Liveness, researcher: Researcher, verifier: Verifier,
              critic: Optional[Critic] = None,
              model_families: Optional[List[str]] = None) -> Dict[str, Any]:
    """Merge the rungs into a verdict. Pure function of its inputs."""
    critic = critic or Critic()
    diversity = model_diversity(model_families or [])

    label = _label(liveness, researcher, verifier)
    # A cell whose citation failed the pre-gate has no tier to earn: the URL
    # never became evidence, whatever the verifier thought it read.
    gate_failed = bool(liveness.url) and not liveness.ok
    tier = T_UNSOURCED if gate_failed else _tier(researcher, verifier, diversity)

    # An upheld critic challenge demotes; the critic exists to be listened to.
    if critic.ran and not critic.upheld:
        label = UNSOURCED_CANDIDATE if label == SOURCED else label
        tier = T_UNSOURCED

    shared_bias_risk = "high" if (diversity == 1 and label == SOURCED) else "low"

    return {
        "label": label,
        "confidence_tier": tier,
        "model_diversity": diversity,
        "shared_bias_risk": shared_bias_risk,
        "promotes_to_canon": label in PROMOTES_TO_CANON,
    }


# ── ledger (stage 5) ─────────────────────────────────────────────────────────

def ledger_path(repo_root: Path, track: str, model: str, user: str,
                timestamp: Optional[str] = None) -> Path:
    ts = timestamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe = lambda s: "".join(c if c.isalnum() or c in "-_." else "_" for c in str(s))
    return repo_root / "ledger" / "runs" / f"{safe(track)}__{safe(model)}__{safe(user)}__{ts}.jsonl"


def append_record(path: Path, *, entity_id: str, field_name: str, track: str,
                  prompt_version: str, model: str, model_version: str,
                  context: str, temperature: float,
                  liveness: Liveness, researcher: Researcher, verifier: Verifier,
                  critic: Optional[Critic] = None,
                  reconciled: Optional[Dict[str, Any]] = None,
                  suggested_entities: Optional[List] = None,
                  suggested_edges: Optional[List] = None,
                  tokens_in: int = 0, tokens_out: int = 0) -> Dict[str, Any]:
    """Append one cell record. The ledger is append-only: never rewrite a line."""
    critic = critic or Critic()
    record = {
        "entity_id": entity_id,
        "field": field_name,
        "track": track,
        "prompt_version": prompt_version,
        "model": model,
        "model_version": model_version,
        "context": context,
        "temperature": temperature,
        "liveness": asdict(liveness),
        "researcher": asdict(researcher),
        "verifier": asdict(verifier),
        "critic": asdict(critic),
        "reconcile": reconciled if reconciled is not None else reconcile(
            liveness, researcher, verifier, critic, [model]),
        "suggested_entities": suggested_entities or [],
        "suggested_edges": suggested_edges or [],
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return record


def replay_canon(ledger_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Derive canon from the ledger: the promotion rule applied over every run.

    Canon is a replayable derivation, not a separate store. Re-run this and you
    reproduce the same values — that is the whole transparency claim. Later
    records win, so a re-verified cell supersedes its earlier reading.
    """
    canon: Dict[str, Dict[str, Any]] = {}
    for path in sorted(ledger_dir.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            rc = rec.get("reconcile") or {}
            if not rc.get("promotes_to_canon"):
                continue
            key = f"{rec.get('entity_id')}.{rec.get('field')}"
            canon[key] = {
                "value": (rec.get("researcher") or {}).get("value"),
                "source_url": (rec.get("researcher") or {}).get("source_url"),
                "confidence_tier": rc.get("confidence_tier"),
                "model_diversity": rc.get("model_diversity"),
                "timestamp_utc": rec.get("timestamp_utc"),
                "prompt_version": rec.get("prompt_version"),
            }
    return canon


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Harness reconcile / canon replay")
    ap.add_argument("--replay", action="store_true",
                    help="derive canon from ledger/runs and print it")
    args = ap.parse_args()
    repo_root = Path(__file__).resolve().parent.parent.parent
    if args.replay:
        canon = replay_canon(repo_root / "ledger" / "runs")
        print(json.dumps(canon, indent=2, ensure_ascii=False))
        print(f"\n{len(canon)} cell(s) promote to canon.")
