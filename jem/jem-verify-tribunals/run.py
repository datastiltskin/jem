#!/usr/bin/env python3
"""
run.py — Prajna · DeepSeek verifier loop for JEM verify-trib-01 (batch verify-trib-01).

Verifies every (entity_id, field) claim in inputs/claims_to_verify.csv against
PRIMARY sources fetched from the live web, and emits into out/:

    {model}__verify-trib-01__{user}__{timestamp}.csv      (one row per claim)
    {model}__verify-trib-01__{user}__{timestamp}.meta.json
    fetch_log/                                            (saved sources, for audit)

Pull-not-push: this script never writes into the JEM repo — out/ only.

Prompt discipline (calibration study!):
  - System prompt = rater card (inputs/prajna_deepseek_card.md) + verifier prompt
    (inputs/verifier_prompt.md), both read byte-identical from disk.
  - temperature 0.2, web search ON, context arm: provided files + web search only.
  - The model never "answers from memory": per entity the script (a) asks the model
    to PLAN which queries/URLs to fetch, (b) performs those searches + fetches and
    saves every doc to fetch_log/, (c) only then asks the model for VERDICTS, fed
    with the fetched text.

Loop mechanics (per RUN_SETUP.md):
  - one entity per iteration, rows appended incrementally and flushed per entity,
    so a crash loses at most the current entity;
  - SAT anchor self-check (1,066 / 429 / 323 from SEBI AR 2025-26 Table 10.35)
    runs FIRST; if the verifier instead CONFIRMs the stale 420/380/345/365, the
    run stops and flags (per card: "stop and flag");
  - --resume skips entities already fully present in the output CSV.

Zero hard dependencies: Python >= 3.8 stdlib (urllib). Optional: pypdf for PDF
text extraction (skipped gracefully if unavailable — raw PDFs still saved).

Usage:
    export DEEPSEEK_API_KEY=sk-...            # required (LLM)
    export TAVILY_API_KEY=tvly-...            # or SERPAPI_API_KEY=...  (search)
    python3 run.py                            # full 44-entity pass
    python3 run.py --entities sat,ngt         # subset
    python3 run.py --resume                   # continue an interrupted pass
    python3 run.py --search-backend direct    # fetch-only, no discovery
    python3 run.py --selftest                 # plumbing check, no network/LLM
    python3 run.py --dry-run                  # plan only, no network/LLM
"""

import argparse
import csv
import getpass
import glob
import hashlib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants — do not edit unless you are DSo (they affect comparability)
# ---------------------------------------------------------------------------

BATCH_ID = "verify-trib-01"
PROMPT_VERSION = "verify-trib-v1"
EXPECTED_ENTITIES_N = 44

HERE = os.path.dirname(os.path.abspath(__file__))
INPUTS = os.path.join(HERE, "inputs")
OUT = os.path.join(HERE, "out")
FETCH_LOG = os.path.join(OUT, "fetch_log")
PROMPT_PATH = os.path.join(INPUTS, "verifier_prompt.md")
CARD_PATH = os.path.join(INPUTS, "prajna_deepseek_card.md")
CLAIMS_DEFAULT = os.path.join(INPUTS, "claims_to_verify.csv")

# Exact output header from verifier_prompt.md (do not reorder/rename).
OUTPUT_HEADER = [
    "entity_id", "type", "field", "current_value", "current_source_type",
    "current_source_url", "verdict", "verified_value", "verified_as_of",
    "source_class", "source_title", "source_url", "table_or_section",
    "verbatim_excerpt", "primary_count", "independent_secondary_count",
    "confidence_tier", "njdg_stamp_valid", "anomaly_flags", "notes",
]

VERDICTS = {"CONFIRM", "REFUTE", "UNSOURCED", "NA"}
TIERS = {"UNSOURCED", "partial", "partial_approaching_complete", "complete", "verified"}

NUMERIC_FIELDS = [
    "pending_cases", "filed_last_year", "disposed_last_year",
    "disposal_rate", "avg_disposal_days",
]

# Source-map hints condensed from verifier_prompt.md §SOURCE MAP, keyed by type.
SRC_HINTS = {
    "CentralTribunal": (
        "SAT -> SEBI Annual Report (anchor FY25-26 Ch.10 Table 10.35: pending 1,066 / "
        "filed 429 / disposed 323 — re-verify, do not copy). NCLT/NCLAT -> MCA Annual "
        "Report, IBBI quarterly newsletters. ITAT -> Finance/Dept of Revenue reports, "
        "Lok Sabha replies. CESTAT -> CBIC/Finance, Lok Sabha replies. AFT -> MoD Annual "
        "Report, Lok Sabha replies. CAT -> DoPT Annual Report, Lok Sabha replies. DRT/DRAT "
        "-> Dept of Financial Services/Finance, Lok Sabha replies. NGT -> greentribunal.gov.in "
        "bench-wise pendency dashboard. APTEL/TDSAT -> own sites / parent-ministry reports."
    ),
    "RegulatoryBodyQJ": (
        "SEBI/TRAI/IRDAI/CCI -> own annual reports (order/adjudication statistics). "
        "RERAs (mh/ka/tn/dl) & ERCs (tnerc/merc/derc/kerc) -> state RERA / commission "
        "annual reports."
    ),
    "ConsumerCommission": (
        "NCDRC / state / district CDRC -> NCDRC / CONFONET / e-Daakhil statistics; "
        "consumerhelpline dashboards."
    ),
    "ADRBody": (
        "NALSA / SLSAs / Lok Adalat -> NALSA annual reports + Lok Adalat disposal statistics."
    ),
    "ArbitralInstitution": (
        "DIAC / IIAC / MCIA -> institutional caseload pages; if genuinely unpublished -> NA."
    ),
}

