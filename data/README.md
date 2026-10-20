# MedSafe-R Dataset Guide

## Current Analysis Input

Use [MedSafe_R_Dataset_v1.3_cleaned.xlsx](MedSafe_R_Dataset_v1.3_cleaned.xlsx), the corrected synthetic workbook with snapshot **31 July 2026**.

The original [v1 workbook](../MedSafe_R_Dataset_v1.xlsx) is retained as a legacy source. It has different counts and unresolved timeline inconsistencies; do not substitute it for v1.3 when reproducing the current results.

| Component | Retained records |
|---|---:|
| Device inventory | 1,200 |
| Maintenance events | 4,366 |
| Monthly operations | 7,193 |
| Safety events | 223 |
| Fictional regulatory signals | 18 |
| ML feature rows | 1,200 |

The 223 safety events affect **206 distinct devices**. The inventory-based overdue-PM estimate is **253 devices (21.1%)**.

## Documentation and Cleaning

The workbook contains a README, field-level data dictionary, change log, dashboard, PM-source flags and excluded-record sheets. Exclusions preserve 385 maintenance events, 15 safety events and 7 monthly operational records for traceability.

- Historical event windows cover exactly **90 dates (3 May-31 July 2026)** and **365 dates (1 August 2025-31 July 2026)**, inclusive.
- Telemetry features with `_30d` names refer to July's calendar month. `utilisation_90d_pct` is the mean of May-July utilisation. Use the dictionary's actual-window labels.
- PM dates use the later of inventory-register and valid logged PM dates. There are 550 log-supported dates, 639 inventory-only dates and 11 commissioning-date placeholders. The placeholders do not prove PM occurred.
- Exclude monthly records whose `hours_check` starts with `Fail` from relevant hours/utilisation calculations. There are nine such retained, flagged records; none is in May-July.
- Use `mtbf_measured_days` only as mean calendar days between recorded repairs for devices with two or more repairs. `days_since_last_repair` describes recency. Do not use the legacy `mtbf_days` sentinel 999 in numerical modelling or averages.
- `model_eligible` only tests an undocumented synthetic quality-score threshold; it is not comprehensive validation.

## Labels and Scores

`failure_next_30d` and `safety_event_next_90d` are synthetic generator-assigned outcomes. No future event records verify them. Trained models use them for exploratory internal evaluation.

`engineering_priority_score` is an unvalidated heuristic, not a probability or clinical risk score.

## Responsible Use

All data are synthetic: no real patients, hospitals, manufacturers, incidents or regulatory alerts are represented. Findings describe the simulated dataset and do not establish real-world predictive performance or safety benefits.

[Return to the project overview](../README.md)
