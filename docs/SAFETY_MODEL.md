# Safety model

## Status

All rules and thresholds in this repository are illustrative software behavior for synthetic records. They are not medical guidance or a validated triage scale.

## Safety floors

| Rule | Synthetic trigger | Floor |
|---|---|---:|
| `SAFE-001` | Recorded oxygen saturation below prototype threshold | Critical |
| `SAFE-002` | Recorded systolic pressure below prototype threshold | Critical |
| `SAFE-003` | Recorded as unresponsive | Critical |
| `SAFE-004` | Responsive only to pain | Emergent |
| `SAFE-005` | Severe bleeding category | Critical |
| `SAFE-006` | Seizure category | Emergent |
| `SAFE-007` | Chest pain with an abnormal recorded vital | Critical |
| `SAFE-008` | Pediatric respiratory symptoms with observed distress | Emergent |
| `SAFE-009` | Young child with high recorded temperature and distress | Emergent |
| `SAFE-010` | Geriatric atypical symptoms with an abnormal vital | Emergent |
| `SAFE-011` | High-risk symptom plus missing critical measurement | Emergent |
| `SAFE-012` | Altered mental status category | Emergent |

If several rules fire, the most urgent floor wins and every rule remains visible in the recommendation.

## Monitoring priority

State selection follows this precedence:

1. Critical escalation.
2. Deteriorating.
3. Stale information.
4. Reassessment due.
5. Stable.
6. Manual review replaces stable when confidence is low or CDM fails.

A lower-priority state never erases a higher-priority alert. For example, a critical record can also contain a stale-data alert, but its action remains immediate review.

## Reassessment intervals

Normal-mode prototype values are 0, 10, 30, 60, and 120 minutes for acuity levels 1 through 5. Surge mode halves every non-zero interval. These demonstrate configurable operations and must not be interpreted as real clinical guidance.

## Model failure

CDM failure cannot disable rule evaluation. The fallback marks recommendations stale, includes new arrivals, preserves the safety/acuity order, and requests manual reassessment.

## Required real-world work

Clinical deployment would require approved local protocols, age- and condition-specific evidence, validation across representative populations, prospective evaluation, human-factors testing, alarm-fatigue analysis, secure integration, formal change control, monitoring, incident response, and licensed-clinician governance.