# DeepSeek API defaults (OpenAI-compatible). Current pricing per
# https://api-docs.deepseek.com/quick_start/pricing (off-peak deepseek-v4-flash).
DEEPSEEK_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
PRICE_IN_PER_M = float(os.environ.get("DEEPSEEK_PRICE_IN_USD_PER_M", "0.22"))
PRICE_OUT_PER_M = float(os.environ.get("DEEPSEEK_PRICE_OUT_USD_PER_M", "0.66"))

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def log(msg):
    print(f"[{datetime.now(timezone.utc):%H:%M:%S}] {msg}", file=sys.stderr, flush=True)


def now_utc():
    return datetime.now(timezone.utc)


def utc_stamp():
    return now_utc().strftime("%Y%m%d_%H%M%S")


def fail(msg, code=2):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------------------
# Input loading
# ---------------------------------------------------------------------------


def load_claims(path):
    # Tolerate the documented spelling (claims_to_verify.csv) and the variant
    # that has appeared on disk (claim_to_verify.csv).
    if not os.path.exists(path):
        alt = path.replace("claims_to_verify.csv", "claim_to_verify.csv")
        if os.path.exists(alt):
            log(f"claims CSV found at {alt} (renamed variant)")
            path = alt
    if not os.path.exists(path):
        cands = [os.path.basename(p) for p in glob.glob(os.path.join(INPUTS, "*to_verify*.csv"))]
        fail(f"claims CSV not found at {path}. candidates in inputs/: {cands or 'none'}")
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        fail(f"{path} is empty or has no header")
    req = {"entity_id", "type", "field", "current_value",
           "current_source_type", "current_source_url", "data_as_of"}
    got = set(rows[0].keys())
    if not req <= got:
        fail(f"{path} header missing columns: {sorted(req - got)}")
    by_entity = {}
    for r in rows:
        by_entity.setdefault(r["entity_id"], []).append(r)
    return rows, by_entity


def load_prompt_files():
    if not os.path.exists(PROMPT_PATH):
        fail(f"missing {PROMPT_PATH} — pin it read-only (RUN_SETUP.md)")
    if not os.path.exists(CARD_PATH):
        fail(f"missing {CARD_PATH}")
    with open(PROMPT_PATH, encoding="utf-8") as f:
        prompt = f.read()
    with open(CARD_PATH, encoding="utf-8") as f:
        card = f.read()
    # Card goes ABOVE the verifier prompt; system prompt must stay byte-identical
    # to what both raters paste, per prajna_deepseek_card.md.
    return card + "\n\n" + prompt


# ---------------------------------------------------------------------------
# HTTP fetch layer (stdlib). Saves every fetch into out/fetch_log/ for audit.
# ---------------------------------------------------------------------------


def _http(method, url, payload=None, headers=None, timeout=30):
    req = urllib.request.Request(url, method=method, headers=headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=data, timeout=timeout) as resp:
        return resp.status, resp.headers, resp.read()


def fetch_bytes(url, timeout=30):
    """GET a URL, return (status, final_url, content_type, body_bytes)."""
    req = urllib.request.Request(
        url, method="GET",
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        final = resp.geturl() or url
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].lower()
        return resp.status, final, ctype, body


def _slug(url, maxlen=60):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", urllib.parse.urlparse(url).netloc + "-" + url.split("/")[-1][:40])
    return s.strip("-")[:maxlen]


def save_to_fetch_log(entity_id, idx, url, body):
    """Persist raw bytes; return the saved path. Never raises."""
    try:
        os.makedirs(FETCH_LOG, exist_ok=True)
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
        name = f"{utc_stamp()}_{entity_id}_{idx}_{digest}-{_slug(url)}.bin"
        path = os.path.join(FETCH_LOG, name)
        with open(path, "wb") as f:
            f.write(body)
        return path
    except Exception as e:  # audit log must never kill the run
        log(f"  ! fetch_log save failed for {url}: {e}")
        return ""


def html_to_text(html_bytes):
    txt = html_bytes.decode("utf-8", errors="replace")
    txt = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", txt)
    txt = re.sub(r"(?s)<[^>]+>", " ", txt)
    txt = html.unescape(txt)
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt)
    return txt.strip()


def pdf_to_text(body_bytes):
    try:
        from pypdf import PdfReader
        import io
        reader = PdfReader(io.BytesIO(body_bytes))
        parts = []
        for page in reader.pages[:40]:
            try:
                parts.append(page.extract_text() or "")
            except Exception:
                continue
        return "\n".join(parts).strip()
    except ImportError:
        return ""  # pypdf not installed: raw PDF is still saved to fetch_log


def extract_text(ctype, body_bytes):
    if "pdf" in ctype:
        txt = pdf_to_text(body_bytes)
        if txt:
            return txt, "pdf"
        return "", "pdf(raw-only)"
    if "html" in ctype or ctype in ("", "text/plain"):
        return html_to_text(body_bytes), "html"
    return "", ctype or "unknown"


