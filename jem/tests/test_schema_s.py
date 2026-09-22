"""
Regression tests for the S schema foundation and the two-axis classification.

The point of these is the gate S defines for itself: the additions are
back-compatible, so the existing corpus must keep validating unchanged, and a
type that nobody has classified must be refused rather than silently counted.
"""

import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
DATA = Path(__file__).resolve().parent.parent / "data"
sys.path.insert(0, str(SCRIPTS))

import validate as V  # noqa: E402
from classification import (  # noqa: E402
    TYPE_CLASSIFICATION,
    classify,
    classify_entity,
    is_countable,
)


def _entity(**overrides):
    base = dict(
        id="x_test_entity",
        name="Test Entity",
        type="ConstitutionalCourt",
        cluster="constitutional_courts",
        level_of_government="Central",
        created_year=1950,
        operational_status="Active",
        data_quality="partial",
        sources=[],
    )
    base.update(overrides)
    return base


# ── S5: classification is total over the declared vocabulary ─────────────────

def test_every_declared_entity_type_is_classifiable():
    unmapped = [t for t in V.ENTITY_TYPES if t not in TYPE_CLASSIFICATION]
    assert unmapped == [], f"types in ENTITY_TYPES with no classification: {unmapped}"


def test_classification_map_declares_no_unknown_types():
    undeclared = [t for t in TYPE_CLASSIFICATION if t not in V.ENTITY_TYPES]
    assert undeclared == [], f"classified types absent from ENTITY_TYPES: {undeclared}"


def test_unmapped_type_is_refused():
    with pytest.raises(ValueError, match="Unclassified entity type"):
        classify("NotARealType")


def test_override_bypasses_derivation():
    e = _entity(classification_override={"nature": "personnel", "function": "judicial"})
    assert classify_entity(e) == ("personnel", "judicial")


def test_judicial_personnel_is_a_derived_intersection():
    """Role archetypes are the personnel x judicial cell the two axes exist for."""
    assert classify("JudicialOfficerRole") == ("personnel", "judicial")


def test_generic_rollups_are_not_countable():
    assert is_countable({"id": "x"}) is True
    assert is_countable({"id": "x_generic", "is_generic_rollup": True}) is False


# ── S1/S2/S3: new type and blocks ─────────────────────────────────────────────

def test_commercial_court_type_accepted_and_judicial():
    V.EntityModel(**_entity(type="CommercialCourt", cluster="subordinate_courts"))
    assert classify("CommercialCourt") == ("institution", "judicial")


def test_pecuniary_jurisdiction_block():
    e = V.EntityModel(**_entity(pecuniary_jurisdiction={
        "specified_value_min": 300000,
        "currency": "INR",
        "basis": {"instrument_id": "commercial_courts_act_2015", "provision": "s.2(1)(i)"},
    }))
    assert e.pecuniary_jurisdiction.specified_value_min == 300000
    assert e.pecuniary_jurisdiction.basis.instrument_id == "commercial_courts_act_2015"


def test_report_publication_block_and_vocabulary():
    e = V.EntityModel(**_entity(report_publication={
        "publishes_reports": "no",
        "statutorily_required": "yes",
        "notes": "no reports found after checking own site, ministry archive, PIB",
    }))
    assert e.report_publication.publishes_reports == "no"

    with pytest.raises(Exception):
        V.EntityModel(**_entity(report_publication={"publishes_reports": "sometimes"}))


# ── S4/S6: legal basis is a string-or-struct union ────────────────────────────

def test_legacy_string_basis_still_validates():
    """The back-compatibility promise: no mass rewrite of existing entities."""
    e = V.EntityModel(**_entity(statutory_basis="Commercial Courts Act 2015, s.3"))
    assert e.statutory_basis == "Commercial Courts Act 2015, s.3"


def test_struct_list_basis_carries_the_transition():
    e = V.EntityModel(**_entity(statutory_basis=[
        {"instrument_id": "bnss_2023", "provision": "ss.21-23",
         "status": "in_force", "effective_from": "2024-07-01"},
        {"instrument_id": "crpc_1973", "provision": "ss.6-29",
         "status": "superseded", "repealed_on": "2024-07-01"},
    ]))
    assert [r.status for r in e.statutory_basis] == ["in_force", "superseded"]


def test_bad_legal_basis_status_rejected():
    with pytest.raises(Exception):
        V.EntityModel(**_entity(statutory_basis=[
            {"instrument_id": "bnss_2023", "status": "sort_of_in_force"}]))


def test_relationship_basis_accepts_struct():
    r = V.RelationshipModel(
        id="rel_test", source="a", target="b",
        relationship_type="AppealableTo", relationship_category="appellate_chain",
        data_quality="partial", sources=[],
        statutory_basis=[{"instrument_id": "bnss_2023", "provision": "s.415"}],
    )
    assert r.statutory_basis[0].instrument_id == "bnss_2023"


# ── S4: instrument registry ───────────────────────────────────────────────────

def test_seeded_instruments_validate():
    files = list((DATA / "legal_instruments").rglob("*.yaml"))
    assert files, "legal-instrument registry is empty"
    for path in files:
        assert V.validate_legal_instrument_file(path, strict=True) == []


def test_instrument_ids_are_snake_case():
    with pytest.raises(Exception):
        V.LegalInstrumentModel(
            id="not-snake-case", title="T", instrument_type="CentralAct",
            data_quality="partial", sources=[],
        )


def test_every_referenced_instrument_id_resolves():
    """A LegalBasisRef pointing at nothing is the drift the registry prevents."""
    known = set()
    for path in (DATA / "legal_instruments").rglob("*.yaml"):
        doc = yaml.safe_load(path.read_text()) or {}
        for row in doc.get("instruments", [doc]):
            if row.get("id"):
                known.add(row["id"])

    dangling = []
    for path in (DATA / "entities").rglob("*.yaml"):
        if "schema" in str(path):
            continue
        doc = yaml.safe_load(path.read_text())
        if not isinstance(doc, dict):
            continue
        for field in ("statutory_basis", "constitutional_basis"):
            value = doc.get(field)
            refs = [value] if isinstance(value, dict) else (value if isinstance(value, list) else [])
            for ref in refs:
                if isinstance(ref, dict) and ref.get("instrument_id") not in known:
                    dangling.append((doc.get("id"), ref.get("instrument_id")))
    assert dangling == [], f"dangling instrument references: {dangling}"


# ── the gate S sets for itself ────────────────────────────────────────────────

def test_existing_corpus_still_validates():
    """S is additive; every entity that validated before must validate now."""
    errors = []
    for path in sorted((DATA / "entities").rglob("*.yaml")):
        if "schema" in str(path):
            continue
        errors.extend(V.validate_entity_file(path, strict=True))
    assert errors == [], f"{len(errors)} validation errors: {errors[:5]}"
