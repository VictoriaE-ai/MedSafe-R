# MedSafe-R
### Medical Device Reliability & Patient Safety Intelligence

**A synthetic-data portfolio prototype by Victoria Ekweani | VictoryHealth Analytics**

MedSafe-R explores how equipment records, maintenance history and simulated safety events can support transparent clinical-engineering analysis. It combines descriptive reliability analytics with an engineering-priority heuristic and predictive-modelling baselines.

**Status:** exploratory analysis and internal model evaluation completed. Power BI updates, model explanations and real-world validation remain in development or planned.

## Project Question

**Which devices need engineering attention, why, and what evidence supports the priority?**

## Start Here

- [Chart report (PDF)](MedSafe_R_Chart_Report.pdf)
- [Offline HTML report](MedSafe_R_Analysis.html) - download the file and open it in a browser.
- [Chart images](charts/) and [supporting CSV tables](tables/)
- [Corrected synthetic dataset v1.3](data/MedSafe_R_Dataset_v1.3_cleaned.xlsx)
- [Data guide](data/README.md), [analysis code](analysis.py) and [model methods](methods.json)

## Dataset

The current analysis uses **corrected v1.3**, snapshot **31 July 2026**.

| Data component | Records |
|---|---:|
| Devices | 1,200 |
| Retained maintenance events | 4,366 |
| Retained monthly operational records | 7,193 |
| Retained safety events | 223 |
| Fictional regulatory signals | 18 |
| ML feature rows | 1,200 |

Excluded records are preserved in separate workbook sheets. The data dictionary, change log and PM-date assumptions are included in the workbook. The original root-level `MedSafe_R_Dataset_v1.xlsx` is retained as a **legacy source**, not the current analysis input.

## Completed Analysis

1. Identify overdue preventive maintenance, including PM-source sensitivity.
2. Explore recorded downtime and recurring corrective repairs.
3. Compare maintenance workload and rates across device types and departments.
4. Examine historical associations with simulated safety events.
5. Evaluate logistic regression and random forest baselines against an engineering heuristic and prevalence baseline.

The package includes six chart sheets, 24 supporting tables, fold-level predictions and reproducible Python code.

## Main Findings

- **253 devices (21.1%)** have overdue PM under the documented inventory-date precedence assumptions.
- Corrective repairs contribute **76.3%** of recorded maintenance downtime.
- **223 safety events** affect **206 distinct devices**.
- Failure-label ROC AUC is approximately **0.68 for random forest** and **0.70 for the engineering heuristic**.
- Reviewing the 120 highest-scored devices finds **6 of 41 failure-positive labels** with random forest, versus **10 of 41** with the heuristic. These are internally evaluated synthetic-label results.

![Overdue preventive maintenance analysis](charts/01_overdue_pm.png)

![Downtime and recurring repairs](charts/02_downtime_recurrence.png)

## Methods and Validation

- Exact historical event windows: **3 May-31 July 2026 (90 days)** and **1 August 2025-31 July 2026 (365 days)**, inclusive.
- Calendar-month telemetry uses July; the utilisation feature averages May-July.
- Preprocessing is fitted inside each training fold. Fixed model settings use stratified five-fold cross-validation repeated three times.
- AUC, average precision, review-budget capture and Brier scores are documented. AUC intervals condition on fixed out-of-fold predictions and do not include model-retraining uncertainty.
- No external, prospective or real-world validation has been performed. No operational decision threshold is validated.

## Reproduce the Analysis

Use **Python 3.11 or later**; the recorded run used Python **3.12.14**. Download or clone the full repository, preserving its folders. From the repository directory:

```bash
python -m pip install -r requirements.txt
python analysis.py
```

The default input is `data/MedSafe_R_Dataset_v1.3_cleaned.xlsx`. An optional input path can be supplied:

```bash
python analysis.py path/to/workbook.xlsx
```

The script regenerates `charts/`, `tables/`, both reports, `methods.json`, `requirements.txt` and `ANALYSIS_NOTES.md` beside the script. It does **not** overwrite this project README. Run in a working copy if you want to retain the uploaded outputs unchanged. The script's assertions target this dataset version; adapting it to other data requires reviewing those checks.

## Tools and Development Status

**Used in the reproducible analysis:** Python, pandas, NumPy, SciPy, scikit-learn and Matplotlib. Excel holds the source workbook.

**Work in progress:** updating the separate Power BI dashboard to the corrected data and completed analysis. No Power BI file is included in this repository yet.

**Planned development:** model explanations and stability checks; probability calibration and practical review thresholds; safety-signal detection and monitoring; clinical-engineering feedback; external or prospective validation. SQL remains a possible future extension, not a completed implementation here.

## Limitations and Responsible Use

All records, manufacturers, regulatory signals and future outcomes are synthetic. Labels are generator-designated outcomes, not model predictions or verified future events. Models were trained and evaluated against those labels, which does not establish real-world predictive performance.

PM estimates depend on 639 inventory-only dates and 11 commissioning-date placeholders. Nine operational records fail hours-plausibility checks and must be excluded from relevant analyses. Repairs are not necessarily independent failures; recorded downtime may overlap. Same-period safety associations do not establish causality. Synthetic generator logic may favour the engineering heuristic.

This is a learning and portfolio prototype, not a validated clinical, regulatory or maintenance decision tool. It does not establish patient-safety benefits.

## Author

**Victoria Ekweani - VictoryHealth Analytics**

[View my portfolio](https://github.com/VictoriaE-ai/VictoryHealth-Analytics)