def fetch_document(entity_id, idx, url, timeout=30):
    """Fetch + extract + save. Returns dict or None on hard failure."""
    try:
        status, final, ctype, body = fetch_bytes(url, timeout=timeout)
    except urllib.error.HTTPError as e:
        log(f"  fetch {url} -> HTTP {e.code}")
        return {"url": url, "error": f"HTTP {e.code}"}
    except Exception as e:
        log(f"  fetch {url} -> {e}")
        return {"url": url, "error": str(e)}
    saved = save_to_fetch_log(entity_id, idx, url, body)
    if status >= 400:
        return {"url": url, "error": f"HTTP {status}"}
    text, kind = extract_text(ctype, body)
    if not text:
        return {"url": url, "error": f"no extractable text ({kind})", "saved": saved}
    return {
        "url": final, "title": "", "kind": kind,
        "text": text, "saved": saved, "chars": len(text),
    }


# ---------------------------------------------------------------------------
# Search backends (Tavily / SerpAPI / direct). Search is discovery only —
# verdicts are always grounded in full fetched documents.
# ---------------------------------------------------------------------------


def resolve_search_backend(args):
    if args.search_backend == "direct":
        return "direct"
    if args.search_backend:
        return args.search_backend
    if os.environ.get("TAVILY_API_KEY"):
        return "tavily"
    if os.environ.get("SERPAPI_API_KEY"):
        return "serpapi"
    fail(
        "no search backend: set TAVILY_API_KEY or SERPAPI_API_KEY, or pass "
        "--search-backend direct (fetch-only). Per prajna_deepseek_card.md: if you "
        "cannot wire a fetch tool, stop and tell DSo before running."
    )


def search_tavily(query, max_results):
    key = os.environ.get("TAVILY_API_KEY")
    status, _, body = _http(
        "POST", "https://api.tavily.com/search",
        payload={"api_key": key, "query": query, "search_depth": "basic",
                 "max_results": max_results},
        timeout=40,
    )
    if status != 200:
        raise RuntimeError(f"tavily HTTP {status}: {body[:200]!r}")
    data = json.loads(body)
    return [{"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": r.get("content", "")}
            for r in data.get("results", []) if r.get("url")]


def search_serpapi(query, max_results):
    key = os.environ.get("SERPAPI_API_KEY")
    qs = urllib.parse.urlencode({"q": query, "engine": "google", "num": max_results,
                                 "api_key": key})
    status, _, body = _http("GET", f"https://serpapi.com/search.json?{qs}", timeout=40)
    if status != 200:
        raise RuntimeError(f"serpapi HTTP {status}: {body[:200]!r}")
    data = json.loads(body)
    return [{"title": r.get("title", ""), "url": r.get("link", ""),
             "snippet": r.get("snippet", "")}
            for r in data.get("organic_results", []) if r.get("link")]


def search(backend, query, max_results):
    if backend == "tavily":
        return search_tavily(query, max_results)
    if backend == "serpapi":
        return search_serpapi(query, max_results)
    return []  # direct mode: no discovery


# ---------------------------------------------------------------------------
# DeepSeek chat (OpenAI-compatible). JSON output mode.
# ---------------------------------------------------------------------------


class LLM:
    def __init__(self, api_key, model, base, temperature, max_retries=3):
        self.api_key = api_key
        self.model = model
        self.base = base.rstrip("/")
        self.temperature = temperature
        self.max_retries = max_retries
        self.tokens_in = 0
        self.tokens_out = 0

    def chat_json(self, system, user_msgs, max_tokens=8000, tag=""):
        """Send messages, return parsed JSON (dict or list) + usage. Retries on
        transport/5xx/429 and on invalid JSON; gives up with a clear error."""
        messages = [{"role": "system", "content": system}]
        messages += [{"role": "user", "content": m} for m in user_msgs]
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"},
            "max_tokens": max_tokens,
            "stream": False,
        }
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                status, _, body = _http(
                    "POST", f"{self.base}/chat/completions", payload=payload,
                    headers={"Authorization": f"Bearer {self.api_key}"}, timeout=120,
                )
            except Exception as e:
                last_err = f"transport: {e}"
                time.sleep(2 * attempt)
                continue
            if status != 200:
                last_err = f"HTTP {status}: {body[:300]!r}"
                if status == 429 or status >= 500:
                    time.sleep(5 * attempt)
                    continue
                break
            data = json.loads(body)
            usage = data.get("usage") or {}
            self.tokens_in += int(usage.get("prompt_tokens", 0))
            self.tokens_out += int(usage.get("completion_tokens", 0))
            content = data["choices"][0]["message"]["content"]
            parsed = parse_json(content)
            if parsed is not None:
                return parsed
            last_err = "model returned non-JSON content"
            user_msgs.append(
                f"Your previous response was not valid JSON ({last_err}). "
                "Reply with ONLY a single JSON object. "
                f"Raw response was: {content[:500]!r}"
            )
        raise RuntimeError(f"{tag} failed after {self.max_retries} attempts: {last_err}")


def parse_json(content):
    """Extract the first JSON value from model output (tolerates fences)."""
    if not content:
        return None
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    # Try whole-body first, then first {...} / [...] block.
    for candidate in (text,):
        try:
            return json.loads(candidate)
        except Exception:
            pass
    for m in re.finditer(r"(\{.*\}|\[.*\])", text, re.S):
        try:
            return json.loads(m.group(0))
        except Exception:
            continue
    return None


# ---------------------------------------------------------------------------
# Per-entity loop: plan -> fetch -> verify
# ---------------------------------------------------------------------------


