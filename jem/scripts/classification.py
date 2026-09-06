"""
classification.py — the single source of truth for entity classification.

Two orthogonal axes derived from `type` (no per-entity field, no drift):
  nature   ∈ {institution, personnel}
  function ∈ {judicial, quasi_judicial, support_apparatus}

"Judicial personnel" is a DERIVED intersection (personnel × judicial), never a
stored bucket. The old "non-judicial" bucket is `support_apparatus`.

Imported by:
  - validate.py  → assert every entity `type` is classifiable
  - derive.py    → compute counts by (nature, function), excluding generics
  - build.py     → surface class on nodes for the UI

REVIEW FLAGS (maintainer call — marked below): ADRBody, LegalOfficer and
PartyRole are defaulted here but are the genuinely arguable rows. Change the
map, or use a per-entity classification_override, if the panel decides
otherwise. Each moves bucket totals, so settle them before publishing counts.
"""

from typing import Tuple

# type → (nature, function)
TYPE_CLASSIFICATION = {
    # ── Judicial institutions (courts) ──────────────────────────────────────
    "ConstitutionalCourt":      ("institution", "judicial"),
    "HighCourtBench":           ("institution", "judicial"),
    "SubordinateCivilCourt":    ("institution", "judicial"),
    "SubordinateCriminalCourt": ("institution", "judicial"),
    "CityCivilCourt":           ("institution", "judicial"),
    "SpecialCourt":             ("institution", "judicial"),
    "CommercialCourt":          ("institution", "judicial"),   # S1

    # ── Quasi-judicial institutions ─────────────────────────────────────────
    "CentralTribunal":          ("institution", "quasi_judicial"),
    "StateTribunal":            ("institution", "quasi_judicial"),
    "ConsumerCommission":       ("institution", "quasi_judicial"),
    "ArbitralInstitution":      ("institution", "quasi_judicial"),
    "MediationBody":            ("institution", "quasi_judicial"),
    "RegulatoryBodyQJ":         ("institution", "quasi_judicial"),
    "ADRBody":                  ("institution", "quasi_judicial"),  # REVIEW: NALSA/SLSA are legal-aid support; Lok Adalats adjudicate. Panel call.

    # ── Support / enabling apparatus (executive + legislative ecosystem) ─────
    "AppointmentBody":          ("institution", "support_apparatus"),
    "InvestigativeAgency":      ("institution", "support_apparatus"),
    "ProsecutionBody":          ("institution", "support_apparatus"),
    "TrainingBody":             ("institution", "support_apparatus"),
    "AuditBody":                ("institution", "support_apparatus"),
    "DigitalInfraBody":         ("institution", "support_apparatus"),
    "SecurityBody":             ("institution", "support_apparatus"),
    "FinancingBody":            ("institution", "support_apparatus"),
    "LegislativeBody":          ("institution", "support_apparatus"),
    "ExecutiveBody":            ("institution", "support_apparatus"),
    "ProfessionalBody":         ("institution", "support_apparatus"),

    # ── Personnel / roles ───────────────────────────────────────────────────
    "LegalOfficer":             ("personnel", "support_apparatus"),  # REVIEW: AG/SG — personnel; function arguable. Panel call.

    # Role-archetype layer (cluster people_roles, role_layer: true). These five
    # types are live in the corpus but were absent from the packet map; the
    # judicial ones are the personnel × judicial intersection the two-axis
    # design exists to express.
    "JudicialOfficerRole":      ("personnel", "judicial"),
    "CourtAdminRole":           ("personnel", "support_apparatus"),
    "LegalProfessionalRole":    ("personnel", "support_apparatus"),
    "ProsecutionRole":          ("personnel", "support_apparatus"),
    "PartyRole":                ("personnel", "support_apparatus"),  # REVIEW: litigants/witnesses neither adjudicate nor enable; support_apparatus is by elimination, not fit. Panel call.

    # ── Status placeholders — classify via override when their intended
    #    type is known; default institution/support until then ───────────────
    "StatutoryBodyNotConstituted": ("institution", "support_apparatus"),
    "ProposedBody":                ("institution", "support_apparatus"),
}


def classify(entity_type: str) -> Tuple[str, str]:
    """Return (nature, function) for a type. Raises if the type is unmapped —
    this is deliberate: a new type must be classified before it can validate."""
    if entity_type not in TYPE_CLASSIFICATION:
        raise ValueError(
            f"Unclassified entity type '{entity_type}'. Add it to "
            f"TYPE_CLASSIFICATION in classification.py before use."
        )
    return TYPE_CLASSIFICATION[entity_type]


def classify_entity(entity: dict) -> Tuple[str, str]:
    """Classify a loaded entity dict, honouring classification_override."""
    ov = entity.get("classification_override")
    if ov:
        return (ov["nature"], ov["function"])
    return classify(entity.get("type"))


def is_countable(entity: dict) -> bool:
    """Generics are never counted in entity totals."""
    return not bool(entity.get("is_generic_rollup", False))


# Convenience for derive.py: initialise a counts structure.
def empty_counts() -> dict:
    return {
        (n, f): 0
        for n in ("institution", "personnel")
        for f in ("judicial", "quasi_judicial", "support_apparatus")
    }
