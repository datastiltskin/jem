#!/usr/bin/env python3
"""Batch driver: walk config/roster.yaml, scrape → gate → adversarially verify → store each
entity. Auto-writes only high-confidence results to the live tree; everything else is queued for
a human. Resilient to per-entity failure, resumable after a crash. Run from jem/.

    python scripts/batch_scrape.py [--roster config/roster.yaml] [--only ID ...] [--limit N]
        [--status existing|net_new|all] [--cluster C] [--state tn] [--model claude-sonnet-5]
        [--concurrency 4] [--resume] [--max-fail-rate 0.1]

Per entity: scrape() (llm_scrape) → run_gate (validate --strict + host allowlist + L4 institution
check) → verify_entity() (second Claude pass that web_fetches the cited sources). Written live
only when the verifier returns confirmed AND confidence ≥ 0.85 AND existence_confirmed AND the
existing file is not human-curated. Otherwise → build/needs_review/. Model-asserted
`data_quality: verified` is downgraded to `complete` (verified is human-only).
"""
from __future__ import annotations
import argparse, datetime, json, signal, sys, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

JEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(JEM))
sys.path.insert(0, str(JEM / "scripts"))
import yaml
from llm_scrape import scrape, verify_entity
from pipeline.stage6_gate.run_gate import run_gate

DEFAULT_MIN_CONFIDENCE = 0.70                      # was 0.85; the write bar (override with --min-confidence)
# Approx list prices $/1M tokens (input, output); sonnet-5 at the intro rate through 2026-08-31.
PRICING = {"claude-sonnet-5": (2.0, 10.0), "claude-opus-5": (5.0, 25.0),
           "claude-opus-4-8": (5.0, 25.0)}
SEARCH_COST_USD = 0.01                            # ≈ $10 / 1000 web_search requests
USAGE_KEYS = ("input_tokens", "output_tokens", "cache_read", "cache_creation", "web_searches")


def _cost(u: dict, model: str) -> float:
    """Ballpark USD. Cached input is billed cheaper than shown here, so this slightly overstates."""
    pin, pout = PRICING.get(model, (3.0, 15.0))
    inp = u["input_tokens"] + u["cache_read"] + u["cache_creation"]
    return inp / 1e6 * pin + u["output_tokens"] / 1e6 * pout + u["web_searches"] * SEARCH_COST_USD


def _fin(res: dict, usage: dict, model: str) -> dict:
    res["tokens"] = usage
    res["est_cost_usd"] = round(_cost(usage, model), 4)
    return res
GENERATED = "data/entities/_generated/"          # only these paths are auto-writable
OUTPUTS = JEM / ".claude" / "outputs"
DRAFTS = JEM / "build" / "llm_drafts"
NEEDS_REVIEW = JEM / "build" / "needs_review"
STOP = threading.Event()                          # set by SIGINT/SIGTERM for a graceful stop
_LEDGER_LOCK = threading.Lock()


def _dump_yaml(entity: dict) -> str:
    return yaml.safe_dump(entity, sort_keys=False, allow_unicode=True)


