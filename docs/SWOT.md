# SWOT analysis

| Strengths | Weaknesses |
|---|---|
| Safety floors cannot be silently downgraded by CDM | Illustrative coefficients and thresholds are not clinically validated |
| Dynamic queue, deterioration, uncertainty, and waiting-time monitoring | In-memory patient store and SQLite audit are prototype adapters |
| Clinician override and tamper-evident event chain | Synthetic labels cannot establish real-world efficacy or fairness |
| Bed-wise and patient-wise role dashboards | Demo header is not real authentication |
| Transparent failure fallback and reproducible tests | No live EHR/device integration or calibrated outcome model |

| Opportunities | Threats |
|---|---|
| Shadow-mode pilots in district hospitals with constrained ED visibility | Regulatory classification or intended-use changes can expand obligations |
| Interoperable adapter to FHIR/EHR events without replacing hospital systems | Alert fatigue or automation bias can harm workflow |
| Multi-site learning from de-identified operational metrics | Poor data quality, delayed observations, or identity mismatch |
| Clinical-safety evidence differentiates it from opaque queue scores | Cyberattack, downtime, or vendor lock-in |
| Surge planning and staffing simulation for administrators | Liability and trust damage from overstated claims |

## Strategic response

Keep the product narrow, run in shadow mode first, publish limitations, require clinician control, instrument every failure path, localize parameters through governance, and treat integration/security/clinical validation as product work rather than post-hackathon polish.
