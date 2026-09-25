#!/usr/bin/env python3
"""
Liveness pre-gate — stage 0 of the intra-run consensus harness.

Deterministic, no LLM. Runs before any URL is accepted as a citation input, so
a dead or laundered link is rejected before a research token is spent. This is
simultaneously the correctness gate that kills homepage-backfill laundering and
the cheapest available token saver.

Reject when:
  - the response is not 200
  - the request redirects to the site root (homepage laundering)
  - the content-type contradicts the claim (HTML served where a PDF is claimed)
  - a bare homepage is cited where a document is claimed
  - the host answers 200 with a catch-all shell for any path (soft 404)

The soft-404 check is not optional decoration. Single-page-app government
portals (indiacode.gov.in since the Aug 2026 migration is the live example)
return an identical 200 shell for every URL including nonsense paths, so status
code alone would wave through a fabricated citation — the same laundering the
gate exists to stop, wearing a different hat.

Usage:
    python3 scripts/harness/liveness.py --url https://example.gov.in/report.pdf
    python3 scripts/harness/liveness.py --urls-file urls.txt --jsonl out.jsonl
    python3 scripts/harness/liveness.py --instruments      # registry URLs
    python3 scripts/harness/liveness.py --corpus-sample 50 # sample entity sources
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import random
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import urllib3
import yaml

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import requests
except ImportError:  # pragma: no cover
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/125.0 Safari/537.36 JEM-liveness-gate/1.0")

DOCUMENT_SUFFIXES = (".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv")
DOCUMENT_CONTENT_TYPES = ("application/pdf", "application/msword", "application/vnd",
                          "text/csv", "application/octet-stream")

# Reasons are stable identifiers so the ledger and CI can key off them.
PASS = "pass"
R_NON_200 = "non_200"
R_UNREACHABLE = "unreachable"
R_REDIRECT_ROOT = "redirects_to_root"
R_HOMEPAGE = "bare_homepage_for_document_claim"
R_TYPE_MISMATCH = "content_type_mismatch"
R_SOFT_404 = "soft_404_catch_all_shell"

# origin → fingerprint of that host's response to a guaranteed-absent path.
# None means the host correctly errors on nonsense, so 200 is meaningful there.
_CONTROL_CACHE: dict = {}
_CONTROL_PATH = "/jem-liveness-control-{}-should-not-exist"


def _fingerprint(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _control_fingerprint(url: str, timeout: int) -> Optional[str]:
    """Fingerprint the host's reply to a path that cannot exist.

    Returns None when the host behaves correctly (non-200 on nonsense), and a
    hash when it serves a catch-all 200 shell that any URL would also match.
    """
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin in _CONTROL_CACHE:
        return _CONTROL_CACHE[origin]

    fp = None
    try:
        probe = origin + _CONTROL_PATH.format(random.randint(10**6, 10**7))
        resp = requests.get(probe, allow_redirects=True, timeout=timeout,
                            headers={"User-Agent": UA}, verify=False)
        if resp.status_code == 200 and "text/html" in (resp.headers.get("Content-Type") or "").lower():
            fp = _fingerprint(resp.content)
    except Exception:
        fp = None

    _CONTROL_CACHE[origin] = fp
    return fp


def _is_bare_root(url: str) -> bool:
    """True when the URL carries no path/query — i.e. a site homepage."""
    p = urlparse(url)
    return p.path in ("", "/") and not p.query and not p.fragment


def _claims_document(url: str, expect_document: Optional[bool]) -> bool:
    if expect_document is not None:
        return expect_document
    return url.lower().split("?")[0].endswith(DOCUMENT_SUFFIXES)


def check(url: str, expect_document: Optional[bool] = None, timeout: int = 25,
          detect_soft_404: bool = True) -> dict:
    """Run the liveness pre-gate against one URL. Never raises."""
    started = time.time()
    result = {
        "url": url,
        "status": None,
        "final_url": None,
        "content_type": None,
        "is_document": None,
        "ok": False,
        "reason": None,
        "elapsed_ms": None,
    }

    wants_document = _claims_document(url, expect_document)
    headers = {"User-Agent": UA}
    body = None

    try:
        # Many government hosts reject or mishandle HEAD; fall back to GET.
        resp = requests.head(url, allow_redirects=True, timeout=timeout,
                             headers=headers, verify=False)
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if resp.status_code >= 400 or resp.status_code == 405 or "text/html" in ctype:
            resp = requests.get(url, allow_redirects=True, timeout=timeout,
                                headers=headers, verify=False)
            body = resp.content
    except Exception as exc:
        result["reason"] = R_UNREACHABLE
        result["error"] = f"{type(exc).__name__}: {exc}"[:200]
        result["elapsed_ms"] = int((time.time() - started) * 1000)
        return result

    ctype = (resp.headers.get("Content-Type") or "").lower()
    final_url = str(resp.url)
    result.update({
        "status": resp.status_code,
        "final_url": final_url,
        "content_type": ctype or None,
        "is_document": any(t in ctype for t in DOCUMENT_CONTENT_TYPES),
        "elapsed_ms": int((time.time() - started) * 1000),
    })

    if resp.status_code not in (200, 206):
        result["reason"] = R_NON_200
        return result

    # Redirected from a real path down to the site root => homepage laundering.
    if not _is_bare_root(url) and _is_bare_root(final_url):
        result["reason"] = R_REDIRECT_ROOT
        return result

    # A 200 means nothing on a host that serves one shell for every path.
    if detect_soft_404 and body is not None and "text/html" in ctype and not _is_bare_root(url):
        control = _control_fingerprint(url, timeout)
        if control and _fingerprint(body) == control:
            result["reason"] = R_SOFT_404
            result["soft_404_control_match"] = control[:16]
            return result

    if wants_document:
        if _is_bare_root(final_url):
            result["reason"] = R_HOMEPAGE
            return result
        if ctype and "text/html" in ctype:
            result["reason"] = R_TYPE_MISMATCH
            return result

    result["ok"] = True
    result["reason"] = PASS
    return result


def check_many(urls, expect_document=None, workers: int = 8, timeout: int = 25):
    """Concurrent liveness over an iterable of URLs. Order is preserved."""
    urls = list(urls)
    out = [None] * len(urls)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(check, u, expect_document, timeout): i for i, u in enumerate(urls)}
        for fut in concurrent.futures.as_completed(futs):
            out[futs[fut]] = fut.result()
    return out


# ── URL collectors ────────────────────────────────────────────────────────────

def _data_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "data"


def instrument_urls() -> list:
    """(instrument_id, url) for every source in the legal-instrument registry."""
    pairs = []
    inst_dir = _data_dir() / "legal_instruments"
    for f in sorted(inst_dir.rglob("*.yaml")):
        doc = yaml.safe_load(f.read_text()) or {}
        rows = doc.get("instruments", [doc]) if isinstance(doc, dict) else []
        for row in rows:
            for src in row.get("sources", []) or []:
                pairs.append((row.get("id"), src.get("url")))
    return pairs


def corpus_source_urls(sample: Optional[int] = None, seed: int = 0) -> list:
    """(entity_id, url) for every entity source URL, optionally sampled."""
    pairs = []
    for f in sorted((_data_dir() / "entities").rglob("*.yaml")):
        if "schema" in str(f):
            continue
        doc = yaml.safe_load(f.read_text())
        if not isinstance(doc, dict):
            continue
        for src in doc.get("sources", []) or []:
            url = src.get("url")
            if url:
                pairs.append((doc.get("id"), url))
    if sample and sample < len(pairs):
        random.Random(seed).shuffle(pairs)
        pairs = pairs[:sample]
    return pairs


def _report(rows, jsonl: Optional[str]):
    passed = sum(1 for r in rows if r["ok"])
    print(f"\n{'='*70}")
    print(f"Liveness pre-gate: {passed}/{len(rows)} passed")
    print(f"{'='*70}")

    by_reason = {}
    for r in rows:
        by_reason.setdefault(r["reason"], []).append(r)
    for reason, group in sorted(by_reason.items(), key=lambda kv: -len(kv[1])):
        print(f"  {len(group):4d}  {reason}")

    failures = [r for r in rows if not r["ok"]]
    if failures:
        print(f"\nFailures ({len(failures)}):")
        for r in failures:
            owner = f"[{r.get('owner')}] " if r.get("owner") else ""
            print(f"  {str(r['status']):>4}  {r['reason']:<34} {owner}{r['url'][:90]}")

    if jsonl:
        Path(jsonl).parent.mkdir(parents=True, exist_ok=True)
        with open(jsonl, "a", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\nAppended {len(rows)} records to {jsonl}")

    return passed == len(rows)


def main():
    ap = argparse.ArgumentParser(description="JEM liveness pre-gate (harness stage 0)")
    ap.add_argument("--url", help="check a single URL")
    ap.add_argument("--urls-file", help="file with one URL per line")
    ap.add_argument("--instruments", action="store_true",
                    help="check every source URL in data/legal_instruments/")
    ap.add_argument("--corpus-sample", type=int, default=None,
                    help="check a random sample of N entity source URLs")
    ap.add_argument("--expect-document", action="store_true",
                    help="treat every URL as claiming a document")
    ap.add_argument("--jsonl", default=None, help="append results to this JSONL ledger file")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=25)
    args = ap.parse_args()

    expect_doc = True if args.expect_document else None
    owners, urls = [], []

    if args.url:
        owners, urls = [None], [args.url]
    elif args.urls_file:
        urls = [l.strip() for l in Path(args.urls_file).read_text().splitlines() if l.strip()]
        owners = [None] * len(urls)
    elif args.instruments:
        pairs = instrument_urls()
        owners, urls = [p[0] for p in pairs], [p[1] for p in pairs]
    elif args.corpus_sample:
        pairs = corpus_source_urls(sample=args.corpus_sample)
        owners, urls = [p[0] for p in pairs], [p[1] for p in pairs]
    else:
        ap.error("one of --url / --urls-file / --instruments / --corpus-sample is required")

    print(f"Liveness-checking {len(urls)} URL(s) with {args.workers} workers...")
    rows = check_many(urls, expect_doc, workers=args.workers, timeout=args.timeout)
    for row, owner in zip(rows, owners):
        row["owner"] = owner
        row["checked_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    ok = _report(rows, args.jsonl)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
