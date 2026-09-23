#!/usr/bin/env python3
"""LLM-native scraper: one Claude call fetches primary GoI sources (server-side web_fetch +
web_search), extracts structure, and emits one entity YAML. Replaces deterministic stages 1-5;
scripts/../pipeline/stage6_gate is the deterministic backstop. Run from jem/.

    ANTHROPIC_API_KEY=... python scripts/llm_scrape.py hc_madras \
        --name "Madras High Court" --type HighCourtBench \
        --cluster constitutional_courts --state tn \
        [--seed-url URL] [--pdf-url URL ...] [--model claude-sonnet-5]

--pdf-url downloads an allowlisted PDF and feeds it to Claude as a base64 document block
(parsed directly, with citations) instead of relying on server-side web_fetch.
"""
from __future__ import annotations
import argparse, datetime, json, os, random, sys, time
from pathlib import Path
from dotenv import load_dotenv
JEM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(JEM))                        # make `agents` importable when run loosely
import yaml
from agents.prompts import load_prompt
from pipeline.stage6_gate.run_gate import run_gate, _host, ALLOWED_HOSTS
load_dotenv()
HOSTS = list(yaml.safe_load((JEM / "sources.yaml").read_text())["hosts"])
DEFAULT_MODEL = "claude-opus-5"                     # sonnet-5 via --model for bulk state entities
MAX_CONTINUATIONS = 5
MAX_STREAM_RETRIES = 6                              # transient (529/5xx/conn) retries per turn
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504, 529}


def _tools() -> list[dict]:
    return [
        {"type": "web_search_20260209", "name": "web_search", "allowed_domains": HOSTS},
        {"type": "web_fetch_20260209", "name": "web_fetch", "allowed_domains": HOSTS,
         "citations": {"enabled": True}, "max_uses": 10},
    ]


def _pdf_block(url: str) -> dict:
    """Download an allowlisted PDF and return a base64 `document` content block so Claude
    parses it directly (with citations), instead of relying on server-side web_fetch."""
    import base64, httpx
    if _host(url) not in ALLOWED_HOSTS:
        raise ValueError(f"PDF host not on allowlist: {url}")
    print(f"  ↓ downloading PDF {url}", file=sys.stderr)
    r = httpx.get(url, timeout=60, follow_redirects=True)
    r.raise_for_status()
    if len(r.content) > 32 * 1024 * 1024:              # base64 PDF must fit the 32MB request cap
        raise ValueError(f"PDF too large ({len(r.content)} bytes > 32MB): {url}")
    return {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf",
                   "data": base64.standard_b64encode(r.content).decode()},
        "title": url.rsplit("/", 1)[-1],
        "citations": {"enabled": True},
    }


def _json_from(content) -> dict:
    """Concatenate text blocks and pull the single JSON object out of them."""
    text = "".join(b.text for b in content if getattr(b, "type", None) == "text")
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError(f"no JSON object in model output:\n{text[:500]}")
    return json.loads(text[start:end + 1])


def _client():
    # max_retries: SDK default is 2; bump so transient 529 overloads back off and retry.
    import anthropic
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"), max_retries=6)


def scrape(spec: dict, model: str, seed_url: str | None, pdf_urls: list[str],
           usage: dict | None = None) -> dict:
    client = _client()

    today = datetime.date.today().isoformat()
    user = (f"Build the entity record for:\n{json.dumps(spec, indent=2)}\n"
            f"Today's date (use for accessed_date): {today}\n")
    if seed_url:
        user += f"Start from this primary source URL: {seed_url}\n"
    if pdf_urls:
        user += ("Attached PDF(s) are primary sources — read them and cite their URLs in "
                 f"sources[]: {', '.join(pdf_urls)}\n")

    system = load_prompt("entity_emit_v1.md")
    # Document blocks must precede the text block in the same user turn.
    content = [_pdf_block(u) for u in pdf_urls] + [{"type": "text", "text": user}]
    messages = [{"role": "user", "content": content}]

    for _ in range(MAX_CONTINUATIONS + 1):
        resp = _stream_turn(client, model, system, messages, usage)
        if resp.stop_reason != "pause_turn":       # server-tool loop finished
            return _json_from(resp.content)
        messages.append({"role": "assistant", "content": resp.content})
    raise RuntimeError("gave up: server-tool loop still paused after max continuations")