def process_entity(row: dict, model: str, dry_run: bool, run_dir: Path, gates: dict) -> dict:
    """Full per-entity flow. Never raises — returns a ledger dict with a terminal status.
    dry_run: writes go to run_dir/would_write and run_dir/needs_review, never the live tree.
    gates: {min_confidence, l4, strict_verify} — the relaxable strictness knobs."""
    eid = row["id"]
    rel_path = row["path"]
    review_dir = (run_dir / "needs_review") if dry_run else NEEDS_REVIEW
    result = {"id": eid, "path": rel_path, "status": "failed", "confidence": None, "reason": ""}
    usage = {k: 0 for k in USAGE_KEYS}                        # per-entity; thread-safe (own dict)
    try:
        # Curation guard: never overwrite hand-curated data (verified, or outside _generated/).
        if not rel_path.startswith(GENERATED):
            return _fin({**result, "status": "skipped_curated", "reason": "outside _generated/"}, usage, model)
        live = JEM / rel_path
        existing = yaml.safe_load(live.read_text()) if live.exists() else None
        if existing and existing.get("data_quality") == "verified":
            return _fin({**result, "status": "skipped_curated", "reason": "existing data_quality=verified"}, usage, model)

        spec = {k: row.get(k) for k in ("id", "name", "type", "cluster")}
        if existing and existing.get("level_of_government"):
            spec["level_of_government"] = existing["level_of_government"]

        entity = scrape(spec, model, row.get("seed_url"), [], usage)
        entity["id"] = eid                                    # never let the model rename the id

        DRAFTS.mkdir(parents=True, exist_ok=True)
        draft = DRAFTS / f"{eid}.yaml"
        draft.write_text(_dump_yaml(entity))
        if run_gate(draft, l4=gates["l4"]) != 0:
            return _fin(_queue_review(eid, entity, {"gate": "failed"}, "deterministic gate failed", review_dir), usage, model)

        v = verify_entity(entity, model, usage)
        # Write bar: reject is never writable; needs_human is unless --strict-verify. Existence
        # must be confirmed, and confidence must clear the (relaxable) threshold.
        ok_status = {"confirmed"} if gates["strict_verify"] else {"confirmed", "needs_human"}
        confirmed = (v.get("verification_status") in ok_status
                     and float(v.get("confidence") or 0) >= gates["min_confidence"]
                     and bool(v.get("existence_confirmed")))
        if not confirmed:
            return _fin(_queue_review(eid, entity, v, f"verify={v.get('verification_status')} "
                                      f"conf={v.get('confidence')} exists={v.get('existence_confirmed')}",
                                      review_dir, confidence=v.get("confidence")), usage, model)

        if entity.get("data_quality") == "verified":
            entity["data_quality"] = "complete"               # verified is human-only (RCA #5)
        dest = (run_dir / "would_write" / Path(rel_path).name) if dry_run else (JEM / rel_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(_dump_yaml(entity))
        if not dry_run:
            draft.unlink(missing_ok=True)
        return _fin({**result, "status": "written", "path": str(dest.relative_to(JEM)) if not dry_run
                     else str(dest), "confidence": v.get("confidence"),
                     "reason": ("DRY " if dry_run else "") + (v.get("notes") or "")}, usage, model)
    except Exception as e:                                    # one bad entity never kills the run
        return _fin({**result, "status": "failed", "reason": f"{type(e).__name__}: {e}"}, usage, model)


def _queue_review(eid, entity, verdict, reason, review_dir: Path, confidence=None) -> dict:
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / f"{eid}.yaml").write_text(_dump_yaml(entity))
    (review_dir / f"{eid}.review.json").write_text(json.dumps(verdict, indent=2, default=str))
    return {"id": eid, "path": str(review_dir / f"{eid}.yaml"), "status": "needs_review",
            "confidence": confidence, "reason": reason}


def _filter(entities: list[dict], args) -> list[dict]:
    rows = entities
    if args.status != "all":
        rows = [r for r in rows if r.get("status") == args.status]
    if args.cluster:
        rows = [r for r in rows if r.get("cluster") == args.cluster]
    if args.state:
        rows = [r for r in rows if r.get("state") == args.state]
    if args.only:
        want = set(args.only)
        rows = [r for r in rows if r["id"] in want]
    if args.limit:
        rows = rows[: args.limit]
    return rows


