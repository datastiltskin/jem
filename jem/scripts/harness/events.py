#!/usr/bin/env python3
"""Append-only ledger events for cell-touching writes.

Canon YAML stays lean. value_history is a DERIVED projection over these
events — never hand-authored on an entity file.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

CHANGE_REASONS = (
    "initial",
    "superseded_newer_period",
    "corrected_false",
    "source_corrected",
    "expert_confirmed",
    "expert_overridden",
)

ROLES = ("rater", "maintainer", "expert")
VERDICTS = ("CONFIRM", "REFUTE", "UNSOURCED", None)


def new_event_id() -> str:
    return uuid4().hex[:16]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def event(
    *,
    run_id: str,
    actor_role: str,
    actor_name: str,
    entity_id: str,
    field_path: str,
    recorded_at: Optional[str] = None,
    model: Optional[str] = None,
    prompt_version: Optional[str] = None,
    data_as_of: Optional[str] = None,
    value: Any = None,
    source_type: Optional[str] = None,
    source_url: Optional[str] = None,
    accessed_date: Optional[str] = None,
    verdict: Optional[str] = None,
    change_reason: Optional[str] = None,
    notes: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if actor_role not in ROLES:
        raise ValueError(f"actor.role must be one of {ROLES}")
    if change_reason is not None and change_reason not in CHANGE_REASONS:
        raise ValueError(f"change_reason must be one of {CHANGE_REASONS}")
    if verdict not in VERDICTS:
        raise ValueError(f"verdict must be one of {VERDICTS}")
    rec: Dict[str, Any] = {
        "event_id": new_event_id(),
        "run_id": run_id,
        "recorded_at": recorded_at or utc_now(),
        "actor": {
            "role": actor_role,
            "name": actor_name,
            "model": model,
            "prompt_version": prompt_version,
        },
        "entity_id": entity_id,
        "field_path": field_path,
        "data_as_of": data_as_of,
        "value": value,
        "source": {
            "type": source_type,
            "url": source_url,
            "accessed_date": accessed_date,
        },
        "verdict": verdict,
        "change_reason": change_reason,
        "notes": notes,
    }
    if extra:
        rec.update(extra)
    return rec


def append_events(path: Path, events: Iterable[Dict[str, Any]]) -> int:
    """Append records. Never rewrite an existing line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with path.open("a", encoding="utf-8") as fh:
        for rec in events:
            fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
            n += 1
    return n


def load_events(ledger_dir: Path) -> List[Dict[str, Any]]:
    """Load every JSONL event under ledger/events/ (and skip comment envelopes)."""
    rows: List[Dict[str, Any]] = []
    if not ledger_dir.exists():
        return rows
    for path in sorted(ledger_dir.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("record_type") == "comment":
                continue
            if not rec.get("entity_id") or not rec.get("field_path"):
                continue
            rows.append(rec)
    return rows


def project_value_history(events: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """Group by (entity_id, field_path), newest-first by recorded_at.

    This is the only sanctioned value_history. Canon YAML does not store it.
    """
    grouped: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for rec in events:
        eid = rec["entity_id"]
        fp = rec["field_path"]
        grouped.setdefault(eid, {}).setdefault(fp, []).append(rec)
    for eid, fields in grouped.items():
        for fp, items in fields.items():
            items.sort(key=lambda r: r.get("recorded_at") or "", reverse=True)
            fields[fp] = [
                {
                    "recorded_at": r.get("recorded_at"),
                    "value": r.get("value"),
                    "data_as_of": r.get("data_as_of"),
                    "change_reason": r.get("change_reason"),
                    "verdict": r.get("verdict"),
                    "source": r.get("source") or {},
                    "actor": r.get("actor") or {},
                    "notes": r.get("notes"),
                    "event_id": r.get("event_id"),
                    "run_id": r.get("run_id"),
                }
                for r in items
            ]
    return grouped