def precompute_anomaly_flags(row):
    """Mechanical anomaly flags from verifier_prompt.md §ANOMALY FLAGS."""
    flags = []
    field, val = row["field"], row["current_value"]
    url, stype = row["current_source_url"], row["current_source_type"]
    try:
        iv = int(val)
        if field in ("pending_cases", "filed_last_year", "disposed_last_year") \
                and iv > 0 and iv % 42 == 0:
            flags.append("42-ladder")
        if field == "avg_disposal_days" and iv == 365:
            flags.append("365-day")
        if field in ("pending_cases",) and iv % 1000 == 0:
            flags.append("round-thousand")
    except (TypeError, ValueError):
        pass
    if field == "disposal_rate":
        flags.append("stored-rate")  # always recompute; mismatch flagged separately
    if stype in ("AnnualReport", "DoJ_Report", "Tribunal_Report"):
        if not url:
            flags.append("empty-url")
        elif urllib.parse.urlparse(url).path in ("", "/"):
            flags.append("homepage-url")
    return flags


def plan_prompt(entity_id, etype, claims, hints):
    lines = [f"- {c['entity_id']} | {c['field']} | {c['current_value']} | "
             f"{c['current_source_type']} | {c['current_source_url']} | {c['data_as_of']}"
             for c in claims]
    return (
        "OPERATOR NOTE: You are inside the automated verifier loop. The script "
        "performs all web searching and fetching for you — you do not call tools. "
        "Reply with ONLY a single JSON object.\n\n"
        f"ENTITY: {entity_id} ({etype})\n"
        f"CLAIMS UNDER TEST (entity_id | field | current_value | source_type | source_url | data_as_of):\n"
        + "\n".join(lines) + "\n\n"
        f"SOURCE MAP HINTS: {hints}\n\n"
        "TASK: Propose what the script should fetch to verify these claims against PRIMARY "
        "sources (annual reports, ministry/DoJ/Lok Sabha/PIB documents). Return JSON:\n"
        '{"fetch_items": [{"kind": "search"|"url", "query": "..." , "url": "https://..." , '
        '"reason": "..."}]}\n'
        "Max 6 items. Prefer direct document URLs (the PDF/page that CONTAINS the numbers, "
        "with table/section names) when you know them; use searches when you do not. "
        "Stored source URLs that are empty or homepages are SUSPECT — do not rely on them. "
        "For the SAT anchor, SEBI AR FY25-26 Chapter 10 Table 10.35 is the target."
    )


def verify_prompt(entity_id, etype, claims, evidence, failed, precomputed):
    claim_lines = [
        f"- {c['entity_id']} | {c['field']} | {c['current_value']} | "
        f"{c['current_source_type']} | {c['current_source_url']} | {c['data_as_of']}"
        for c in claims
    ]
    flag_lines = [
        f"- {c['entity_id']}|{c['field']}: {', '.join(precomputed[c['entity_id']][c['field']]) or 'none'}"
        for c in claims
    ]
    ev_lines = []
    for i, e in enumerate(evidence, 1):
        head = f"[{i}] url={e['url']}"
        if e.get("title"):
            head += f" title={e['title']!r}"
        if e.get("saved"):
            head += f" saved={e['saved']}"
        ev_lines.append(head)
        ev_lines.append("    " + (e["text"][:6000].replace("\n", " ") or "(no text)"))
    fail_lines = [f"- {u}" for u in failed]
    pairs = [f'"{c["entity_id"]}|{c["field"]}"' for c in claims]
    return (
        "OPERATOR NOTE: You are inside the automated verifier loop. The fetched "
        "documents below are your ONLY evidence. Reply with ONLY a single JSON object.\n\n"
        f"ENTITY: {entity_id} ({etype})\n"
        f"CLAIMS UNDER TEST (entity_id | field | current_value | source_type | source_url | data_as_of):\n"
        + "\n".join(claim_lines) + "\n\n"
        "OPERATOR-PRECOMPUTED ANOMALY FLAGS (mechanical: 42-ladder, 365-day, round-thousand, "
        "empty/homepage URL, stored-rate). Confirm or amend; they are hints, not verdicts:\n"
        + "\n".join(flag_lines) + "\n\n"
        "FETCHED EVIDENCE (live web; full copies in out/fetch_log/):\n"
        + ("\n".join(ev_lines) if ev_lines else "(none fetched)")
        + "\n\nFAILED FETCHES (attempted, no content):\n"
        + ("\n".join(fail_lines) if fail_lines else "(none)")
        + "\n\n"
        "KEY RULES (from your system prompt):\n"
        "- Verdicts: CONFIRM / REFUTE / UNSOURCED / NA. No primary contains the integer -> "
        "UNSOURCED, recommend withdraw. A secondary can raise confidence but NEVER justifies "
        "keeping an integer. India Code / statute text is not a case count.\n"
        "- NJDG is invalid for EVERY entity in this set (none are eCourts). For "
        "njdg_source_stamp rows: current_value 'present' -> njdg_stamp_valid FALSE, notes "
        "'recommend strip NJDG source'; 'absent' -> TRUE.\n"
        "- Recompute disposal_rate = disposed/filed to 4 dp; compare with stored; flag "
        "any mismatch.\n"
        "- Record the DIRECT URL of the document containing the number, table/section name, "
        "and a short verbatim excerpt. On failed fetch record the attempted URL in notes; "
        "never substitute a guess. Do NOT average conflicting figures — surface both in notes.\n\n"
        "TASK: Emit verdict rows for EXACTLY these (entity_id, field) pairs:\n"
        + ", ".join(pairs) + "\n\n"
        'Return JSON: {"rows": [ {entity_id, type, field, current_value, current_source_type, '
        'current_source_url, verdict, verified_value, verified_as_of, source_class, source_title, '
        'source_url, table_or_section, verbatim_excerpt, primary_count, '
        'independent_secondary_count, confidence_tier, njdg_stamp_valid, anomaly_flags, notes}, ... ]}\n'
        "One object per pair. Fill every field: '' for empty strings, 0 for counts, '' for "
        "njdg_stamp_valid on non-NJDG rows. anomaly_flags: comma-separated or ''."
    )


