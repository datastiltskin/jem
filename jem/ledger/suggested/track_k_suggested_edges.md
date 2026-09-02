# Track K — SUGGESTED edges (TN sub-district criminal magistracy)

**Not auto-applied.** Relationships are maintainer-only. Every row below is a
proposal to be confirmed against the cited primary before promotion.

Only one entity cleared the gate this run (`cjm_nilgiris`), so only edges with
that entity as an endpoint have a live source endpoint in the graph. Rows whose
source entity was **not** emitted are listed in the second table as blocked
proposals, so the reasoning survives in the ledger without inventing endpoints.

## Proposed edges with both endpoints present in the graph

| source | rel_type | target | category | basis | evidence_url | confidence |
|--------|----------|--------|----------|-------|--------------|------------|
| cjm_nilgiris | AppealableTo | tn_district_court_nilgiris | appellate_chain | BNSS 2023 s.13(1): "Every Chief Judicial Magistrate shall be subordinate to the Sessions Judge". Appeal routing by offence gravity, not money. The specific appellate provision (BNSS Ch. XXXI) was NOT read in this run — subordination is sourced, the appeal route is inferred from it and must be confirmed. | https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf | partial |
| hc_madras | AdministrativeSupervision | cjm_nilgiris | oversight | BNSS 2023 s.9(2): "The presiding officers of such Courts shall be appointed by the High Court"; s.10(1): "In every district, the High Court shall appoint a Judicial Magistrate of the first class to be the Chief Judicial Magistrate"; s.12(1) makes the CJM's local-limits power "Subject to the control of the High Court". Establishing notification II(2)/HO/141/2024 was made "after consultation with the High Court, Madras". | https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf | partial |

**Note on the Madurai bench.** The track prompt asks whether supervision routes
via `hc_madras` or `hc_madras_bench_madurai` per territorial jurisdiction. The
Nilgiris district falls outside the Madurai bench's districts on the ordinary
understanding, but **no primary allocating Nilgiris to a bench was opened in this
run**, so the row above is written to `hc_madras` (the High Court itself, which is
what BNSS names) and the bench question is left open for the maintainer.

## Blocked proposals (source entity not emitted — do not apply)

| source (not emitted) | rel_type | target | category | basis | evidence_url | confidence |
|----------------------|----------|--------|----------|-------|--------------|------------|
| cjm_ranipet | AppealableTo | tn_district_court_ranipet | appellate_chain | Blocked: the CJM character of the Ranipet court is contested (see ledger `cjm_ranipet`). Establishment of *a* Court of Judicial Magistrate at Ranipet is sourced; its class is not. | https://www.stationeryprinting.tn.gov.in/gazette/2024/2_II_2_2024.pdf | unsourced_candidate |
| cjm_tirupathur | AppealableTo | tn_district_court_tirupathur | appellate_chain | Blocked: same conflict as Ranipet. | https://www.stationeryprinting.tn.gov.in/gazette/2024/2_II_2_2024.pdf | unsourced_candidate |
| jmfc_nanguneri | AppealableTo | tn_district_court_tirunelveli | appellate_chain | Blocked: existence and year (2018) are sourced twice over, but no opened primary states the magistrate's **class**, and the `jmfc_` id asserts first class. | https://www.stationeryprinting.tn.gov.in/gazette/2018/43_II_2.pdf | unsourced_candidate |
