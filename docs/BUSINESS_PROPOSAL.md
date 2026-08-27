# Business proposal

## Executive proposition

PatientTriage.ai is a focused emergency-department coordination layer. It helps clinical teams see who may need review next, who is deteriorating or overdue, where the 18 synthetic care spaces are occupied, and which minimum-necessary pharmacy or blood-readiness signals are pending. It is not an ERP and does not replace an EHR, bed-management master, laboratory system, pharmacy system, or clinical judgement.

## Problem

Emergency queues change after triage. New patients arrive, observations become stale, patients deteriorate, and surge pressure changes what needs review. FCFS is fair to arrival order but unsafe for acuity; pure acuity can starve lower groups; shortest-job-first can improve throughput while delaying severe cases; long-wait priority can ignore new emergencies. Hospitals need an auditable coordination view that keeps safety floors and uncertainty visible.

## Buyers and users

| Group | Value hypothesis |
|---|---|
| District/state hospital leadership | De-identified capacity, overdue reassessment, and surge evidence |
| Emergency clinical leadership | Reviewable prioritization rules and override traceability |
| Nurses and doctors | Bed-wise and patient-wise operational views with explanations |
| Pharmacy/blood-bank teams | Minimum-necessary readiness signals without full chart access |
| Quality and safety teams | Audit trail, failure behavior, and benchmark reports |

## Pilot offer

A 12-week, single-site, shadow-mode pilot:

| Weeks | Work |
|---|---|
| 1-2 | Workflow discovery, intended use, hazards, local parameters, integration plan |
| 3-5 | Identity, interface, environment, and dashboard localization |
| 6-8 | Silent shadow operation with synthetic and approved retrospective cases |
| 9-10 | Human-factors, load, downtime, and security exercises |
| 11-12 | Independent evaluation, clinician sign-off, and go/no-go recommendation |

No recommendation should affect live care during the shadow phase. Pre-agreed stop criteria include unsafe ranking behavior, stale-data blindness, excessive false alerts, identity failures, or inability to recover to manual workflow.

## Commercial model

1. Fixed-price discovery and shadow-pilot implementation.
2. Annual site subscription only after clinical, security, privacy, and procurement gates.
3. Optional managed support and multi-site analytics.
4. Hospital retains ownership/control of clinical data; contracts must prohibit secondary use without explicit authorization.

## Success measures

- zero synthetic critical misses in approved scenarios;
- high-risk time-to-review and overdue-reassessment rate;
- alert precision and acknowledgement time;
- override rate, reasons, and safety conflicts;
- ranking/API latency under normal and surge load;
- system availability and manual-fallback recovery time;
- clinician usability and trust scores;
- subgroup performance and missing-data behavior.

These are evaluation measures, not promised outcomes or savings.