def process_entity(entity_id, claims, system, llm, args, backend):
    etype = claims[0]["type"]
    hints = SRC_HINTS.get(etype, "")
    log(f"entity {entity_id} ({etype}): {len(claims)} claims")

    # --- Phase 1: plan -----------------------------------------------------
    plan = llm.chat_json(system, [plan_prompt(entity_id, etype, claims, hints)],
                         max_tokens=3000, tag=f"{entity_id}/plan")
    items = (plan or {}).get("fetch_items") or []
    if not items:
        log(f"  ! model proposed no fetch items for {entity_id}; falling back to stored URLs")
        items = [{"kind": "url", "url": c["current_source_url"], "reason": "stored"}
                 for c in claims if c["current_source_url"]][:4]

    # --- Phase 2: execute (search + fetch), save everything ----------------
    evidence, failed = [], []
    idx = 0
    budget = args.evidence_budget_chars
    for item in items[:args.max_fetch_items]:
        if budget <= 0:
            break
        if item.get("kind") == "search" and backend != "direct" and item.get("query"):
            try:
                results = search(backend, item["query"], args.search_results)
            except Exception as e:
                log(f"  ! search failed: {e}")
                results = []
            for r in results[:args.search_results]:
                if budget <= 0:
                    break
                doc = fetch_document(entity_id, idx, r["url"], timeout=args.fetch_timeout)
                idx += 1
                if doc and doc.get("text"):
                    doc["title"] = r.get("title", "")
                    doc["snippet"] = r.get("snippet", "")
                    doc["text"] = doc["text"][:budget]
                    budget -= len(doc["text"])
                    evidence.append(doc)
                elif doc:
                    failed.append(doc["url"])
        elif item.get("kind") == "url" and item.get("url"):
            doc = fetch_document(entity_id, idx, item["url"], timeout=args.fetch_timeout)
            idx += 1
            if doc and doc.get("text"):
                doc["text"] = doc["text"][:budget]
                budget -= len(doc["text"])
                evidence.append(doc)
            elif doc:
                failed.append(doc["url"])
    log(f"  fetched {len(evidence)} docs ({sum(e['chars'] for e in evidence)} chars), "
        f"{len(failed)} failed")

    # --- Phase 3: verdicts --------------------------------------------------
    precomputed = {entity_id: {c["field"]: precompute_anomaly_flags(c) for c in claims}}
    out = llm.chat_json(system, [verify_prompt(entity_id, etype, claims, evidence,
                                               failed, precomputed)],
                        max_tokens=args.verify_max_tokens, tag=f"{entity_id}/verify")
    rows = (out or {}).get("rows") or []
    if not isinstance(rows, list):
        raise RuntimeError(f"{entity_id}/verify returned non-list rows")
    return rows, evidence


# ---------------------------------------------------------------------------
# Output normalization + mechanical enforcement
# ---------------------------------------------------------------------------


def apply_mechanical(row, claim, claims):
    """Prompt-deterministic rules that hold regardless of model output:
    anomaly flags (42-ladder / 365-day / round-thousand / empty|homepage URL /
    stored-rate), disposal_rate recompute vs stored, and the NJDG stamp rule."""
    notes = row.get("notes", "") or ""
    flags = set(f.strip() for f in re.split(r"[,;]", row.get("anomaly_flags", "")) if f.strip())
    for f in precompute_anomaly_flags(claim):
        flags.add(f)
    if row["field"] == "disposal_rate":
        d = next((x["current_value"] for x in claims
                  if x["field"] == "disposed_last_year"), None)
        fl = next((x["current_value"] for x in claims
                   if x["field"] == "filed_last_year"), None)
        try:
            rec = round(float(d) / float(fl), 4)
            if claim["current_value"] and abs(rec - float(claim["current_value"])) > 1e-9:
                flags.add("rate-mismatch")
                if "rate-mismatch" not in notes:
                    notes += (f"; stored rate {claim['current_value']} != recomputed "
                              f"{d}/{fl}={rec}") if notes else (
                        f"stored rate {claim['current_value']} != recomputed {d}/{fl}={rec}")
        except (TypeError, ValueError, ZeroDivisionError):
            pass
    if row["field"] == "njdg_source_stamp":
        if claim["current_value"] == "present":
            row["njdg_stamp_valid"] = "FALSE"
            if "recommend strip NJDG source" not in notes:
                notes = (notes + "; " if notes else "") + "recommend strip NJDG source"
        elif claim["current_value"] == "absent":
            row["njdg_stamp_valid"] = "TRUE"
    row["anomaly_flags"] = ", ".join(sorted(flags))
    row["notes"] = notes
    return row


