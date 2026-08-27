# Implementation roadmap

## Phase A - hackathon package (complete in this repository)

- Branded role dashboards.
- Configurable district-hospital simulation.
- 18-bed projection and patient/bed navigation.
- Safety-constrained CDM queue.
- Normal, deterioration, failure, override, and 3x surge stories.
- Six baseline policies and scalability reports.
- Hash-chained audit, Docker, virtual environment, tests, PDF, deck, and video.

## Phase B - 12-week shadow pilot

| Week | Deliverable | Exit gate |
|---|---|---|
| 1 | Intended use, clinical owner, workflow map | Signed scope and non-ERP boundary |
| 2 | Hazard log and local configuration | Clinical-safety approval to build |
| 3-4 | OIDC/SSO, roles, test environment | Identity and authorization test |
| 5 | EHR/FHIR event adapter in non-production | Proven provenance/idempotency |
| 6 | Observability, backup, kill switch | Downtime exercise passed |
| 7-8 | Silent shadow run | No effect on live care |
| 9 | Human-factors and accessibility | Usability risks mitigated |
| 10 | Security and load testing | Critical findings closed |
| 11 | Subgroup and missing-data review | Independent evidence review |
| 12 | Go/no-go report | Hospital governance decision |

## Phase C - production consideration

Only after classification, clinical safety, privacy, security, procurement, integration, and shadow evidence gates. Production scope includes stateless APIs, managed transactional stores, hospital SSO, event ingestion, immutable centralized logs, site-level configuration versioning, recovery rehearsals, and continuous monitoring.

## Explicit exclusions

- autonomous diagnosis or treatment;
- billing and claims;
- pharmacy stock/dispensing;
- blood inventory/cross-match management;
- authoritative admission, discharge, transfer, or bed master;
- payroll, procurement, finance, or other ERP modules.
