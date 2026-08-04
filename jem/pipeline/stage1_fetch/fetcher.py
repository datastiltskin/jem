# fetch.py
from __future__ import annotations
import hashlib, json, time, random, ssl, socket, yaml
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse
import httpx

EVIDENCE = Path("evidence_store")
MANIFEST = EVIDENCE / "manifest.jsonl"
EVIDENCE.mkdir(exist_ok=True)

CFG = yaml.safe_load(Path("sources.yaml").read_text())
DEFAULTS = CFG["defaults"]
HOSTS = CFG["hosts"]


def _policy(host: str) -> dict:
    """Merge per-host policy over defaults."""
    return {**DEFAULTS, **HOSTS.get(host, {})}


@dataclass
class FetchResult:
    url: str
    host: str
    status: str                 # "OK" or a failure token
    fetched_at: str
    final_url: str | None = None
    sha256: str | None = None
    ext: str | None = None
    content_type: str | None = None
    bytes: int | None = None
    http_status: int | None = None
    backend: str | None = None
    request_params: dict | None = None   # for POST/XHR sources — part of identity
    note: str | None = None

    def ok(self) -> bool:
        return self.status == "OK"


# ---------- soft-404 / content assertions ----------

def _assert_content(body: bytes, ctype: str, pol: dict) -> str | None:
    """Return a failure token if the response looks like an error page, else None."""
    if len(body) < pol["min_bytes"]:
        return f"TOO_SMALL_{len(body)}b"

    accept = pol.get("accept_content_types")
    if accept and not any(a in ctype for a in accept):
        return f"BAD_CONTENT_TYPE_{ctype.split(';')[0]}"

    # required-substring guard: PDFs skip text check (binary); text/html must match
    needles = pol.get("must_contain", [])
    if needles and "pdf" not in ctype:
        try:
            text = body.decode("utf-8", errors="replace")
        except Exception:
            return "DECODE_FAIL"
        for n in needles:
            if n not in text:
                return f"MISSING_MARKER::{n}"
    return None


# ---------- TLS policy ----------

def _verify_fingerprint(host: str, port: int, expected: str) -> bool:
    """Pin cert fingerprint when we downgrade verification. Mismatch = refuse."""
    ctx = ssl._create_unverified_context()
    with socket.create_connection((host, port), timeout=15) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ss:
            der = ss.getpeercert(binary_form=True)
    fp = ":".join(f"{b:02X}" for b in hashlib.sha256(der).digest())
    return fp == expected.upper()


def _client(pol: dict, host: str) -> httpx.Client:
    if pol["tls"] == "downgrade":
        exp = pol.get("tls_fingerprint_sha256")
        if exp and not _verify_fingerprint(host, 443, exp):
            raise RuntimeError(f"TLS fingerprint mismatch for {host} — refusing")
        verify = False
    else:
        verify = True
    return httpx.Client(
        follow_redirects=True,
        timeout=pol["timeout_s"],
        verify=verify,
        headers={"User-Agent": pol["user_agent"]},
    )


# ---------- static backend ----------

def _fetch_static(url: str, pol: dict, host: str, method="GET",
                  data: dict | None = None) -> tuple[bytes, int, str, str]:
    with _client(pol, host) as c:
        if pol.get("needs_session") and pol.get("warmup_url"):
            c.get(pol["warmup_url"])                 # establish cookies
        r = c.request(method, url, data=data)
        return r.content, r.status_code, str(r.url), r.headers.get("content-type", "")


# ---------- persistence ----------

def _store(body: bytes, ctype: str) -> tuple[str, str]:
    sha = hashlib.sha256(body).hexdigest()
    ext = "pdf" if "pdf" in ctype else "json" if "json" in ctype else "html"
    path = EVIDENCE / f"{sha}.{ext}"
    if not path.exists():                            # content-addressed = idempotent
        path.write_bytes(body)
    return sha, ext


def _append_manifest(res: FetchResult) -> None:
    with MANIFEST.open("a") as f:
        f.write(json.dumps(asdict(res)) + "\n")


# ---------- public entry point ----------

def fetch(url: str, *, method="GET", data: dict | None = None) -> FetchResult:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    host = urlparse(url).netloc.lower()

    if host not in HOSTS:                             # allowlist enforced in code
        res = FetchResult(url, host, "REJECTED_HOST", now)
        _append_manifest(res)
        return res

    pol = _policy(host)
    backend = pol["backend"]
    last_err = None

    for attempt in range(pol["max_retries"]):
        try:
            if backend == "rendered":
                from .render import fetch_rendered
                body, http_status, final_url, ctype = fetch_rendered(url, pol)
            else:
                body, http_status, final_url, ctype = _fetch_static(
                    url, pol, host, method, data)

            if http_status != 200:
                last_err = f"HTTP_{http_status}"
            else:
                fail = _assert_content(body, ctype, pol)
                if fail:
                    last_err = fail                  # soft-404 caught here
                else:
                    sha, ext = _store(body, ctype)
                    res = FetchResult(
                        url=url, host=host, status="OK", fetched_at=now,
                        final_url=final_url, sha256=sha, ext=ext,
                        content_type=ctype, bytes=len(body),
                        http_status=200, backend=backend,
                        request_params=data)
                    _append_manifest(res)
                    return res
        except Exception as e:
            last_err = f"EXC::{type(e).__name__}::{e}"

        # backoff with jitter (rate-limit / WAF politeness)
        sleep = pol["backoff_base_s"] * (2 ** attempt) + random.uniform(0, 1.5)
        time.sleep(sleep)

    res = FetchResult(url, host, "FAILED", now, backend=backend, note=last_err)
    _append_manifest(res)                            # failures logged too
    return res


if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser(description="Fetch a URL through the allowlist + evidence store.")
    ap.add_argument("url")
    ap.add_argument("--method", default="GET")
    ap.add_argument("--data", help="JSON body for POST/XHR sources")
    args = ap.parse_args()
    res = fetch(args.url, method=args.method,
                data=json.loads(args.data) if args.data else None)
    print(json.dumps(asdict(res), indent=2))
    sys.exit(0 if res.ok() else 1)