def normalize_rows(entity_id, claims, raw_rows):
    """Align model rows to the input claims, enforce prompt-deterministic rules."""
    by_pair = {}
    for r in raw_rows:
        if not isinstance(r, dict):
            continue
        k = (r.get("entity_id") or entity_id, r.get("field") or "")
        by_pair.setdefault(k, []).append(r)

    out = []
    for c in claims:
        pair = (c["entity_id"], c["field"])
        rs = by_pair.get(pair)
        if not rs:
            row = {k: c.get(k, "") for k in ("entity_id", "type", "field", "current_value",
                                             "current_source_type", "current_source_url",
                                             "data_as_of")}
            row.update({"verdict": "UNSOURCED", "verified_value": "",
                        "verified_as_of": "", "source_class": "", "source_title": "",
                        "source_url": "", "table_or_section": "", "verbatim_excerpt": "",
                        "primary_count": 0, "independent_secondary_count": 0,
                        "confidence_tier": "UNSOURCED", "njdg_stamp_valid": "",
                        "anomaly_flags": "", "notes": "model omitted row; auto-filled UNSOURCED"})
            out.append(apply_mechanical(row, c, claims))
            continue
        r = rs[0]
        row = {k: c.get(k, "") for k in ("entity_id", "type", "field", "current_value",
                                         "current_source_type", "current_source_url",
                                         "data_as_of")}
        row["verdict"] = str(r.get("verdict", "UNSOURCED")).upper()
        if row["verdict"] not in VERDICTS:
            row["verdict"] = "UNSOURCED"
        row["verified_value"] = str(r.get("verified_value", "") or "")
        row["verified_as_of"] = str(r.get("verified_as_of", "") or "")
        row["source_class"] = str(r.get("source_class", "") or "")
        row["source_title"] = str(r.get("source_title", "") or "")
        row["source_url"] = str(r.get("source_url", "") or "")
        row["table_or_section"] = str(r.get("table_or_section", "") or "")
        row["verbatim_excerpt"] = str(r.get("verbatim_excerpt", "") or "")
        try:
            row["primary_count"] = int(r.get("primary_count", 0) or 0)
        except (TypeError, ValueError):
            row["primary_count"] = 0
        try:
            row["independent_secondary_count"] = int(
                r.get("independent_secondary_count", 0) or 0)
        except (TypeError, ValueError):
            row["independent_secondary_count"] = 0
        row["confidence_tier"] = str(r.get("confidence_tier", "") or "")
        if row["confidence_tier"] not in TIERS:
            row["confidence_tier"] = ""
        row["njdg_stamp_valid"] = str(r.get("njdg_stamp_valid", "") or "")
        row["anomaly_flags"] = str(r.get("anomaly_flags", "") or "")
        row["notes"] = str(r.get("notes", "") or "")
        out.append(apply_mechanical(row, c, claims))
    return out


# ---------------------------------------------------------------------------
# SAT anchor self-check (method calibration, runs first)
# ---------------------------------------------------------------------------


def run_sat_anchor(system, llm, claims_by_entity, args, backend):
    """Verify sat against SEBI AR FY25-26 Table 10.35. Returns (result, rows)."""
    if "sat" not in claims_by_entity:
        return "SKIPPED", []
    log("SAT anchor self-check: re-deriving 1,066 / 429 / 323 from SEBI AR 2025-26 Table 10.35")
    try:
        raw, _ = process_entity("sat", claims_by_entity["sat"], system, llm, args, backend)
        rows = normalize_rows("sat", claims_by_entity["sat"], raw)
    except Exception as e:
        log(f"  SAT anchor loop failed: {e}")
        return "ERROR", []
    num = {r["field"]: r for r in rows if r["field"] in NUMERIC_FIELDS}
    got = {f: num.get(f, {}).get("verdict") for f in ("pending_cases", "filed_last_year",
                                                      "disposed_last_year")}
    confirmed_stale = all(got.get(f) == "CONFIRM" for f in got)
    refuted_to_anchor = all(got.get(f) == "REFUTE" for f in got)
    if refuted_to_anchor:
        result = "PASS"
    elif confirmed_stale:
        result = "FAILED-stale-snapshot"
    else:
        result = "INCONCLUSIVE"
    log(f"  SAT anchor: {result} (verdicts: {got})")
    return result, rows


# ---------------------------------------------------------------------------
# Output writing
# ---------------------------------------------------------------------------


def open_output(out_path, resume):
    os.makedirs(OUT, exist_ok=True)
    if resume and os.path.exists(out_path):
        mode = "a"
        with open(out_path, encoding="utf-8", newline="") as f:
            existing = list(csv.DictReader(f))
        log(f"resuming {out_path} with {len(existing)} existing rows")
        done = {(r["entity_id"], r["field"]) for r in existing}
    else:
        mode = "w"
        done = set()
        existing = []
    f = open(out_path, mode, encoding="utf-8", newline="")
    writer = csv.DictWriter(f, fieldnames=OUTPUT_HEADER, extrasaction="ignore")
    if mode == "w":
        writer.writeheader()
        f.flush()
    return f, writer, done


def build_meta(args, rows_n, tokens_in, tokens_out, sat_result, extra=None):
    meta = {
        "rater": args.rater,
        "model": args.model,
        "model_version": args.model_version,
        "context": "provided-files + web_search_on, temp 0.2",
        "web_search": True,
        "temperature": args.temperature,
        "prompt_version": PROMPT_VERSION,
        "batch_id": BATCH_ID,
        "timestamp_utc": now_utc().isoformat(),
        "entities_n": args.entities_n,
        "rows_n": rows_n,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_estimate": (
            f"${(tokens_in / 1e6 * PRICE_IN_PER_M + tokens_out / 1e6 * PRICE_OUT_PER_M):.4f} "
            f"(deepseek-v4-flash off-peak ${PRICE_IN_PER_M}/M in, ${PRICE_OUT_PER_M}/M out; "
            f"peak ~2x)"
        ),
    }
    if extra:
        meta.update(extra)
    return meta


