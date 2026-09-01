#!/usr/bin/env python3
"""
JEM public inspection — read-only invariant audit.

The executable half of ledger/prompts/08_public_inspection_prompt.md. It edits
nothing and writes nowhere: it reads a JEM snapshot and emits a violations
report. Internally this is the critic rung; published, it is the community
verifier on-ramp. One artifact, two audiences.

Every check here is deterministic, so it is re-runnable in CI and gives the
same answer for everyone. The judgement calls the prompt reserves for a human
auditor (does this URL actually *contain* the integer) stay with the human;
what is mechanical is mechanised.

Checks (numbered as in the prompt):
  1  sourced numerics            — integers need a live, non-homepage source URL
  2  source-type eligibility     — no NJDG stamp on a non-eCourts body
  3  anomaly telltales           — 42-ladder, 365-day, round thousands, echoed rate
  4  generics not counted        — recompute buckets, compare to the artifact
  5  classification consistency  — every type maps to (nature, function)
  6  legal-basis integrity       — every instrument_id resolves to the registry
  7  report-publication negatives— a "no" needs a documented search trail
  8  suggested-not-applied       — dangling appellate endpoints are gaps, not errors
  9  prompt provenance           — ledger runs cite a registered prompt

Usage:
    python3 scripts/harness/inspect.py                 # offline structural checks
    python3 scripts/harness/inspect.py --liveness      # also HTTP-check source URLs
    python3 scripts/harness/inspect.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
from classification import TYPE_CLASSIFICATION, classify_entity, is_countable  # noqa: E402

SEV_HIGH, SEV_MED, SEV_LOW, SEV_INFO = "high", "medium", "low", "info"

# Body types that are not on eCourts, so an NJDG stamp cannot be their provenance.
NON_ECOURTS_TYPES = {
    "CentralTribunal", "StateTribunal", "ConsumerCommission", "ArbitralInstitution",
    "MediationBody", "RegulatoryBodyQJ", "ADRBody", "ExecutiveBody", "AppointmentBody",
    "InvestigativeAgency", "ProsecutionBody", "TrainingBody", "AuditBody",
    "DigitalInfraBody", "SecurityBody", "FinancingBody", "LegislativeBody",
    "ProfessionalBody", "LegalOfficer", "StatutoryBodyNotConstituted", "ProposedBody",
}

NJDG_SOURCE_MARKERS = ("njdg",)

APPELLATE_RELS = {"AppealableTo", "FinalAppealTo"}

# A negative finding has to show its work; these alone do not.
BARE_NEGATIVES = {
    "none found", "no reports found", "not found", "none", "n/a", "na",
    "no reports", "nothing found", "unknown",
}


class Report:
    def __init__(self):
        self.rows: List[Dict[str, Any]] = []

    def add(self, check_id, subject, field, observed, expected, evidence_url, severity):
        self.rows.append({
            "check_id": check_id,
            "entity_or_edge": subject,
            "field": field,
            "observed": observed,
            "expected": expected,
            "evidence_url": evidence_url,
            "severity": severity,
        })

    def by_check(self):
        out = defaultdict(list)
        for r in self.rows:
            out[r["check_id"]].append(r)
        return out


# ── loading ───────────────────────────────────────────────────────────────────

def load_entities(data_dir: Path) -> List[Dict[str, Any]]:
    entities = []
    for path in sorted((data_dir / "entities").rglob("*.yaml")):
        if "schema" in str(path):
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(doc, dict) and doc.get("id"):
            doc["__path"] = str(path)
            entities.append(doc)
    return entities


def load_relationships(data_dir: Path) -> List[Dict[str, Any]]:
    rels = []
    rel_dir = data_dir / "relationships"
    if not rel_dir.exists():
        return rels
    for path in sorted(rel_dir.glob("*.yaml")):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        for r in doc.get("relationships", []) or []:
            r["__path"] = str(path)
            rels.append(r)
    return rels


def load_instruments(data_dir: Path) -> Dict[str, Dict]:
    out = {}
    inst_dir = data_dir / "legal_instruments"
    if not inst_dir.exists():
        return out
    for path in sorted(inst_dir.rglob("*.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        rows = doc.get("instruments", [doc]) if isinstance(doc, dict) else []
        for row in rows:
            if row.get("id"):
                out[row["id"]] = row
    return out


def _basis_refs(value) -> List[Dict]:
    """Normalise a string-or-struct-or-list basis field to a list of refs."""
    if value is None or isinstance(value, str):
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [v for v in value if isinstance(v, dict)]
    return []


def _is_bare_homepage(url: str) -> bool:
    from urllib.parse import urlparse
    p = urlparse(url or "")
    return p.scheme and p.netloc and p.path in ("", "/") and not p.query


# ── checks ────────────────────────────────────────────────────────────────────

def check_1_sourced_numerics(entities, rep: Report, live_results: Optional[Dict] = None):
    """Every stored integer needs a source URL that is live and not a homepage."""
    for e in entities:
        for block_name in ("case_volume", "judge_strength"):
            block = e.get(block_name)
            if not isinstance(block, dict):
                continue
            integers = {k: v for k, v in block.items()
                        if isinstance(v, int) and not isinstance(v, bool)}
            if not integers:
                continue
            url = block.get("source_url")
            if not url:
                rep.add("1", e["id"], f"{block_name}.source_url", "missing",
                        "a source URL containing the value", None, SEV_HIGH)
                continue
            if _is_bare_homepage(url):
                rep.add("1", e["id"], f"{block_name}.source_url", f"bare homepage: {url}",
                        "a document URL containing the value", url, SEV_HIGH)
                continue
            if live_results is not None:
                res = live_results.get(url)
                if res and not res.get("ok"):
                    rep.add("1", e["id"], f"{block_name}.source_url",
                            f"liveness {res.get('reason')} (status {res.get('status')})",
                            "200, a real document", url, SEV_HIGH)


def check_2_source_type_eligibility(entities, rep: Report):
    """An NJDG stamp on a body that is not on eCourts cannot be its provenance."""
    for e in entities:
        etype = e.get("type")
        if etype not in NON_ECOURTS_TYPES:
            continue
        for block_name in ("case_volume", "judge_strength"):
            block = e.get(block_name)
            if not isinstance(block, dict):
                continue
            stype = (block.get("source_type") or "")
            surl = (block.get("source_url") or "")
            if stype.lower().startswith("njdg") or any(m in surl.lower() for m in NJDG_SOURCE_MARKERS):
                rep.add("2", e["id"], f"{block_name}.source_type",
                        f"{stype or surl} on type {etype}",
                        "a source eligible for this body type", surl or None, SEV_HIGH)
        for src in e.get("sources", []) or []:
            if (src.get("type") == "NJDG") or any(m in (src.get("url") or "").lower()
                                                  for m in NJDG_SOURCE_MARKERS):
                rep.add("2", e["id"], "sources[].type",
                        f"NJDG source on type {etype}",
                        "a source eligible for this body type", src.get("url"), SEV_MED)


def check_3_anomaly_telltales(entities, rep: Report):
    """Shapes that a number takes when it was reasoned to rather than read."""
    for e in entities:
        cv = e.get("case_volume")
        if not isinstance(cv, dict):
            continue
        eid = e["id"]

        # 42-ladder: 42 x 10^n
        for field in ("pending_cases", "filed_last_year", "disposed_last_year"):
            v = cv.get(field)
            if isinstance(v, int) and v > 0:
                s = str(v)
                if s.startswith("42") and s[2:] in ("", "0", "00", "000", "0000", "00000", "000000"):
                    rep.add("3", eid, f"case_volume.{field}", v,
                            "a sourced integer, not a 42-ladder value",
                            cv.get("source_url"), SEV_MED)

        if cv.get("avg_disposal_days") in (365, 365.0):
            rep.add("3", eid, "case_volume.avg_disposal_days", 365,
                    "a measured average, not exactly one year",
                    cv.get("source_url"), SEV_MED)

        pend = cv.get("pending_cases")
        if isinstance(pend, int) and pend >= 10000 and pend % 1000 == 0:
            rep.add("3", eid, "case_volume.pending_cases", pend,
                    "an exact figure, not a round thousand",
                    cv.get("source_url"), SEV_LOW)

        # A stored rate that exactly echoes disposed/filed is a recomputation,
        # not an independent datum.
        filed, disposed, rate = cv.get("filed_last_year"), cv.get("disposed_last_year"), cv.get("disposal_rate")
        if all(isinstance(x, (int, float)) for x in (filed, disposed, rate)) and filed:
            for scale in (1.0, 100.0):
                if abs(rate - (disposed / filed) * scale) < 1e-6:
                    rep.add("3", eid, "case_volume.disposal_rate", rate,
                            f"not an echo of disposed/filed ({disposed}/{filed})",
                            cv.get("source_url"), SEV_LOW)
                    break


def check_4_generics_not_counted(entities, data_dir: Path, rep: Report):
    """Recompute the buckets here and compare to the committed artifact."""
    counts_path = data_dir / "derived" / "entity_counts.yaml"
    buckets = {n: {f: 0 for f in ("judicial", "quasi_judicial", "support_apparatus")}
               for n in ("institution", "personnel")}
    generics = 0
    for e in entities:
        if not is_countable(e):
            generics += 1
            continue
        try:
            n, f = classify_entity(e)
        except ValueError:
            continue
        buckets[n][f] += 1

    if not counts_path.exists():
        rep.add("4", "data/derived/entity_counts.yaml", "-", "missing",
                "a committed derived counts artifact", None, SEV_MED)
        return buckets, generics

    artifact = (yaml.safe_load(counts_path.read_text()) or {}).get("entity_counts", {})
    a_buckets = artifact.get("buckets", {})
    for n in buckets:
        for f in buckets[n]:
            mine, theirs = buckets[n][f], (a_buckets.get(n) or {}).get(f)
            if mine != theirs:
                rep.add("4", "entity_counts.yaml", f"buckets.{n}.{f}", theirs,
                        f"{mine} (recomputed)", None, SEV_HIGH)
    if artifact.get("generics_excluded") != generics:
        rep.add("4", "entity_counts.yaml", "generics_excluded",
                artifact.get("generics_excluded"), f"{generics} (recomputed)", None, SEV_HIGH)

    # A generic must never be inside a bucket total.
    for e in entities:
        if e.get("is_generic_rollup") and str(e.get("id", "")).endswith("_generic") is False:
            rep.add("4", e["id"], "is_generic_rollup", True,
                    "flag set on an id that is not a *_generic rollup", None, SEV_LOW)
        if str(e.get("id", "")).endswith("_generic") and not e.get("is_generic_rollup"):
            rep.add("4", e["id"], "is_generic_rollup", e.get("is_generic_rollup"),
                    "true (id ends in _generic but flag is unset)", None, SEV_HIGH)
    return buckets, generics


def check_5_classification_consistency(entities, rep: Report):
    for e in entities:
        if e.get("classification_override"):
            if not e.get("data_quality_notes"):
                rep.add("5", e["id"], "classification_override", "override without justification",
                        "a justification in data_quality_notes", None, SEV_LOW)
            continue
        if e.get("type") not in TYPE_CLASSIFICATION:
            rep.add("5", e["id"], "type", e.get("type"),
                    "a type present in classification.py", None, SEV_HIGH)


def check_6_legal_basis_integrity(entities, relationships, instruments, rep: Report):
    """Every instrument_id must resolve; inline dates that duplicate the
    registry are the drift the registry exists to prevent."""
    def scan(obj, subject, field):
        for ref in _basis_refs(obj):
            iid = ref.get("instrument_id")
            if iid and iid not in instruments:
                rep.add("6", subject, field, f"dangling instrument_id: {iid}",
                        "an id present in data/legal_instruments/", None, SEV_HIGH)
                continue
            reg = instruments.get(iid) or {}
            for date_field, reg_field in (("effective_from", "commenced"),
                                          ("repealed_on", "repealed_on")):
                v = ref.get(date_field)
                if v and reg.get(reg_field) and str(v) == str(reg[reg_field]):
                    rep.add("6", subject, f"{field}.{date_field}", v,
                            f"reference {iid} rather than copying its {reg_field}",
                            None, SEV_INFO)

    for e in entities:
        scan(e.get("statutory_basis"), e["id"], "statutory_basis")
        scan(e.get("constitutional_basis"), e["id"], "constitutional_basis")
        pj = e.get("pecuniary_jurisdiction")
        if isinstance(pj, dict):
            scan(pj.get("basis"), e["id"], "pecuniary_jurisdiction.basis")
    for r in relationships:
        scan(r.get("statutory_basis"), r.get("id", "?"), "statutory_basis")
        scan(r.get("constitutional_basis"), r.get("id", "?"), "constitutional_basis")


def check_7_report_publication_negatives(entities, rep: Report):
    for e in entities:
        rp = e.get("report_publication")
        if not isinstance(rp, dict):
            continue
        if rp.get("publishes_reports") == "no":
            notes = (rp.get("notes") or "").strip()
            if not notes or notes.lower() in BARE_NEGATIVES or len(notes) < 25:
                rep.add("7", e["id"], "report_publication.notes", notes or "(empty)",
                        "a documented search trail: what was checked, where", None, SEV_HIGH)
        if rp.get("statutorily_required") == "yes" and rp.get("publishes_reports") == "no":
            rep.add("7", e["id"], "report_publication", "required by statute but not publishing",
                    "an accountability finding, flagged not softened",
                    rp.get("statutorily_required_source"), SEV_INFO)


def check_8_suggested_not_applied(entities, relationships, rep: Report):
    """A missing appellate endpoint is a gap to report, not an error to fix."""
    ids = {e["id"] for e in entities}
    for r in relationships:
        if r.get("relationship_type") not in APPELLATE_RELS:
            continue
        for end in ("source", "target"):
            node = r.get(end)
            if node and node not in ids:
                rep.add("8", r.get("id", "?"), end, f"{node} not in graph",
                        "a suggested entity/edge pending confirmation", None, SEV_INFO)


def check_10_published_totals_match(repo_root: Path, data_dir: Path, rep: Report):
    """Prose drifts; artifacts do not. Catch published totals that no longer
    match the derived counts.

    Documentation is the one place a hand-typed number can still hide after the
    counting reform, and it is exactly where the previous wrong total lived. Any
    figure quoted in the docs must be reproducible from entity_counts.yaml.
    """
    counts_path = data_dir / "derived" / "entity_counts.yaml"
    if not counts_path.exists():
        return
    counts = (yaml.safe_load(counts_path.read_text()) or {}).get("entity_counts", {})
    countable = counts.get("total_countable")
    files = counts.get("total_entity_files")
    generics = counts.get("generics_excluded")
    if countable is None:
        return

    def _fmt(n):
        return f"{n:,}"

    # Any of these numbers appearing in the docs must be the current one.
    expected = {
        "countable total": (countable, {_fmt(countable), str(countable)}),
        "entity file total": (files, {_fmt(files), str(files)}),
        "generics excluded": (generics, {_fmt(generics), str(generics)}),
    }

    docs = [repo_root.parent / "README.md", repo_root / "docs" / "ENTITY_BUILD_ROADMAP.md"]

    # A number in the corpus-total magnitude band that is not a current figure
    # is either stale or needs rewording. Exclusions keep the signal usable:
    # a bare year is not a count, and a figure marked "~" or "+" is explicitly
    # an estimate or a threshold rather than a claim about the corpus.
    # Python lookbehind must be fixed width, so the approximation word is
    # captured as an optional prefix group and tested afterwards.
    band = re.compile(
        r"(roughly |about |around |approx\.? |approximately |target |reaching |over |up to )?"
        r"(?<![\d,.~])(1,\d{3}|1\d{3})(?![\d,.+])", re.IGNORECASE)
    years = {str(y) for y in range(1900, 2101)}

    current = {v for _, (_, vs) in expected.items() for v in vs}
    current |= {_fmt(counts.get("buckets", {}).get(n, {}).get(f, -1))
                for n in ("institution", "personnel")
                for f in ("judicial", "quasi_judicial", "support_apparatus")}
    # Relationship totals are derived in build.py, not here, but are legitimate.
    allowed = current | {"1,797", "1797", "1,800", "1800"}

    for doc in docs:
        if not doc.exists():
            continue
        seen = set()
        for prefix, match in band.findall(doc.read_text(encoding="utf-8")):
            if prefix or match in allowed or match.replace(",", "") in years:
                continue
            if match in seen:
                continue
            seen.add(match)
            rep.add("10", doc.name, "published total", match,
                    f"a current derived figure (countable {_fmt(countable)}, "
                    f"files {_fmt(files)})", None, SEV_MED)


def check_9_prompt_provenance(repo_root: Path, rep: Report):
    registry_path = repo_root / "ledger" / "prompt_registry.yaml"
    if not registry_path.exists():
        rep.add("9", "ledger/prompt_registry.yaml", "-", "missing",
                "a committed prompt registry", None, SEV_MED)
        return
    registry = yaml.safe_load(registry_path.read_text()) or {}
    known = {p.get("prompt_id") for p in registry.get("prompts", [])}
    known |= {f"{p.get('prompt_id')}-{p.get('version')}" for p in registry.get("prompts", [])}

    # Registry rows must point at prompt artifacts that actually exist.
    for p in registry.get("prompts", []):
        rel = p.get("path")
        if rel and not (repo_root / rel).exists():
            rep.add("9", p.get("prompt_id"), "path", f"{rel} not present",
                    "a committed prompt artifact", None, SEV_MED)

    runs_dir = repo_root / "ledger" / "runs"
    if not runs_dir.exists():
        return
    for run in sorted(runs_dir.glob("*.jsonl")):
        for i, line in enumerate(run.read_text().splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            pv = rec.get("prompt_version") or rec.get("prompt_id")
            if pv is None:
                continue
            base = str(pv).rsplit("-v", 1)[0]
            if pv not in known and base not in known:
                rep.add("9", f"{run.name}:{i}", "prompt_version", pv,
                        "a prompt_id present in prompt_registry.yaml", None, SEV_MED)


# ── driver ────────────────────────────────────────────────────────────────────

CHECK_TITLES = {
    "1": "sourced numerics",
    "2": "source-type eligibility",
    "3": "anomaly telltales",
    "4": "generics not counted",
    "5": "classification consistency",
    "6": "legal-basis integrity",
    "7": "report-publication negatives",
    "8": "suggested-not-applied (gaps)",
    "9": "prompt provenance",
    "10": "published totals match derived",
}


def main():
    ap = argparse.ArgumentParser(description="JEM public inspection (read-only audit)")
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--liveness", action="store_true",
                    help="also HTTP-check every numeric source URL (network)")
    ap.add_argument("--json", default=None, help="write the violations report as JSON")
    ap.add_argument("--fail-on", default=None, choices=["high", "medium", "low"],
                    help="exit 1 if a violation at or above this severity exists")
    args = ap.parse_args()

    repo_root = _HERE.parent.parent
    data_dir = Path(args.data_dir) if args.data_dir else repo_root / "data"

    entities = load_entities(data_dir)
    relationships = load_relationships(data_dir)
    instruments = load_instruments(data_dir)

    print(f"JEM public inspection — read-only. Edits nothing.")
    print(f"  entities      {len(entities)}")
    print(f"  relationships {len(relationships)}")
    print(f"  instruments   {len(instruments)}")

    rep = Report()

    live_results = None
    if args.liveness:
        from harness.liveness import check_many
        urls = sorted({
            b.get("source_url")
            for e in entities
            for b in (e.get("case_volume"), e.get("judge_strength"))
            if isinstance(b, dict) and b.get("source_url")
        })
        print(f"\n  liveness-checking {len(urls)} numeric source URLs...")
        live_results = {u: r for u, r in zip(urls, check_many(urls, workers=10))}

    check_1_sourced_numerics(entities, rep, live_results)
    check_2_source_type_eligibility(entities, rep)
    check_3_anomaly_telltales(entities, rep)
    check_4_generics_not_counted(entities, data_dir, rep)
    check_5_classification_consistency(entities, rep)
    check_6_legal_basis_integrity(entities, relationships, instruments, rep)
    check_7_report_publication_negatives(entities, rep)
    check_8_suggested_not_applied(entities, relationships, rep)
    check_9_prompt_provenance(repo_root, rep)
    check_10_published_totals_match(repo_root, data_dir, rep)

    grouped = rep.by_check()
    print(f"\n{'='*78}")
    print("VIOLATIONS BY CHECK")
    print(f"{'='*78}")
    for cid in sorted(CHECK_TITLES):
        rows = grouped.get(cid, [])
        sev = ""
        if rows:
            counts = defaultdict(int)
            for r in rows:
                counts[r["severity"]] += 1
                sev = "  (" + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())) + ")"
        print(f"  check {cid}  {CHECK_TITLES[cid]:<32} {len(rows):>5}{sev}")

    total = len(rep.rows)
    highs = sum(1 for r in rep.rows if r["severity"] == SEV_HIGH)
    print(f"\n  total violations: {total}   (high: {highs})")

    for cid in sorted(grouped):
        rows = grouped[cid]
        print(f"\n── check {cid} · {CHECK_TITLES[cid]} — {len(rows)} ──")
        for r in rows[:25]:
            print(f"  [{r['severity']:<6}] {str(r['entity_or_edge'])[:38]:<38} "
                  f"{str(r['field'])[:30]:<30} observed={str(r['observed'])[:60]}")
        if len(rows) > 25:
            print(f"  ... and {len(rows)-25} more")

    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps({
            "summary": {cid: len(grouped.get(cid, [])) for cid in CHECK_TITLES},
            "total": total,
            "violations": rep.rows,
        }, indent=2, ensure_ascii=False))
        print(f"\nWrote {args.json}")

    if args.fail_on:
        order = {SEV_HIGH: 3, SEV_MED: 2, SEV_LOW: 1, SEV_INFO: 0}
        threshold = order[{"high": SEV_HIGH, "medium": SEV_MED, "low": SEV_LOW}[args.fail_on]]
        if any(order[r["severity"]] >= threshold for r in rep.rows):
            sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
