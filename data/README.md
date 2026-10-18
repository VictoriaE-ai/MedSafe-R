# MedSafe-R Dataset Guide

## Overview

MedSafe-R Dataset v1 is a synthetic dataset created for a Clinical Engineering and Healthcare Data Analytics portfolio.

It supports exploration of medical-device reliability, maintenance prioritisation and patient-safety indicators.

## Workbook Location

The workbook is currently stored in the repository’s main directory:

[Download MedSafe_R_Dataset_v1.xlsx](../MedSafe_R_Dataset_v1.xlsx)

## Dataset Contents

| Component | Records | Purpose |
|---|---:|---|
| Device inventory | 1,200 | Describes equipment, clinical criticality and maintenance information. |
| Maintenance events | 4,751 | Supports analysis of maintenance activity and equipment reliability. |
| Monthly operational records | 7,200 | Supports analysis of equipment operation over time. |
| Safety events | 238 | Provides simulated device-related safety incidents. |
| Fictional regulatory signals | 18 | Provides training examples for exploring safety surveillance. |
| Machine-learning feature rows | 1,200 | Provides prepared features and synthetic outcomes for modelling. |

The workbook also includes a README, data dictionary and Excel overview dashboard.

## Suggested Analysis

- Identify devices with overdue preventive maintenance.
- Explore downtime and recurring equipment failures.
- Compare maintenance needs across device types and departments.
- Examine relationships between reliability indicators and simulated safety events.
- Develop and evaluate predictive-maintenance models.

## Interpretation

The initial engineering-priority score is a transparent heuristic, not a validated clinical risk score.

The fields `failure_next_30d` and `safety_event_next_90d` contain synthetic outcome labels for model development. They are not predictions from a trained model.

## Limitations

All data are synthetic. No records represent real patients, hospitals, manufacturers, incidents or regulatory alerts.

Findings demonstrate analytical methods within a simulated environment. They do not establish real-world predictive performance or patient-safety benefits.

## Documentation Status

This guide provides a dataset overview. Detailed field definitions and data-quality checks will be documented as the analysis develops.
