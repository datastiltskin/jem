# scripts/run_fetch.py
"""
Manual driver for Stage 1. Usage:
    python3 scripts/run_fetch.py https://main.sci.gov.in/
    python3 scripts/run_fetch.py https://njdg.ecourts.gov.in/njdgnew/
    python3 scripts/run_fetch.py https://main.sci.gov.in/ --peek
"""
import sys, json, argparse
from pathlib import Path

# make the package importable when run as a loose script
root = next(p for p in Path(__file__).resolve().parents if (p / "pipeline").is_dir())
sys.path.insert(0, str(root))

from pipeline.stage1_fetch.fetcher import fetch, EVIDENCE
from dataclasses import asdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--method", default="GET")
    ap.add_argument("--peek", action="store_true",
                    help="print first 800 chars of stored body")
    args = ap.parse_args()

    print(f"→ fetching {args.url}")
    res = fetch(args.url, method=args.method)

    print("\n=== RESULT ===")
    print(json.dumps(asdict(res), indent=2))

    if res.ok():
        print(f"\n✓ OK  backend={res.backend}  {res.bytes}b  sha={(res.sha256 or '')[:12]}…")
        if args.peek:
            body_path = EVIDENCE / f"{res.sha256}.{res.ext}"
            raw = body_path.read_bytes()
            if res.ext == "pdf":
                print(f"[PDF — {len(raw)}b binary, not printing]")
            else:
                print("\n=== PEEK (first 800 chars) ===")
                print(raw.decode("utf-8", errors="replace")[:800])
    else:
        print(f"\n✗ FAILED  status={res.status}  note={res.note}")
        sys.exit(1)


if __name__ == "__main__":
    main()