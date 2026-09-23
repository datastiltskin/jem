"""Tests for score derivation exclusions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from derive import (  # noqa: E402
    compute_independence_risk,
    is_scores_excluded,
    is_structural_only_entity,
    STRUCTURAL_ONLY_EXCLUDED_MESSAGE,
)


def test_role_archetype_is_structural_only():
    entity = {
        "id": "role_accused",
        "cluster": "people_roles",
        "role_layer": True,
        "type": "PartyRole",
    }
    assert is_structural_only_entity(entity)
    assert is_scores_excluded(entity)
    score, breakdown = compute_independence_risk(entity)
    assert score == 0
    assert STRUCTURAL_ONLY_EXCLUDED_MESSAGE in breakdown


def test_generic_scaffold_is_structural_only():
    entity = {
        "id": "fema_adjudicating_authority_generic",
        "cluster": "tribunals_adr",
        "type": "RegulatoryBodyQJ",
        "operational_status": "Active",
    }
    assert is_structural_only_entity(entity)
    score, _ = compute_independence_risk(entity)
    assert score == 0


def test_adjudicatory_body_still_scored():
    entity = {
        "id": "cestat",
        "cluster": "tribunals_adr",
        "type": "CentralTribunal",
        "operational_status": "Active",
        "appointment": {
            "formally_appoints": "ministry_of_finance",
            "criteria_public": False,
            "reappointment_possible": True,
            "removal_authority": "ministry_of_finance",
        },
        "funding": {
            "primary_source": "Ministry_Budget",
            "ministry_responsible": "ministry_of_finance",
        },
        "audit": {},
        "complaint_mechanism": {},
    }
    assert not is_scores_excluded(entity)
    score, _ = compute_independence_risk(entity)
    assert score >= 6
