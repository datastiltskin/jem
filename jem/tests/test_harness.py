"""
Tests for the deterministic rungs of the consensus harness.

The liveness gate and the reconcile step are the parts of the pipeline that are
committed code rather than judgement, so they are exactly the parts that must
behave identically for every reader. These tests pin the behaviour that the
harness spec relies on: a failed gate never becomes evidence, agreement from a
single model family never promotes past `partial`, and canon is a replayable
derivation over the ledger rather than a separate store.

Nothing here touches the network.
"""

import sys
import tempfile
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from harness.reconcile import (  # noqa: E402
    CONFIRM, REFUTE, UNSOURCED_V,
    Critic, Liveness, Researcher, Verifier,
    FETCH_FAILED, HOMEPAGE_ONLY, REFUTED, SECONDARY_ONLY, SOURCED,
    UNSOURCED_CANDIDATE,
    T_PARTIAL, T_UNSOURCED, T_VERIFIED,
    append_record, ledger_path, model_diversity, reconcile, replay_canon,
)
from harness.liveness import _is_bare_root, _claims_document  # noqa: E402


def _clean_gate(url="https://x.gov.in/report.pdf"):
    return Liveness(url=url, status=200, is_document=True, ok=True, reason="pass")


def _good_find(url="https://x.gov.in/report.pdf", **kw):
    base = dict(value=42, source_url=url, source_is_primary=True, is_goi_primary=True)
    base.update(kw)
    return Researcher(**base)


def _confirmed():
    return Verifier(verdict=CONFIRM, value_present_at_url=True)


# ── liveness helpers ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("url,expected", [
    ("https://x.gov.in/", True),
    ("https://x.gov.in", True),
    ("https://x.gov.in/reports/2025.pdf", False),
    ("https://x.gov.in/?q=1", False),
])
def test_bare_root_detection(url, expected):
    assert _is_bare_root(url) is expected


@pytest.mark.parametrize("url,expected", [
    ("https://x.gov.in/annual.pdf", True),
    ("https://x.gov.in/data.xlsx", True),
    ("https://x.gov.in/page", False),
])
def test_document_claim_inferred_from_suffix(url, expected):
    assert _claims_document(url, None) is expected


# ── diversity ─────────────────────────────────────────────────────────────────

def test_two_runs_of_one_model_count_once():
    assert model_diversity(["claude", "claude", "Claude"]) == 1
    assert model_diversity(["claude", "gpt"]) == 2


# ── reconcile ─────────────────────────────────────────────────────────────────

def test_goi_primary_confirmed_across_families_is_verified():
    r = reconcile(_clean_gate(), _good_find(), _confirmed(),
                  model_families=["claude", "gpt"])
    assert r["label"] == SOURCED
    assert r["confidence_tier"] == T_VERIFIED
    assert r["promotes_to_canon"] is True
    assert r["shared_bias_risk"] == "low"


def test_single_family_agreement_is_capped_and_flagged():
    """Agreement at diversity 1 is shared bias risk, not proof."""
    r = reconcile(_clean_gate(), _good_find(), _confirmed(),
                  model_families=["claude", "claude"])
    assert r["confidence_tier"] == T_PARTIAL
    assert r["model_diversity"] == 1
    assert r["shared_bias_risk"] == "high"


def test_bare_homepage_is_labelled_and_earns_no_tier():
    gate = Liveness(url="https://x.gov.in/", status=200, ok=False,
                    reason="bare_homepage_for_document_claim")
    r = reconcile(gate, _good_find("https://x.gov.in/"), _confirmed(),
                  model_families=["claude", "gpt"])
    assert r["label"] == HOMEPAGE_ONLY
    assert r["confidence_tier"] == T_UNSOURCED
    assert r["promotes_to_canon"] is False


def test_soft_404_shell_never_becomes_evidence():
    gate = Liveness(url="https://indiacode.gov.in/handle/1", status=200, ok=False,
                    reason="soft_404_catch_all_shell")
    r = reconcile(gate, _good_find("https://indiacode.gov.in/handle/1"), _confirmed(),
                  model_families=["claude", "gpt"])
    assert r["label"] == FETCH_FAILED
    assert r["confidence_tier"] == T_UNSOURCED
    assert r["promotes_to_canon"] is False


def test_refuted_value_does_not_promote():
    r = reconcile(_clean_gate(), _good_find(), Verifier(verdict=REFUTE),
                  model_families=["claude", "gpt"])
    assert r["label"] == REFUTED
    assert r["promotes_to_canon"] is False


def test_upheld_critic_challenge_demotes():
    r = reconcile(_clean_gate(), _good_find(), _confirmed(),
                  Critic(ran=True, challenge="wrong reporting period", upheld=False),
                  model_families=["claude", "gpt"])
    assert r["label"] == UNSOURCED_CANDIDATE
    assert r["confidence_tier"] == T_UNSOURCED
    assert r["promotes_to_canon"] is False


def test_secondaries_without_a_primary_do_not_promote():
    r = reconcile(
        Liveness(url="https://news.example/x", status=200, ok=True, reason="pass"),
        Researcher(value=42, source_url="https://news.example/x",
                   source_is_primary=False, independent_secondaries=2),
        _confirmed(), model_families=["claude", "gpt"])
    assert r["label"] == SECONDARY_ONLY
    assert r["promotes_to_canon"] is False


def test_documented_negative_is_captured_not_dropped():
    """`unsourced after documented attempts` is a finding the ledger keeps."""
    r = reconcile(Liveness(),
                  Researcher(value=None, attempts=[{"q": "a"}, {"q": "b"}, {"q": "c"}]),
                  Verifier(verdict=UNSOURCED_V), model_families=["claude"])
    assert r["label"] == UNSOURCED_CANDIDATE
    assert r["promotes_to_canon"] is False


# ── ledger + canon replay ─────────────────────────────────────────────────────

def test_canon_is_a_replayable_derivation_over_the_ledger():
    root = Path(tempfile.mkdtemp())
    (root / "ledger" / "runs").mkdir(parents=True)
    path = ledger_path(root, "cursor-C-commercial", "claude", "dso")

    append_record(
        path, entity_id="tn_ok", field_name="created_year", track="C",
        prompt_version="cursor-C-commercial-v1", model="claude",
        model_version="opus-5", context="tn", temperature=0.2,
        liveness=_clean_gate(), researcher=_good_find(value=2016),
        verifier=_confirmed())
    append_record(
        path, entity_id="tn_dead", field_name="created_year", track="C",
        prompt_version="cursor-C-commercial-v1", model="claude",
        model_version="opus-5", context="tn", temperature=0.2,
        liveness=Liveness(url="https://dead.gov.in/", status=404, ok=False, reason="non_200"),
        researcher=Researcher(value=None), verifier=Verifier(verdict=UNSOURCED_V))

    canon = replay_canon(root / "ledger" / "runs")
    assert list(canon) == ["tn_ok.created_year"], "only sourced cells reach canon"
    assert canon["tn_ok.created_year"]["value"] == 2016

    # Replaying again reproduces exactly the same canon — the transparency claim.
    assert replay_canon(root / "ledger" / "runs") == canon


def test_ledger_filename_carries_run_provenance():
    name = ledger_path(Path("/tmp"), "cursor-K-criminal", "gpt-5.6", "dso").name
    assert name.startswith("cursor-K-criminal__gpt-5.6__dso__")
    assert name.endswith(".jsonl")