def write_meta(path, meta):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
        f.write("\n")


# ---------------------------------------------------------------------------
# Final 6-point summary for DSo (RUN_SETUP.md)
# ---------------------------------------------------------------------------


def summarize(all_rows, sat_result, meta_path):
    vc = {}
    for r in all_rows:
        vc[r["verdict"]] = vc.get(r["verdict"], 0) + 1
    covered = {r["entity_id"] for r in all_rows
               if r["verdict"] in ("CONFIRM", "REFUTE") and r.get("source_url")}
    refutes = [r for r in all_rows if r["verdict"] == "REFUTE"]
    njdg_false = sum(1 for r in all_rows
                     if r["field"] == "njdg_source_stamp" and r["njdg_stamp_valid"] == "FALSE")
    meta_ok = True
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            m = json.load(f)
        meta_ok = all(m.get(k) not in (None, "", 0) for k in
                      ("model_version", "context", "tokens_in", "tokens_out", "cost_estimate"))
    lines = [
        "\n===== 6-POINT SUMMARY FOR DSo =====",
        f"1. COVERAGE: {len(covered)}/{EXPECTED_ENTITIES_N} entities with >=1 verifiable primary",
        f"2. VERDICTS: {json.dumps(vc, sort_keys=True)} across {len(all_rows)} rows",
        f"3. SAT ANCHOR: {sat_result}",
        f"4. REFUTEs ({len(refutes)}):",
    ]
    for r in refutes:
        lines.append(f"   - {r['entity_id']}|{r['field']}: stored={r['current_value']} "
                     f"-> verified={r['verified_value']} @ {r['source_url']}")
    lines.append(f"5. njdg_stamp_valid=FALSE: {njdg_false} (all 43 'present' should be FALSE)")
    lines.append(f"6. meta.json complete: {meta_ok} ({meta_path})")
    lines.append("=================================")
    log("\n".join(lines))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def build_argparser():
    p = argparse.ArgumentParser(
        description="Prajna · DeepSeek verifier loop for JEM verify-trib-01",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--claims", default=CLAIMS_DEFAULT,
                   help="claims CSV under test (default inputs/claim_to_verify.csv)")
    p.add_argument("--out-dir", default=OUT, help="output directory (out/ only)")
    p.add_argument("--output", default="", help="explicit output CSV path "
                   "(default {model}__verify-trib-01__{user}__{ts}.csv in out/)")
    p.add_argument("--api-key", default=os.environ.get("DEEPSEEK_API_KEY", ""),
                   help="DeepSeek API key (or DEEPSEEK_API_KEY)")
    p.add_argument("--model", default=DEEPSEEK_MODEL, help="DeepSeek model id")
    p.add_argument("--model-version", default="",
                   help="exact model string + date for meta (default '<model> @ YYYY-MM-DD')")
    p.add_argument("--base-url", default=DEEPSEEK_BASE, help="OpenAI-compatible base URL")
    p.add_argument("--rater", default="prajna")
    p.add_argument("--user", default=getpass.getuser())
    p.add_argument("--temperature", type=float, default=0.2,
                   help="must stay 0.2 for the calibration arm")
    p.add_argument("--search-backend", choices=["tavily", "serpapi", "direct"], default="",
                   help="auto: TAVILY_API_KEY > SERPAPI_API_KEY; direct = fetch-only")
    p.add_argument("--search-results", type=int, default=4, help="top results per query")
    p.add_argument("--max-fetch-items", type=int, default=6, help="max plan items per entity")
    p.add_argument("--evidence-budget-chars", type=int, default=60000,
                   help="total evidence text budget per entity")
    p.add_argument("--verify-max-tokens", type=int, default=8000)
    p.add_argument("--fetch-timeout", type=int, default=30)
    p.add_argument("--max-retries", type=int, default=3, help="LLM retries per phase")
    p.add_argument("--sleep", type=float, default=1.5, help="seconds between entities")
    p.add_argument("--entities", default="", help="comma-separated subset (e.g. sat,ngt)")
    p.add_argument("--limit", type=int, default=0, help="max entities to process (0=all)")
    p.add_argument("--resume", action="store_true", help="skip entities already in output CSV")
    p.add_argument("--skip-sat", action="store_true", help="do not run SAT anchor first")
    p.add_argument("--no-sat-exit", action="store_true",
                   help="warn but do not exit on stale-snapshot SAT result")
    p.add_argument("--dry-run", action="store_true", help="plan only, no network/LLM")
    p.add_argument("--selftest", action="store_true", help="plumbing check, no network/LLM")
    return p


def run_selftest(args):
    log("selftest: loading claims + prompt files (no network/LLM)")
    rows, by_entity = load_claims(args.claims)
    system = load_prompt_files()
    log(f"  claims rows: {len(rows)}; entities: {len(by_entity)} "
        f"(expected {EXPECTED_ENTITIES_N})")
    log(f"  system prompt chars: {len(system)}")
    log(f"  out dir writable: {os.access(args.out_dir, os.W_OK) if os.path.isdir(args.out_dir) else os.makedirs(args.out_dir, exist_ok=True) or True}")
    pairs = sum(len(v) for v in by_entity.values())
    missing = []
    for eid, cs in by_entity.items():
        if len(cs) != len({c["field"] for c in cs}):
            missing.append((eid, "duplicate fields"))
        for c in cs:
            if c["field"] not in NUMERIC_FIELDS and c["field"] != "njdg_source_stamp":
                missing.append((eid, f"unknown field {c['field']}"))
    log(f"  field pairs: {pairs}; structural issues: {missing or 'none'}")
    log("selftest OK")
    return 0