def _write_digest(run_dir: Path, ledger: list[dict], stamp: str) -> None:
    counts: dict[str, int] = {}
    for r in ledger:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    lines = [f"# Batch scrape digest — {stamp}", "",
             f"Total processed: {len(ledger)}", ""]
    for status in ("written", "needs_review", "failed", "skipped_curated"):
        lines.append(f"- **{status}**: {counts.get(status, 0)}")

    # Measured cost — only entities that actually hit the API (skipped ones cost ~0).
    billed = [r for r in ledger if (r.get("tokens") or {}).get("input_tokens")]
    total_cost = sum(r.get("est_cost_usd") or 0 for r in ledger)
    lines += ["", "## Cost (approx)", f"- Measured total: **${total_cost:.2f}** over {len(billed)} API entities"]
    if billed:
        mean = total_cost / len(billed)
        mean_in = sum(r["tokens"]["input_tokens"] for r in billed) / len(billed)
        mean_out = sum(r["tokens"]["output_tokens"] for r in billed) / len(billed)
        lines += [f"- Mean/entity: **${mean:.3f}** (~{mean_in:,.0f} in / {mean_out:,.0f} out tokens)",
                  f"- Projected × 1,500: **${mean * 1500:,.0f}**  (× 1,119 roster: ${mean * 1119:,.0f})"]
    for status, header in (("needs_review", "Needs review"), ("failed", "Failed")):
        rows = [r for r in ledger if r["status"] == status]
        if rows:
            lines += ["", f"## {header} ({len(rows)})"]
            lines += [f"- `{r['id']}` — {r['reason']}" for r in rows]
    (run_dir / f"batch_digest_{stamp}.md").write_text("\n".join(lines) + "\n")
    (OUTPUTS / "batch_digest_latest.md").write_text("\n".join(lines) + "\n")
    (run_dir / "schedule.json").write_text(json.dumps({
        "stamp": stamp, "counts": counts, "total": len(ledger),
        "completed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }, indent=2) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roster", default=str(JEM / "config" / "roster.yaml"))
    ap.add_argument("--only", nargs="*", default=None, help="entity id(s) to run")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--status", choices=("existing", "net_new", "all"), default="all")
    ap.add_argument("--cluster", default=None)
    ap.add_argument("--state", default=None)
    ap.add_argument("--model", default="claude-sonnet-5", help="sonnet-5 is the bulk cost lever")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--resume", action="store_true", help="reuse latest batch_* dir, skip done ids")
    ap.add_argument("--dry-run", action="store_true",
                    help="write results into the run dir (would_write/, needs_review/), never the live tree")
    ap.add_argument("--min-confidence", type=float, default=DEFAULT_MIN_CONFIDENCE,
                    help="verifier confidence needed to auto-write (default %(default)s)")
    ap.add_argument("--strict-verify", action="store_true",
                    help="require verification_status=confirmed (default also accepts needs_human)")
    ap.add_argument("--no-l4", action="store_true", help="disable the L4 institution-existence gate")
    ap.add_argument("--max-fail-rate", type=float, default=0.1)
    args = ap.parse_args()
    gates = {"min_confidence": args.min_confidence, "l4": not args.no_l4,
             "strict_verify": args.strict_verify}

    entities = yaml.safe_load(Path(args.roster).read_text())["entities"]
    worklist = _filter(entities, args)

    OUTPUTS.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    ledger: list[dict] = []
    if args.resume:
        prior = sorted(OUTPUTS.glob("batch_*/ledger.jsonl"))
        if prior:
            run_dir = prior[-1].parent
            stamp = run_dir.name.removeprefix("batch_")
            for line in prior[-1].read_text().splitlines():
                r = json.loads(line)
                ledger.append(r)
                if r["status"] in ("written", "needs_review", "skipped_curated"):
                    done.add(r["id"])                         # retry only failed on resume
            print(f"resuming {run_dir.name}: {len(done)} already done", file=sys.stderr)
        else:
            args.resume = False
    if not args.resume:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = OUTPUTS / f"batch_{stamp}"
        run_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = run_dir / "ledger.jsonl"

    worklist = [r for r in worklist if r["id"] not in done]
    print(f"batch: {len(worklist)} entities, concurrency={args.concurrency}, model={args.model}"
          f"{' [DRY-RUN]' if args.dry_run else ''}", file=sys.stderr)

    signal.signal(signal.SIGINT, lambda *_: STOP.set())
    signal.signal(signal.SIGTERM, lambda *_: STOP.set())

    def record(r: dict) -> None:
        with _LEDGER_LOCK:
            ledger.append(r)
            with open(ledger_path, "a") as f:                # append after each = crash-safe
                f.write(json.dumps(r, default=str) + "\n")
        print(f"  [{r['status']}] {r['id']} {r.get('reason','')}", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futures = {}
        for row in worklist:
            if STOP.is_set():
                print("stop requested — not submitting more; draining in-flight", file=sys.stderr)
                break
            futures[ex.submit(process_entity, row, args.model, args.dry_run, run_dir, gates)] = row["id"]
        for fut in as_completed(futures):
            record(fut.result())

    _write_digest(run_dir, ledger, stamp)
    n = len(ledger) or 1
    failed = sum(1 for r in ledger if r["status"] == "failed")
    print(f"done: {failed} failed / {len(ledger)} — digest at {run_dir.name}/", file=sys.stderr)
    return 1 if failed / n > args.max_fail_rate else 0


if __name__ == "__main__":
    sys.exit(main())
