# Judiciary Entity Map (India) - JEM: data model and score formulae

`scripts/derive.py` computes all derived scores from structural data
fields. No editorial judgment is applied. Every point traces back to a
data field documented here.

---

## Independence Risk Score

**Definition:** Measures structural conditions that create dependency,
opacity, or conflicts of interest in an entity's design.
Higher = more structural risk. Does not indicate actual misconduct.

**Scale:** 0-2 Low | 3-5 Moderate | 6-8 High | 9+ Severe

### Factors

| Factor | Points | Source field |
|---|---|---|
| Appointed directly by executive body | +3 | `appointment.formally_appoints` |
| Appointed by independent collegium | −2 | `appointment.nominates` contains "collegium" |
| Appointment via Parliamentary process | −1 | `appointment.formally_appoints` contains "parliament" |
| Reappointment possible by same executive | +2 | `appointment.reappointment_possible == true` AND appointer is executive |
| No publicly stated appointment criteria | +1 | `appointment.criteria_public == false` |
| Removal by same authority that appoints (no independent committee) | +1 | `appointment.removal_authority` == appointer AND `removal_independent_committee == false` |
| Removal requires Parliamentary process | −1 | `appointment.removal_requires_parliament == true` |
| Funder == Appointing authority | +2 | `funding.ministry_responsible` == appointer |
| Funded by parties (not state) | −1 | `funding.primary_source == Party_Fees` |
| No external financial audit | +1 | `audit.audit_type` is None or empty |
| No independent conduct oversight body | +1 | `audit.conduct_oversight_body` is empty |
| Conduct oversight body is the entity itself | +1 | `audit.conduct_oversight_body` == entity id |
| Audit reports not public | +1 | `audit.audit_report_public == false` |
| No bias complaint mechanism exists | +2 | `complaint_mechanism.bias_complaint_to` is empty |
| All complaint mechanisms are internal | +1 | No entry in `bias_complaint_to` has `external_to_judiciary == true` |
| Complaint process is not public | +1 | No entry has `is_public_process == true` |
| Complainant has no locus | +1 | No entry has `complainant_has_locus == true` |
| No defined timeframe for complaint | +1 | No entry has `timeframe_defined == true` |
| Lokpal has no jurisdiction | +1 | `complaint_mechanism.lokpal_jurisdiction == No` |
| Constitutional basis (harder to politicise) | −2 | `constitutional_basis` is populated |
| Statutory body not constituted (regulatory vacuum) | +3 | `operational_status == Not_Constituted` |

**Minimum score: 0** (negative contributions cannot take score below zero)

---

## Discretionary Power Score

**Definition:** Measures concentration of discretionary decision-making power
in an entity. High discretionary power combined with high independence risk
is a structural concern. Discretionary power alone is not problematic.

**Scale:** 0-2 Low | 3-5 Moderate | 6-8 High | 9+ Very High

### Base score by entity type

| Type | Base |
|---|---|
| ConstitutionalCourt | 4 |
| AppointmentBody | 4 |
| RegulatoryBodyQJ | 3 |
| InvestigativeAgency | 3 |
| SubordinateCriminalCourt | 3 |
| SubordinateCivilCourt | 2 |
| SpecialCourt | 2 |
| CentralTribunal | 2 |
| AuditBody | 2 |
| ArbitralInstitution | 1 |
| All others | 1 |

### Entity-specific additions (documented extra-statutory discretion)

| Entity | Extra points | Documented basis |
|---|---|---|
| supreme_court_india | +5 | Master of Roster, PIL jurisdiction, suo moto, contempt |
| chief_justice_india | +5 | Master of Roster, no codified rules for bench allocation |
| collegium_sc | +5 | Entirely opaque appointment process, no statutory criteria |

### Universal factors

| Factor | Points |
|---|---|
| No public criteria for key decisions | +1 |
| Has removal authority over other entities | +1 |
| Controls own case listing / bench composition (ConstitutionalCourt only) | +2 |
| No universal mandatory timeline for all decisions | +1 |

---

## Governance nodes and score exclusions

Structural IR and DP scores apply to adjudicatory, regulatory, and investigative
entities whose independence and discretion matter for judicial governance analysis.
Governance nodes (officeholders, ministries, and abstract executive bodies) appear
in the relationship graph for appointment chains, but they are not scored.

`scripts/derive.py` sets both scores to 0 with breakdown key
`Scores excluded: governance officeholder or administrative body` when any of:

| Rule | Examples |
|---|---|
| `type == AppointmentBody` | Not excluded. Committees remain scored. |
| `id` starts with `ministry_` or `minister_` | `ministry_home_affairs`, `minister_home_affairs` |
| Fixed officeholder IDs | `president_india`, `prime_minister`, `chief_justice_india`, `governor_state`, Speakers, LoP, Deputy Chairman Rajya Sabha |
| `id` ends with `_lieutenant_governor` or `_advocate_general` | `dl_lieutenant_governor`, state AGs |
| `type == ExecutiveBody` and `cluster` in `legislative_executive` or `executive_interface` | `central_government`, Union ministries |

Rationale: the minister-versus-ministry distinction (PHRA 1993 s.4, CVC Act 2003 s.4)
and the Lokpal Act CBI Director committee are appointment topology, not bodies whose
case volume or bench composition is modeled. Appointment committees (`AppointmentBody`)
keep their scores because they concentrate statutory appointment discretion.

---

## Scores and community validation

Scores are computed automatically but require human review to confirm that:
- The formula input fields are accurately populated
- The entity-specific extra-statutory discretion entries are sourced
- No data quality issues affect the inputs

Unvalidated scores display with a "⚐ Pending community review" badge in the UI.

To mark a score as validated, set in the entity YAML:
```yaml
derived:
  scores_validated: true
```
This should only be done after the entity's data quality is `verified`
and the score breakdown has been reviewed against primary sources.