def main():
    args = build_argparser().parse_args()
    if args.selftest:
        return run_selftest(args)

    rows, by_entity = load_claims(args.claims)
    system = load_prompt_files()

    if args.dry_run:
        entity_ids = list(by_entity)
        if args.entities:
            entity_ids = [e for e in entity_ids if e in
                          {x.strip() for x in args.entities.split(",") if x.strip()}]
        log("dry-run plan (no network/LLM):")
        for eid in entity_ids[: args.limit or len(entity_ids)]:
            log(f"  {eid}: {len(by_entity[eid])} claims, phases: plan->fetch->verify")
        log(f"  total entities: {len(by_entity)}; rows: {len(rows)}")
        return 0

    if not args.api_key:
        fail("DEEPSEEK_API_KEY is not set. A verifier with no LLM cannot verify — "
             "set DEEPSEEK_API_KEY (or --api-key) and re-run.")
    backend = resolve_search_backend(args)

    ts = utc_stamp()
    if args.output:
        out_path = args.output
    else:
        out_path = os.path.join(args.out_dir,
                                f"{args.model}__verify-trib-01__{args.user}__{ts}.csv")
    meta_path = out_path.rsplit(".", 1)[0] + ".meta.json"

    model_version = args.model_version or f"{args.model} @ {now_utc():%Y-%m-%d}"
    llm = LLM(args.api_key, args.model, args.base_url, args.temperature,
              max_retries=args.max_retries)

    entity_ids = list(by_entity)
    if args.entities:
        subset = [e.strip() for e in args.entities.split(",") if e.strip()]
        unknown = set(subset) - set(entity_ids)
        if unknown:
            fail(f"unknown entities: {sorted(unknown)}")
        entity_ids = [e for e in entity_ids if e in subset]

    # SAT anchor first (unless told otherwise). Its rows are written to the
    # output once; sat is then skipped by the main loop. Resume-aware: if sat
    # is already complete in the output file, do not re-verify it.
    resume_done = set()
    if args.resume and os.path.exists(out_path):
        with open(out_path, encoding="utf-8", newline="") as f:
            resume_done = {(r["entity_id"], r["field"]) for r in csv.DictReader(f)}
    sat_result, sat_rows = "SKIPPED", []
    sat_claims = by_entity.get("sat")
    sat_needs_run = sat_claims and not args.skip_sat and not (
        args.resume and all((c["entity_id"], c["field"]) in resume_done for c in sat_claims))
    if sat_needs_run:
        sat_result, sat_rows = run_sat_anchor(system, llm, by_entity, args, backend)
        if sat_result == "FAILED-stale-snapshot" and not args.no_sat_exit:
            fail("SAT anchor CONFIRMed the stale 420/380/345/365 snapshot — a stale "
                 "snapshot leaked into the verifier (card: 'stop and flag'). Re-run with "
                 "--no-sat-exit only if you have verified the leak source.", code=3)

    f, writer, done = open_output(out_path, args.resume)
    all_rows = []
    if sat_rows:
        fresh_sat = [r for r in sat_rows if (r["entity_id"], r["field"]) not in resume_done]
        for r in fresh_sat:
            writer.writerow(r)
            all_rows.append(r)
        done.update((r["entity_id"], r["field"]) for r in fresh_sat)
        entity_ids = [e for e in entity_ids if e != "sat"]
        f.flush()
    meta = build_meta(args, 0, llm.tokens_in, llm.tokens_out, sat_result,
                      extra={"search_backend": backend, "sat_anchor_check": sat_result,
                             "pricing_note": "off-peak deepseek-v4-flash"})
    write_meta(meta_path, meta)
    log(f"output: {out_path}")

    processed = 0
    try:
        for eid in entity_ids:
            if args.limit and processed >= args.limit:
                log(f"hit --limit {args.limit}; stopping")
                break
            claims = by_entity[eid]
            if args.resume and all((c["entity_id"], c["field"]) in done for c in claims):
                log(f"skip {eid}: already complete in output")
                continue
            try:
                raw, _ = process_entity(eid, claims, system, llm, args, backend)
                norm = normalize_rows(eid, claims, raw)
            except Exception as e:
                log(f"  ! {eid} loop failed: {e} — emitting UNSOURCED rows and continuing")
                norm = normalize_rows(eid, claims, [])
                for r in norm:
                    r["notes"] = (r["notes"] + "; " if r["notes"] else "") + f"loop error: {e}"
            for r in norm:
                writer.writerow(r)
                all_rows.append(r)
            f.flush()
            done.update((r["entity_id"], r["field"]) for r in norm)
            processed += 1
            # keep meta fresh so a crash leaves a usable audit trail
            write_meta(meta_path, build_meta(
                args, len(all_rows), llm.tokens_in, llm.tokens_out, sat_result,
                extra={"search_backend": backend, "sat_anchor_check": sat_result,
                       "pricing_note": "off-peak deepseek-v4-flash"}))
            time.sleep(args.sleep)
    finally:
        f.close()
        write_meta(meta_path, build_meta(
            args, len(all_rows), llm.tokens_in, llm.tokens_out, sat_result,
            extra={"search_backend": backend, "sat_anchor_check": sat_result,
                   "pricing_note": "off-peak deepseek-v4-flash"}))
        log(f"closed {out_path} with {len(all_rows)} rows")
        log(f"tokens in={llm.tokens_in} out={llm.tokens_out}")

    summarize(all_rows, sat_result, meta_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
