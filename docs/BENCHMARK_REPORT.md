# Queue-policy benchmark report

## Compared policies

| Policy | Represents | Why it is included |
|---|---|---|
| FIFO / FCFS | First arrival is served first | Simple baseline; exposes the risk of arrival order alone |
| Priority queue | Highest current five-level acuity first | Most important traditional safety comparison |
| SJF-like | Shortest illustrative service time first | Throughput versus fairness/safety trade-off |
| Waiting-time priority | Longest current wait first | Anti-starvation/fairness comparison |
| Acuity + waiting | Combined severity and elapsed wait | Stronger practical baseline |
| PatientTriage.ai | Safety floors, CDM context, confidence, and monitoring | Proposed approach |

## Simulation contract

- Four parallel treatment teams from the district profile.
- Non-preemptive scheduling.
- Illustrative service time by final acuity: 50, 40, 28, 16, and 9 minutes from critical to non-urgent.
- 120-minute evaluation horizon.
- Normal set: 20 synthetic patients.
- Surge set: 60 synthetic patients.

## Reproduced results

### Normal scenario

| Policy | Safety-weighted delay | Mean added wait | Completed by 120 min | Starvation count |
|---|---:|---:|---:|---:|
| FIFO / FCFS | 935.50 | 51.10 | 15 | 3 |
| Priority queue | 690.50 | 82.00 | 11 | 11 |
| SJF-like | 938.40 | 50.00 | 15 | 4 |
| Waiting-time priority | 935.50 | 51.10 | 15 | 3 |
| Acuity + waiting | 795.30 | 65.10 | 13 | 11 |
| PatientTriage.ai | 690.50 | 82.00 | 11 | 11 |

### 3x surge scenario

| Policy | Safety-weighted delay | Mean added wait | Completed by 120 min | Starvation count |
|---|---:|---:|---:|---:|
| FIFO / FCFS | 1951.77 | 180.50 | 17 | 60 |
| Priority queue | 1624.43 | 225.73 | 11 | 51 |
| SJF-like | 2006.40 | 161.60 | 22 | 49 |
| Waiting-time priority | 1951.77 | 180.50 | 17 | 60 |
| Acuity + waiting | 1846.30 | 196.07 | 16 | 60 |
| PatientTriage.ai | 1624.43 | 225.73 | 11 | 51 |

## Interpretation

The static snapshot does not prove that PatientTriage.ai is universally best. In these cases it ties the acuity-priority baseline on the safety-weighted metric because safety-first ordering dominates the initial queue. SJF-like completes more cases inside the horizon but gives worse critical-case delay. FCFS and waiting-priority improve some mean-wait measures while delaying newly arrived critical cases.

PatientTriage.ai's differentiator is not a fabricated win on every scalar metric. It adds capabilities the baselines do not model: safety floors, context within acuity groups, uncertainty, missing-data visibility, continuous reassessment, deterioration-driven re-ranking, explicit fallback, role permissions, and audited clinician override. A credible Phase 2 claim is therefore "safer and more governable dynamic coordination in the synthetic workflow," not "clinically superior."

## Reproduce

```bash
patient-triage-reports --output reports
```

The source data are `reports/baseline_benchmark.csv` and `.json`.