def verify_entity(entity: dict, model: str, usage: dict | None = None) -> dict:
    """Second, adversarial pass: web_fetch the entity's cited sources and judge whether the
    record is true and supported. Returns {verification_status, confidence, existence_confirmed,
    unsupported_fields, notes}. Reuses the same tools/stream/retry plumbing as scrape()."""
    client = _client()
    system = load_prompt("entity_verify_v1.md")
    user = ("Verify this entity record against its cited sources:\n"
            f"{json.dumps(entity, indent=2, default=str)}\n")
    messages = [{"role": "user", "content": [{"type": "text", "text": user}]}]

    for _ in range(MAX_CONTINUATIONS + 1):
        resp = _stream_turn(client, model, system, messages, usage)
        if resp.stop_reason != "pause_turn":
            return _json_from(resp.content)
        messages.append({"role": "assistant", "content": resp.content})
    raise RuntimeError("verify: server-tool loop still paused after max continuations")


def _accumulate_usage(usage: dict, msg) -> None:
    """Add one turn's token/server-tool counts into the caller's accumulator dict."""
    u = getattr(msg, "usage", None)
    if u is None:
        return
    usage["input_tokens"] += getattr(u, "input_tokens", 0) or 0
    usage["output_tokens"] += getattr(u, "output_tokens", 0) or 0
    usage["cache_read"] += getattr(u, "cache_read_input_tokens", 0) or 0
    usage["cache_creation"] += getattr(u, "cache_creation_input_tokens", 0) or 0
    stu = getattr(u, "server_tool_use", None)
    if stu is not None:
        usage["web_searches"] += getattr(stu, "web_search_requests", 0) or 0


def _stream_turn(client, model, system, messages, usage: dict | None = None):
    """One streamed turn. Streaming avoids the idle-connection timeout on multi-minute
    server-tool loops and shows progress. max_retries only covers pre-stream errors, so we
    retry transient failures (529/5xx/connection) raised MID-stream ourselves, from scratch."""
    import anthropic
    for attempt in range(MAX_STREAM_RETRIES + 1):
        try:
            with client.messages.stream(
                model=model, max_tokens=8000, system=system,
                tools=_tools(), messages=messages,
            ) as stream:
                for event in stream:
                    if event.type == "content_block_start":
                        b = event.content_block
                        if getattr(b, "type", "") == "server_tool_use":
                            print(f"  … {getattr(b, 'name', '?')}: {getattr(b, 'input', '')}",
                                  file=sys.stderr)
                msg = stream.get_final_message()
                if usage is not None:
                    _accumulate_usage(usage, msg)
                return msg
        except anthropic.APIStatusError as e:
            if e.status_code not in RETRYABLE_STATUS or attempt == MAX_STREAM_RETRIES:
                raise
        except anthropic.APIConnectionError:
            if attempt == MAX_STREAM_RETRIES:
                raise
        sleep = min(2.0 * 2 ** attempt, 30.0) + random.uniform(0, 1.5)
        print(f"  (transient error — retry {attempt + 1}/{MAX_STREAM_RETRIES} in {sleep:.0f}s)",
              file=sys.stderr)
        time.sleep(sleep)
    raise RuntimeError("unreachable: stream retry loop exhausted without raising")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("entity_id")
    ap.add_argument("--name", required=True)
    ap.add_argument("--type", required=True)
    ap.add_argument("--cluster", required=True)
    ap.add_argument("--state", required=True, help="lowercase state/UT code, e.g. tn")
    ap.add_argument("--seed-url", default=None)
    ap.add_argument("--pdf-url", action="append", default=[],
                    help="allowlisted PDF to download and parse directly (repeatable)")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--draft-dir", default=str(JEM / "build" / "llm_drafts"),
                    help="where a gate-failing draft is left for inspection")
    args = ap.parse_args()

    spec = {"id": args.entity_id, "name": args.name, "type": args.type,
            "cluster": args.cluster, "level_of_government": "State"}
    pdf_urls = list(args.pdf_url)
    if args.seed_url and args.seed_url.lower().endswith(".pdf"):
        pdf_urls.append(args.seed_url)               # a .pdf seed is parsed directly, not just cited
    entity = scrape(spec, args.model, args.seed_url, pdf_urls)
    entity["id"] = args.entity_id                    # never let the model rename the id

    yaml_text = yaml.safe_dump(entity, sort_keys=False, allow_unicode=True)

    draft = Path(args.draft_dir) / f"{args.entity_id}.yaml"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text(yaml_text)

    if run_gate(draft) != 0:
        print(f"\nGATE FAILED — draft left at {draft}", file=sys.stderr)
        return 1

    dest = (JEM / "data" / "entities" / "_generated" / "states"
            / args.state / f"{args.entity_id}.yaml")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(yaml_text)
    draft.unlink(missing_ok=True)
    print(f"GATE PASSED — wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
