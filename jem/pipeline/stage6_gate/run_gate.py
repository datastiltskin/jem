# Stage 6 — Gate, deterministic hard exit codes (spec §5). The backstop for the
# non-deterministic LLM scraper (scripts/llm_scrape.py): schema + source-host validity.
from __future__ import annotations
import subprocess, sys
from pathlib import Path
from urllib.parse import urlparse
import yaml

JEM = Path(__file__).resolve().parents[2]          # dir containing scripts/, sources.yaml


def _host(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")   # www. and bare are equivalent


ALLOWED_HOSTS = {_host("//" + h) for h in yaml.safe_load((JEM / "sources.yaml").read_text())["hosts"]}

# L4 institution gate (RCA_AI_HALLUCINATION_TRICHY_BENCH.md, mitigation #3): a body that is
# *created by a specific order* — a HighCourtBench being the documented case — must cite a
# source that actually establishes it, not only generic Constitution / GoI-website URLs. This
# is the deterministic rule that would have caught the phantom Trichy bench.
HIGH_RISK_TYPES = {"HighCourtBench"}
# A source that can establish/attest a specific body. Broadened to include official GoI reports
# (e.g. a DoJ report that names the bench) — real evidence of existence. Still excludes the
# generic-only combo that let the phantom Trichy bench through: Constitution + GoIWebsite / NJDG.
SPECIFIC_BASIS_TYPES = {"GazetteNotification", "CentralAct", "StateAct", "SCJudgment",
                        "HCJudgment", "OfficialReport", "AnnualReport"}


def _l4_institution_check(entity: dict) -> list[str]:
    """Return error strings if a high-risk entity lacks a specific establishing source."""
    if entity.get("type") not in HIGH_RISK_TYPES:
        return []
    stypes = {s.get("type") for s in entity.get("sources", [])}
    if stypes & SPECIFIC_BASIS_TYPES:
        return []
    return [f"L4: {entity.get('type')} '{entity.get('id')}' cites no specific establishing "
            f"source (needs one of {sorted(SPECIFIC_BASIS_TYPES)}); has only {sorted(stypes)}"]


def run_gate(entity_path: Path, l4: bool = True) -> int:
    """Return 0 iff the entity passes validate.py --strict AND every source URL is on an
    allowlisted GoI host. Non-zero (and a printed reason) otherwise."""
    entity_path = Path(entity_path)

    r = subprocess.run(
        [sys.executable, "scripts/validate.py", "--entity", str(entity_path), "--strict"],
        cwd=JEM,
    )
    if r.returncode != 0:
        return r.returncode                        # validate.py already printed the errors

    doc = yaml.safe_load(entity_path.read_text())
    entity = doc.get("entity", doc)                # files may nest under `entity:`
    bad = [s["url"] for s in entity.get("sources", [])
           if _host(s.get("url", "")) not in ALLOWED_HOSTS]
    if bad:
        print(f"GATE FAIL: source host(s) not on allowlist: {bad}", file=sys.stderr)
        return 1

    if l4:
        for e in _l4_institution_check(entity):
            print(f"GATE FAIL: {e}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:
        sys.exit(run_gate(Path(sys.argv[1])))

    # self-check: allowlist host passes (incl. www/bare equivalence), off-allowlist is rejected
    assert _host("https://main.sci.gov.in/x") in ALLOWED_HOSTS
    assert _host("https://indiacode.nic.in/") in ALLOWED_HOSTS      # sources.yaml has www.
    assert _host("https://en.wikipedia.org/x") not in ALLOWED_HOSTS

    # L4 regression (the Trichy case): a HighCourtBench with only generic sources FAILS;
    # add a gazette source and it PASSES. Non-high-risk types are unaffected.
    generic = [{"type": "Constitution"}, {"type": "GoIWebsite"}]        # the Trichy combo
    assert _l4_institution_check({"type": "HighCourtBench", "id": "x", "sources": generic})
    for good in ("GazetteNotification", "OfficialReport", "AnnualReport"):
        assert not _l4_institution_check(
            {"type": "HighCourtBench", "id": "x", "sources": generic + [{"type": good}]})
    assert not _l4_institution_check({"type": "ConstitutionalCourt", "id": "x", "sources": generic})
    print("run_gate self-check ok")
