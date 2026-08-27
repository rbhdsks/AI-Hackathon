# Test matrix

| Area | Cases |
|---|---|
| Validation | Age limits, vital ranges, timezone awareness, blood-pressure consistency, timeline ordering, identifier format, duplicate symptoms |
| Safety rules | Every critical/emergent rule, multiple simultaneous hits, no-hit default, missing-measurement escalation |
| Feature extraction | Adult, pediatric, geriatric, zero history, ambiguous presentation, missing data, waiting, deterioration, future arrival |
| CDM | Empty set, one patient, equal patients, probability sum, deterministic results, context change, non-finite input, wrong shape, large finite values |
| Ranking | Empty queue, stable tie, duplicate ID, safety floor precedence, surge auto-detection, explicit mode, fallback, new critical patient during failure |
| Monitoring | Stable, critical, deterioration, stale data, overdue review, surge thresholds, future timestamps |
| Confidence | Complete, missing values, no history, ambiguity, stale observation, unavailable model, category boundaries |
| Repository | Add/get copies, duplicate intake, not found, vital update, invalid observation order, status filtering, duplicate scenario IDs |
| Overrides | Valid move, invalid patient, invalid position, required reason, critical downward safety conflict, persistent override |
| Audit | Genesis event, multiple events, order, valid chain, tampered payload, invalid limit, timezone requirement |
| Evaluation | Empty queue, labelled records, critical miss, under-triage, over-triage, explanations, alerts |
| Baseline policies | FCFS, acuity, SJF-like, waiting priority, acuity + waiting, PatientTriage.ai, empty workload |
| Scalability | 5/10 test queues, unique expansion IDs, invalid counts, invalid repetitions, timezone requirement |
| Hospital configuration | 18-bed zone sum, staffing/team consistency, invalid capacity, 12-hour shift calculation |
| Bed projection | Empty, 20-patient normal, 60-patient surge, stable IDs, zones, waiting-for-bed counts |
| Readiness coordination | Pharmacy and blood signals, acknowledgement persistence, reset, unknown task |
| Access control | All five roles, allowed reads/writes, denied patient/queue/audit/scenario paths, invalid role header |
| API | Lifespan, health, bootstrap, CRUD, infrastructure, RBAC, beds, readiness, baselines, surge, deterioration, fallback, override, audit verification, request validation |
| Dashboard/client | Proxy isolation, role header propagation, readiness routes, default nurse Streamlit render |
| End-to-end | Normal → deterioration → override → surge → failure report |

Software tests cannot prove that the illustrative rules, features, or ranking are clinically safe.
