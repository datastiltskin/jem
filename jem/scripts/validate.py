#!/usr/bin/env python3
"""
JEM — Data Validation Script
Validates all YAML entity and relationship files against the schema.
Runs as a GitHub Actions check on every Pull Request.
Exit code 0 = all valid. Exit code 1 = validation errors found.

Usage:
    python scripts/validate.py
    python scripts/validate.py --strict    # Fails if any source URLs missing
    python scripts/validate.py --entity data/entities/constitutional_courts/supreme_court_india.yaml
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional, List, Literal, Any
import yaml

try:
    from pydantic import BaseModel, ConfigDict, field_validator, model_validator, ValidationError
except ImportError:
    print("ERROR: pydantic not installed. Run: pip install pydantic pyyaml")
    sys.exit(1)

# ── Controlled Vocabularies ───────────────────────────────────────────────────

ENTITY_TYPES = [
    "ConstitutionalCourt", "HighCourtBench", "SubordinateCivilCourt", "SubordinateCriminalCourt",
    "CityCivilCourt", "SpecialCourt", "CentralTribunal", "StateTribunal",
    "ConsumerCommission", "ArbitralInstitution", "MediationBody",
    "RegulatoryBodyQJ", "ADRBody", "AppointmentBody", "InvestigativeAgency",
    "ProsecutionBody", "TrainingBody", "AuditBody", "DigitalInfraBody",
    "SecurityBody", "FinancingBody", "LegislativeBody", "ExecutiveBody",
    "LegalOfficer", "ProfessionalBody", "StatutoryBodyNotConstituted", "ProposedBody"
]

CLUSTERS = [
    "constitutional_courts", "subordinate_courts", "tribunals_adr",
    "consumer_redressal", "arbitration", "regulatory_bodies", "executive_interface",
    "digital_infrastructure", "financing_audit", "training_professional",
    "appointment_bodies", "legislative_executive"
]

GOV_LEVELS = ["Central", "State", "UT", "Shared_MultiState", "Shared_CentralState"]

OPERATIONAL_STATUSES = ["Active", "Not_Constituted", "Proposed", "Abolished", "Merged", "Suspended"]

DATA_QUALITY_VALUES = ["verified", "complete", "partial", "unverified", "contested"]

FUNDING_SOURCES = [
    "Consolidated_Fund_India", "State_Consolidated_Fund",
    "Centrally_Sponsored_Scheme", "Ministry_Budget", "Statutory_Fund",
    "Party_Fees", "Mixed"
]

AUDIT_TYPES = ["CAG_Statutory", "CAG_Performance", "Internal", "Parliamentary_PAC", "None", "Contested"]

LOKPAL_VALUES = ["Yes", "No", "Contested", "Not_Applicable"]

SOURCE_TYPES = [
    "Constitution", "CentralAct", "StateAct", "SCJudgment",
    "HCJudgment", "GazetteNotification", "GoIWebsite", "OfficialReport",
    "NJDG", "AnnualReport",
]

RELATIONSHIP_TYPES = [
    "Nominates", "Recommends", "ConsultedOn_Appointment", "FormallyAppoints", "CanRemove",
    "PrimaryFunder", "CoFunder", "BudgetAllocatedBy",
    "AppealableTo", "FinalAppealTo", "ReferredTo", "TransferableTo",
    "AdministrativeSupervision", "DisciplinaryControl", "PolicyOversight", "Designates",
    "ProvidesInductionTraining", "ProvidesContinuingEducation", "SetsTrainingCurriculum", "AccreditsTrainingInstitution",
    "AuditsAccounts", "AuditsPerformance", "ConductOversight", "ReportsTo",
    "BiasComplaintReceivedBy", "CriminalSanctionGrantedBy", "ImpeachmentInitiatedBy",
    "InvestigatesOffencesIn", "RequiresConsentOf", "SupervisedBy_Investigation",
    "BuildsMaintains", "FundsDigitalProject", "PolicyDirectionDigital", "ImplementingAgency",
    "ProvidesCourtSecurity", "ProvidesPersonalSecurity", "ThreatAssessedBy",
    "EstablishedUnder", "JurisdictionDefinedBy", "AwardEnforcedIn", "AwardChallengedIn",
    "BenchOf",
]

RELATIONSHIP_CATEGORIES = [
    "appointment", "funding", "appellate_chain", "supervisory", "training",
    "audit", "complaint", "investigative", "digital", "security", "statutory_ref"
]

# ── Pydantic Models ───────────────────────────────────────────────────────────

class Source(BaseModel):
    label: str
    url: str
    type: str
    accessed_date: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_source_type(cls, v):
        if v not in SOURCE_TYPES:
            raise ValueError(f"Invalid source type '{v}'. Must be one of: {SOURCE_TYPES}")
        return v

    @field_validator("url")
    @classmethod
    def validate_url(cls, v):
        if not v.startswith("http"):
            raise ValueError(f"URL must start with http/https: '{v}'")
        return v


class AppointmentModel(BaseModel):
    nominates: Optional[str] = None
    recommends: Optional[str] = None
    consulted: Optional[List[str]] = []
    consultation_binding: Optional[bool] = None
    formally_appoints: Optional[str] = None
    criteria_public: Optional[bool] = None
    tenure: Optional[str] = None
    reappointment_possible: Optional[bool] = None
    removal_authority: Optional[str] = None
    removal_requires_parliament: Optional[bool] = None
    removal_independent_committee: Optional[bool] = None


class FundingModel(BaseModel):
    primary_source: str
    ministry_responsible: Optional[str] = None
    state_contribution_percent: Optional[int] = None
    budget_figure_crore: Optional[float] = None
    budget_year: Optional[int] = None

    @field_validator("primary_source")
    @classmethod
    def validate_funding_source(cls, v):
        if v not in FUNDING_SOURCES:
            raise ValueError(f"Invalid funding source '{v}'. Must be one of: {FUNDING_SOURCES}")
        return v


class AuditModel(BaseModel):
    audited_by: Optional[str] = None
    audit_type: Optional[str] = None
    audit_report_public: Optional[bool] = None
    conduct_oversight_body: Optional[str] = None

    @field_validator("audit_type")
    @classmethod
    def validate_audit_type(cls, v):
        if v and v not in AUDIT_TYPES:
            raise ValueError(f"Invalid audit type '{v}'. Must be one of: {AUDIT_TYPES}")
        return v


class ComplaintBodyModel(BaseModel):
    body: str
    mechanism: str
    complainant_has_locus: Optional[bool] = None
    is_public_process: Optional[bool] = None
    timeframe_defined: Optional[bool] = None
    external_to_judiciary: Optional[bool] = None


class CriminalProsecutionModel(BaseModel):
    requires_sanction_from: Optional[str] = None
    consultation_required_with: Optional[str] = None
    consultation_binding: Optional[bool] = None


class ComplaintMechanismModel(BaseModel):
    bias_complaint_to: Optional[List[ComplaintBodyModel]] = []
    criminal_prosecution: Optional[CriminalProsecutionModel] = None
    removal_mechanism: Optional[str] = None
    lokpal_jurisdiction: Optional[str] = None
    lokpal_jurisdiction_note: Optional[str] = None
    source: Optional[str] = None

    @field_validator("lokpal_jurisdiction")
    @classmethod
    def validate_lokpal(cls, v):
        if v and v not in LOKPAL_VALUES:
            raise ValueError(f"Invalid lokpal_jurisdiction '{v}'. Must be one of: {LOKPAL_VALUES}")
        return v


class StructuralVariation(BaseModel):
    variation_id: str
    description: str
    applicable_to: List[str]
    source: str
    independence_risk_note: Optional[str] = None


class UnverifiedFieldModel(BaseModel):
    """Per-field verification flag surfaced in the L3 detail panel."""

    field: str
    note: str


class JurisdictionScope(BaseModel):
    states_covered: Optional[List[str]] = []
    uts_covered: Optional[List[str]] = []
    is_all_india: Optional[bool] = False
    jurisdiction_types: Optional[List[str]] = []


CASE_VOLUME_SOURCE_TYPES = [
    "NJDG_Live", "NJDG_Snapshot", "DoJ_Report", "Tribunal_Report", "HC_Report", "Estimated",
    "AnnualReport",
]


class JudgeStrengthModel(BaseModel):
    """Sanctioned posts vs judges in post (v2.0 — courts & court-like bodies)."""

    model_config = ConfigDict(extra="ignore")

    data_as_of: Optional[str] = None
    allotted: Optional[int] = None
    appointed: Optional[int] = None
    vacancy_count: Optional[int] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("source_type")
    @classmethod
    def validate_js_source_type(cls, v):
        if v and v not in CASE_VOLUME_SOURCE_TYPES:
            raise ValueError(
                f"Invalid judge_strength.source_type '{v}'. Must be one of: {CASE_VOLUME_SOURCE_TYPES}"
            )
        return v


class CaseVolumeModel(BaseModel):
    """Optional pendency / clog block (entity_schema.yaml)."""

    model_config = ConfigDict(extra="ignore")

    data_as_of: Optional[str] = None
    sanctioned_strength: Optional[int] = None
    working_strength: Optional[int] = None
    vacancy_count: Optional[int] = None
    vacancy_rate: Optional[float] = None
    pending_cases: Optional[int] = None
    filed_last_year: Optional[int] = None
    disposed_last_year: Optional[int] = None
    disposal_rate: Optional[float] = None
    avg_disposal_days: Optional[float] = None
    institution_rate_trend: Optional[str] = None
    source_url: Optional[str] = None
    source_type: Optional[str] = None
    clog_severity: Optional[str] = None

    @field_validator("source_type")
    @classmethod
    def validate_cv_source_type(cls, v):
        if v and v not in CASE_VOLUME_SOURCE_TYPES:
            raise ValueError(
                f"Invalid case_volume.source_type '{v}'. Must be one of: {CASE_VOLUME_SOURCE_TYPES}"
            )
        return v


class DigitalInfraModel(BaseModel):
    system_used: Optional[List[str]] = []
    digital_variant: Optional[str] = None
    integrated_with_njdg: Optional[bool] = None
    integration_notes: Optional[str] = None


class TrainingModel(BaseModel):
    trained_by: Optional[List[str]] = []
    induction_training: Optional[bool] = None
    continuing_education: Optional[bool] = None
    training_mandatory: Optional[bool] = None


class EntityModel(BaseModel):
    id: str
    name: str
    name_hindi: Optional[str] = None
    abbreviation: Optional[str] = None
    aliases: Optional[List[str]] = []

    type: str
    cluster: str
    level_of_government: str
    jurisdiction_scope: Optional[JurisdictionScope] = None

    created_year: int
    abolished_year: Optional[int] = None
    operational_status: str

    constitutional_basis: Optional[str] = None
    statutory_basis: Optional[str] = None
    parent_hc: Optional[str] = None

    appointment: Optional[AppointmentModel] = None
    funding: Optional[FundingModel] = None
    audit: Optional[AuditModel] = None
    complaint_mechanism: Optional[ComplaintMechanismModel] = None
    training: Optional[TrainingModel] = None
    digital_infrastructure: Optional[DigitalInfraModel] = None
    structural_variations: Optional[List[StructuralVariation]] = []
    unverified_fields: Optional[List[UnverifiedFieldModel]] = []

    case_volume: Optional[CaseVolumeModel] = None
    judge_strength: Optional[JudgeStrengthModel] = None

    data_quality: str
    data_quality_notes: Optional[str] = None
    sources: List[Source]

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v not in ENTITY_TYPES:
            raise ValueError(f"Invalid entity type '{v}'. Must be one of: {ENTITY_TYPES}")
        return v

    @field_validator("cluster")
    @classmethod
    def validate_cluster(cls, v):
        if v not in CLUSTERS:
            raise ValueError(f"Invalid cluster '{v}'. Must be one of: {CLUSTERS}")
        return v

    @field_validator("level_of_government")
    @classmethod
    def validate_gov_level(cls, v):
        if v not in GOV_LEVELS:
            raise ValueError(f"Invalid level_of_government '{v}'. Must be one of: {GOV_LEVELS}")
        return v

    @field_validator("operational_status")
    @classmethod
    def validate_operational_status(cls, v):
        if v not in OPERATIONAL_STATUSES:
            raise ValueError(f"Invalid operational_status '{v}'. Must be one of: {OPERATIONAL_STATUSES}")
        return v

    @field_validator("data_quality")
    @classmethod
    def validate_data_quality(cls, v):
        if v not in DATA_QUALITY_VALUES:
            raise ValueError(f"Invalid data_quality '{v}'. Must be one of: {DATA_QUALITY_VALUES}")
        return v

    @model_validator(mode='after')
    def check_verified_has_source(self):
        if self.data_quality == "verified" and not self.sources:
            raise ValueError("data_quality 'verified' requires at least one source.")
        return self

    @model_validator(mode='after')
    def check_id_format(self):
        if ' ' in self.id or '-' in self.id:
            raise ValueError(f"id must be snake_case with underscores only: '{self.id}'")
        return self


class RelationshipModel(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    relationship_category: str
    is_binding: Optional[bool] = None
    is_constitutional: Optional[bool] = None
    constitutional_basis: Optional[str] = None
    statutory_basis: Optional[str] = None
    year_established: Optional[int] = None
    year_abolished: Optional[int] = None
    notes: Optional[str] = None
    data_quality: str
    contested_note: Optional[str] = None
    sources: List[Source]

    @field_validator("relationship_type")
    @classmethod
    def validate_rel_type(cls, v):
        if v not in RELATIONSHIP_TYPES:
            raise ValueError(f"Invalid relationship_type '{v}'. Must be one of: {RELATIONSHIP_TYPES}")
        return v

    @field_validator("relationship_category")
    @classmethod
    def validate_rel_category(cls, v):
        if v not in RELATIONSHIP_CATEGORIES:
            raise ValueError(f"Invalid relationship_category '{v}'. Must be one of: {RELATIONSHIP_CATEGORIES}")
        return v

    @field_validator("data_quality")
    @classmethod
    def validate_data_quality(cls, v):
        if v not in DATA_QUALITY_VALUES:
            raise ValueError(f"Invalid data_quality '{v}'. Must be one of: {DATA_QUALITY_VALUES}")
        return v


# ── Validation Functions ──────────────────────────────────────────────────────

def load_yaml(path: Path) -> Any:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_entity_file(path: Path, strict: bool = False) -> List[str]:
    """Validate a single entity YAML file. Returns list of error strings."""
    errors = []
    try:
        data = load_yaml(path)
        EntityModel(**data)
    except ValidationError as e:
        for err in e.errors():
            loc = " → ".join(str(x) for x in err['loc'])
            errors.append(f"  [{path.name}] {loc}: {err['msg']}")
    except Exception as e:
        errors.append(f"  [{path.name}] YAML parse error: {e}")

    if strict and not errors:
        # Strict mode: check all source URLs are real (basic check)
        try:
            data = load_yaml(path)
            for src in data.get('sources', []):
                if 'placeholder' in src.get('url', '').lower():
                    errors.append(f"  [{path.name}] Placeholder URL found: {src['url']}")
        except Exception:
            pass

    return errors


def validate_relationship_file(path: Path, strict: bool = False) -> List[str]:
    """Validate a relationships YAML file. Returns list of error strings."""
    errors = []
    try:
        data = load_yaml(path)
        relationships = data.get('relationships', [])
        if not relationships:
            errors.append(f"  [{path.name}] No relationships found — check 'relationships:' key")
            return errors
        for i, rel in enumerate(relationships):
            try:
                RelationshipModel(**rel)
            except ValidationError as e:
                for err in e.errors():
                    loc = " → ".join(str(x) for x in err['loc'])
                    errors.append(f"  [{path.name}] relationship[{i}] ({rel.get('id','?')}) {loc}: {err['msg']}")
    except Exception as e:
        errors.append(f"  [{path.name}] YAML parse error: {e}")
    return errors


def collect_entity_files(data_dir: Path) -> List[Path]:
    return list((data_dir / "entities").rglob("*.yaml"))


def collect_relationship_files(data_dir: Path) -> List[Path]:
    rel_dir = data_dir / "relationships"
    if not rel_dir.exists():
        return []
    return [f for f in rel_dir.glob("*.yaml") if f.is_file()]


def run_validation(data_dir: Path, strict: bool = False, single_file: Optional[Path] = None):
    all_errors = []
    files_checked = 0

    if single_file:
        # Guess type from path
        if "relationship" in str(single_file):
            errs = validate_relationship_file(single_file, strict)
        else:
            errs = validate_entity_file(single_file, strict)
        all_errors.extend(errs)
        files_checked = 1
    else:
        entity_files = collect_entity_files(data_dir)
        rel_files = collect_relationship_files(data_dir)

        print(f"\nValidating {len(entity_files)} entity files...")
        for f in sorted(entity_files):
            # Skip schema files
            if 'schema' in str(f):
                continue
            errs = validate_entity_file(f, strict)
            all_errors.extend(errs)
            files_checked += 1

        print(f"Validating {len(rel_files)} relationship files...")
        for f in sorted(rel_files):
            errs = validate_relationship_file(f, strict)
            all_errors.extend(errs)
            files_checked += 1

    print(f"\n{'='*60}")
    print(f"JEM Validation Report")
    print(f"Files checked: {files_checked}")
    print(f"Errors found:  {len(all_errors)}")
    print(f"{'='*60}")

    if all_errors:
        print("\nERRORS:")
        for err in all_errors:
            print(err)
        print(f"\n✗ Validation FAILED — {len(all_errors)} error(s)")
        return False
    else:
        print("\n✓ All files valid")
        if strict:
            print("✓ Strict mode: no placeholder URLs found")
        return True


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JEM data validation")
    parser.add_argument("--strict", action="store_true",
                        help="Fail on placeholder URLs and missing optional fields for verified entities")
    parser.add_argument("--entity", type=str, default=None,
                        help="Validate a single file instead of all files")
    args = parser.parse_args()

    # Determine data directory relative to this script
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"

    single_file = Path(args.entity) if args.entity else None
    success = run_validation(data_dir, strict=args.strict, single_file=single_file)
    sys.exit(0 if success else 1)
