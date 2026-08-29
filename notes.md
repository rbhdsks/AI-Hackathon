# PatientTriage.ai — Product Evidence Map

Compiled by direct inspection of the codebase (`src/`, `dashboard/`, `configs/`, `data/`,
`reports/`, `docs/`, `tests/`) on 2026-08-29. Every number below was re-verified by running
the test suite / reading the checked-in report files, not copied from earlier chat claims.
Tags: `[OBSERVED]` verified by running code/tests · `[DOCUMENTED]` stated in repo docs/config ·
`[CONCEPT]` planned, not built · `[UNKNOWN]` not verifiable from this repo.

---

## A. WHAT I HAVE

### Core triage/queue logic
| What it is | What it does | Evidence/status |
|---|---|---|
| Safety rules (`rules/safety_rules.py`) | Hard, fail-safe escalation floors evaluated *before* any ranking; e.g. pediatric respiratory distress or high-risk symptom + missing vitals force escalation | `[OBSERVED]` 100% test coverage on this file |
| Acuity thresholds (`rules/thresholds.py`) | Per-acuity max safe wait (0/10/30/60/120 min), halved under surge; separate vitals-staleness threshold (30 min normal / 15 min surge) | `[OBSERVED]` |
| Transparent urgency model (`models/urgency.py`) | Fixed, inspectable linear model (`intercept -0.2`, 7 hand-set coefficients) mapping features → acuity band; thresholds explicitly tuned to over-triage under uncertainty (code comment: "false-negative cost is treated as higher than the operational cost of an unnecessary review") | `[OBSERVED]` |
| Feature-conditioned CDM (`models/cdm.py`) | `U_i(S) = βᵀxᵢ + mean_{j≠i}(xᵢᵀ W xⱼ)` — utility depends on the *other* patients currently waiting (context term), not just the patient alone | `[OBSERVED]`; safety rules explicitly outside this model ("applied as hard ordering floors") |
| 7 model features (`models/features.py`) | `physiology_risk, symptom_risk, pain, waiting, deterioration, uncertainty, vulnerability` | `[OBSERVED]` exact `FEATURE_NAMES` tuple |
| Confidence scoring (`models/confidence.py`) | 1.0 minus deductions for missing vitals, no prior record, ambiguous symptom, missing pain score, stale vitals, model unavailable → High/Medium/Low | `[OBSERVED]`; explicitly a data-quality heuristic, not a calibrated outcome probability (matches stated constraint) |
| Waiting-room monitoring (`services/monitoring.py`) | Computes `QueueState` per patient each snapshot: `stable / reassessment_due / deteriorating / critical_escalation / stale_information / manual_review`; deterioration = O₂ drop ≥3, SBP drop ≥20, HR rise ≥25, RR rise ≥8, or risk-score jump ≥0.2 | `[OBSERVED]` 100% coverage |
| Ranking service (`services/ranking.py`) | Runs safety floor → CDM ordering, remembers last-good positions for hysteresis, applies active overrides on top | `[OBSERVED]` 100% coverage |

### Beds, coordination, audit
| What it is | What it does | Evidence/status |
|---|---|---|
| 18-bed ED projection (`configs/district_hospital.json`) | 3 Resuscitation + 9 Acute care + 6 Observation = 18 (schema-enforced: zone counts must sum to `ed_beds`) | `[DOCUMENTED]`+`[OBSERVED]` (validated by Pydantic model) |
| Bed board (`services/bed_board.py`) | Projects the ranked queue onto beds by stable patient-ID order (not raw queue position) — a read model, not a bed-master system | `[OBSERVED]` 100% coverage |
| Clinician override (`services/overrides.py`) | Moves a patient to a target position; requires a reason (≥10 chars, enforced by `OverrideRequest` schema); flags a warning if a critical patient is moved *down* | `[OBSERVED]` |
| Tamper-evident audit chain (`storage/sqlite_audit.py`) | SQLite-backed hash chain (`previous_hash` → `event_hash`), `verify_chain()` walks the whole chain | `[OBSERVED]` 100% coverage; live `/v1/audit/verify` returns `valid: true` |
| Pharmacy/blood-bank coordination (`services/coordination.py`) | Minimum-necessary readiness tasks; blood-bank task triggers only on `severe_bleeding` symptom, shock signal (low SBP), or critical trauma tag | `[OBSERVED]` |
| RBAC (`configs/rbac.json`, `services/access_control.py`) | Server-enforced permission matrix by `X-Demo-Role` header; `service.access.require(role, Permission.X)` gate on every endpoint | `[OBSERVED]` live-tested this session: nurse → 403 on discharge, doctor → 403 on `/v1/evaluation/baselines` |

### Evaluation / benchmarking
| What it is | What it does | Evidence/status |
|---|---|---|
| 6-policy baseline comparison (`evaluation/baselines.py`) | FCFS, Acuity priority, SJF-like, Waiting-time priority, Acuity+waiting, **PatientTriage.ai** — same metrics computed for all 6 | `[OBSERVED]` enum has exactly 6 `BaselineStrategy` members |
| Scalability benchmark (`evaluation/scalability.py`) | In-process ranking-only microbenchmark at N=20/60/180, 12 repetitions, `perf_counter_ns`; explicitly excludes network/persistence/auth/concurrency | `[OBSERVED]` code + re-ran; see §G for numbers |
| Generated report artifacts (`reports/*.json`, `*.csv`) | Pre-computed, checked-in `baseline_benchmark.json` and `scalability_benchmark.json` | `[OBSERVED]` — read directly, not regenerated for this map |

### Tests & scenarios
| What it is | What it does | Evidence/status |
|---|---|---|
| Test suite | **159 tests**, **96.19% overall coverage** (`pytest --cov`, run live this session) | `[OBSERVED]` — re-ran, exact match |
| Normal scenario (`data/synthetic/patients_normal.json`) | **20 patients**: 4 critical-tagged, 3 respiratory, 2 chest pain, 2 pediatric, 3 geriatric, 3 zero-history, plus ambiguous/missing-vitals/deteriorating/unsafe-wait cases | `[OBSERVED]` — parsed the file directly |
| Surge scenario (`patients_surge.json`) | **60 patients** = same core cases + 40 deterministic surge arrivals (`scenario_tags: surge_generated: 40`) — confirms "3× normal" | `[OBSERVED]` |

### Existing collateral (not code, but already produced)
| What it is | Evidence/status |
|---|---|
| `output/pdf/PatientTriage_AI_Technical_and_Business_Report.pdf` | `[OBSERVED]` file exists (1.1 MB) |
| `output/presentation/PatientTriage_AI_Hackathon_Pitch.pptx` | `[OBSERVED]` file exists (1.5 MB) |
| `output/video/PatientTriage_AI_Prototype_Walkthrough.mp4` + README | `[OBSERVED]`; README states it covers "problem, non-ERP boundary, district profile, role views, 18-bed board, CDM safety architecture, dynamic scenario, baseline evidence, scalability, governance, costs, next decision" |

---

## B. SCREEN MAP

| Screen | User | Purpose | Key info shown | Key actions | Important behavior |
|---|---|---|---|---|---|
| Attention/Queue tab | Nurse | Spot who needs attention now | Attention-Required cards (deteriorating/overdue/low-confidence), live queue cards (position, acuity, confidence, wait, state, movement) | none (read + expand) | Movement indicator (`↑ Moved from #N`) tracked client-side vs. last snapshot |
| Bed-wise view | Nurse, Doctor | Spatial capacity view | 18-bed Plotly grid, per-bed zone/status/acuity/wait/monitoring state/recommended action | Select bed; **Simulate deterioration** (nurse+doctor); **Discharge patient** (doctor only) | Discharging frees the bed *and* the projection auto-reassigns the next waiting patient into an open slot on next fetch (verified live: 18/18 occupied before and after, waiting count 2→1) |
| Patient-wise view | Nurse, Doctor | Deep dive on one patient | Acuity/confidence/state badges, "prioritized because" reasons, missing info, recommended action | Simulate deterioration; Discharge (doctor only) | — |
| Override tab | Doctor only | Override the AI-recommended position | Current AI recommendation (position, acuity, top reasons) | Accept / Override (form: target position, clinician ID, reason ≥10 chars) | On submit, pulls the real just-written audit event (`client.audit(limit=1)`) and shows it persistently |
| Readiness (Pharmacy/Blood bank sub-tabs) | Doctor (read), Pharmacy, Blood bank | Coordination without full record access | Priority, patient ref, summary, reason, ack status | Acknowledge | Pharmacy/Blood bank standalone dashboards show *only* this — no patient list, no queue |
| Audit tab | Doctor, Administration | Accountability trail | Hash-chain validity, Time/Action/Actor/Patient table + raw-hash expander | none | `verify_chain()` walks the full chain live |
| Infrastructure tab | Administration | Capacity/staffing assumptions | Hospital level, catchment, bed counts, shift staffing table | none | — |
| Capacity tab | Administration | Occupancy view (read-only) | Bed board (no discharge/deteriorate buttons) + occupancy gauge | none | `allow_deterioration=False`, `allow_discharge` unset → both hidden |
| Policy evaluation tab | Administration | Evidence, not marketing | Bar chart + table of the 6-policy comparison, interpretation/limitation text | none | Data == the checked-in `baseline_benchmark.json` |
| Scenario control (sidebar) | Administration | Change synthetic load | — | Load "20 patients" (normal) / "3× surge" (60) | Sets `scenario_mode` session flag driving the SURGE MODE banner |

## C. WORKFLOW MAP

```
Synthetic patient (data/synthetic/*.json)
  → Feature extraction (7 features: physiology/symptom/pain/waiting/deterioration/uncertainty/vulnerability)
  → Safety rules (hard floor) ──┬── floor binds → AcuityLevel fixed, CDM cannot rank below it
                                 └── floor doesn't bind → falls through
  → Transparent urgency model → AcuityLevel (fallback path if CDM unavailable)
  → CDM (context-dependent) → utility U_i(S) using *other* waiting patients → position within acuity band
  → Confidence assessment (independent of ranking) → High/Medium/Low + missing-info list
  → Monitoring assessment (independent) → QueueState (stable/reassessment_due/deteriorating/critical_escalation/stale_information/manual_review)
  → QueueSnapshot (position, state, confidence, reasons, recommended_action)
  → [Nurse/Doctor view] → optional clinician Override (reason required) → re-inserted, `is_overridden=True`
  → Every mutation (override, deteriorate, discharge, acknowledge, ranking pass) → AuditEvent appended → hash chain
  → Bed board / Coordination tasks / Baseline evaluation all *read* from the same QueueSnapshot (no parallel state)
```

Branch not covered above: `simulate_model_failure=True` → CDM step skipped, `model_status != "ready"`,
dashboard shows the LIMITED MODE banner; safety rules + urgency model still run.

## D. ROLE MAP

Verified against `docs/RBAC_AND_DASHBOARDS.md` permission matrix + live 403 tests this session
(not assumed).

| Role | Screen/Dashboard | Sees | Does | Influences |
|---|---|---|---|---|
| Nurse | Attention/Queue, Bed-wise, Patient-wise | Full queue, full patient detail, beds | Simulate deterioration | Queue re-ranks after deterioration; **no** override/audit/pharmacy/blood/discharge access |
| Doctor | Queue, Patient, Bed map, Override, Readiness, Audit | Everything nurse sees + audit trail + pharmacy/blood readiness (read-only) | Deteriorate, **discharge**, **override** (reason required), acknowledge readiness (implicitly, if used) | Queue order (override), bed occupancy (discharge), audit log (every action) |
| Pharmacy | Single readiness view | Only medication-readiness signals for current queue | Acknowledge | Own task status only; no patient/queue visibility |
| Blood bank | Single readiness view | Only transfusion-readiness signals (severe bleeding/shock/trauma triggers) | Acknowledge | Own task status only |
| Administration | Infrastructure, Capacity, Policy evaluation, Audit + scenario control | De-identified capacity/staffing, occupancy, 6-policy comparison, audit trail | Load normal/surge scenario | Which synthetic dataset the whole system runs on; **no** clinical queue/patient access |

## E. "LIVING QUEUE" EVIDENCE

- **What the score represents:** two scores exist — (1) the *urgency score* (`βᵀx`, fixed
  linear model) that sets the **acuity band / safety floor**, and (2) the *CDM utility*
  `U_i(S) = βᵀxᵢ + mean_{j≠i}(xᵢᵀWxⱼ)` that ranks a patient **within** that band.
- **What determines queue order:** safety floor first (hard, cannot be beaten by context),
  then CDM utility within the floor, then any active clinician override.
- **What makes the queue move:** the CDM's context term depends on *every other patient
  currently waiting* (`mean_{j≠i}`) — a new arrival or a departure changes everyone's utility,
  even patients whose own features haven't changed. This is the literal mechanism behind "the
  score does not move, the queue does": a patient's own `βᵀxᵢ` term is stable; the context term
  moves with the room.
- **How patient changes affect it:** `simulate_deterioration` mutates vitals →
  `physiology_risk`/`deterioration` features change → re-ranked on next `rank_queue()` call;
  `monitoring.py` independently flags `deteriorating`/`critical_escalation` state.
- **How waiting time is handled:** `waiting` is one of the 7 CDM features (feeds ranking);
  separately, `max_wait_minutes(acuity, mode)` (0/10/30/60/120 min, halved in surge) drives the
  independent `reassessment_due` monitoring state — two different mechanisms, not one.
- **How overrides work:** doctor-only, mandatory reason (≥10 chars, schema-enforced),
  re-inserts the patient at the target position, flags `is_overridden=True`, warns if a critical
  patient is moved down, and appends an audit event.
- **What is audited:** `queue_ranked`, `patient_status_changed` (discharge), overrides,
  coordination acknowledgements — every one hash-chained.

**Verdict: Implemented** (not conceptual) — the mechanism is code, tested at 96%+ coverage, and
independently confirmed live via API calls this session (discharge → bed reassignment; override
→ real audit event retrieved and displayed).

## F. SAFETY & CLINICAL GOVERNANCE

| Mechanism | Evidence |
|---|---|
| Uncertainty | `[OBSERVED]` `confidence.py` — visible High/Medium/Low + itemized reasons; missing-info surfaced verbatim in queue entries and patient detail |
| Alerts | `[OBSERVED]` `monitoring.py` alert strings ("critical safety floor: immediate clinical review", "recorded vital signs indicate deterioration", "latest vital signs are stale", "reassessment threshold has been reached") |
| Escalation | `[OBSERVED]` `safety_rules.py` hard floors evaluated before ranking; urgency-model thresholds explicitly biased toward escalation (code comment) |
| Override | `[OBSERVED]` doctor-only, mandatory reason, warned if it demotes a critical patient, audited |
| Human oversight | `[OBSERVED]` clinician remains the decision-maker for override/discharge/disposition; CDM cannot downgrade a safety-floor patient (architectural separation in `cdm.py` docstring) |
| Audit | `[OBSERVED]` SQLite hash chain, `verify_chain()`, live-tested `valid: true` |
| Explainability | `[OBSERVED]` `reasons` list per queue entry ("prioritized because"), `recommended_action` string, `missing_information` list — all surfaced in the UI, not just the API |
| Safety controls (fail-safe) | `[OBSERVED]` `simulate_model_failure` path: CDM skipped, rule-only fallback stays active, `model_status`/`warnings` surfaced, dashboard shows a LIMITED MODE banner |

## G. EVIDENCE / NUMBERS

| Item | Found? | What it proves | Limitation |
|---|---|---|---|
| 20 synthetic patients (normal) | ✅ `[OBSERVED]` exact count 20 | A curated, tagged demonstration dataset exists | Synthetic; `expected_acuity`/`scenario_tags` are eval-only metadata, never fed to the model |
| 18-bed ED | ✅ `[OBSERVED]` 3+9+6=18, schema-validated | Bed capacity assumption is explicit and internally consistent | Illustrative hospital profile, not a real facility |
| 5 role dashboards | ✅ `[OBSERVED]` nurse/doctor/pharmacy/blood_bank/administration, each with distinct enforced permissions | RBAC is real, not cosmetic (403s confirmed live) | Single Streamlit app with a role switcher, not 5 separate deployed apps |
| Normal vs. 3× surge | ✅ `[OBSERVED]` 20 → 60 patients, 40 tagged `surge_generated` | Surge behavior is testable, not asserted | Deterministic/scripted surge, not a live arrival-rate model |
| Clinician override + audit | ✅ `[OBSERVED]` live-tested this session: override recorded, real audit event retrieved | End-to-end accountability loop works | Single demo doctor identity (`demo_doctor_01`), no real clinician auth |
| 159 tests / 96.19% coverage | ✅ `[OBSERVED]` re-ran `pytest --cov` live, exact match | Software-quality evidence is current, not stale | Coverage ≠ clinical correctness; two files (`generate_reports.py` 0%, `run_demo.py` 72%) drag the total down from higher |
| 6 queue-policy baselines | ✅ `[OBSERVED]` exactly 6 `BaselineStrategy` members incl. PatientTriage.ai | Comparative evaluation exists and is reproducible | **On the checked-in normal/surge report, PatientTriage.ai's safety-weighted delay and starvation count are numerically *identical* to plain "Acuity priority"** (690.5/11 normal, 1624.43/51 surge) — the CDM's context-dependent reordering does not change this particular aggregate metric in this seeded scenario. Do not claim PatientTriage.ai "outperforms" acuity-priority on this metric without re-checking; its differentiation shows up in confidence/uncertainty visibility and dynamic reordering, not this number. |
| Safety-weighted delay | ✅ `[OBSERVED]` formula: `additional_wait × (6 − acuity_level)²`, "lower is safer" | A defined, code-level metric, not a marketing term | Only as credible as the synthetic scenario it's computed on |
| 20/60/180 scalability | ✅ `[OBSERVED]` re-read checked-in `reports/scalability_benchmark.json`: 20p → 0.711 ms mean / 1.036 ms P95; 60p → 1.580 / 1.803 ms; 180p → 4.745 / 5.394 ms (12 reps each) | Ranking-only latency scales sub-linearly and stays sub-6ms even at 10× normal load | Explicitly excludes network, persistence, auth, concurrency, and production observability (stated in the report's own `limitation` field) — do not present as an API/system SLA |

## H. PROPOSAL MAPPING

| Proposal section | Relevant product evidence | Relevant screen/evidence | Missing evidence |
|---|---|---|---|
| ED Challenge → Operational Gap | Static-triage-vs-dynamic-reality is the design premise behind the safety-floor + CDM split | — (conceptual framing, not a screen) | No external ED industry statistics in-repo — cite externally or omit |
| Introducing PatientTriage.ai | Scope statement already exists (`docs/RBAC_AND_DASHBOARDS.md` "Explicit non-ERP boundary") | — | — |
| The Living Queue | §E above, in full | Queue tab (movement indicator), Override tab (recommendation vs. decision) | A literal before/after screenshot of a queue reordering after a new arrival isn't captured yet — would need a live demo run |
| Safety/Uncertainty/Governance | §F above, in full | Attention-Required panel, Patient detail (confidence + missing info), LIMITED MODE banner | — |
| Product & Workflow Design | §B (Screen Map), §D (Role Map) | All 5 dashboards | — |
| Target Users/Customers/Stakeholders | Role permission matrix (`docs/RBAC_AND_DASHBOARDS.md`) distinguishes user vs. buyer implicitly (Administration = buyer-adjacent role) | — | No named persona research — this is a design inference, not user research; must be labeled `[PROPOSED]` |
| Adoption & Deployment | Shadow-mode-compatible design (read-heavy roles for pharmacy/blood bank) | — | No adoption plan exists in-repo — fully `[PROPOSED]`/to-write |
| Value Proposition | Role-scoped minimum-necessary access is itself a value point (pharmacy/blood-bank never see full record) | Coordination screens | No competitor/alternative comparison in-repo — must be authored fresh |
| Impact/Measurement | §G numbers are the *inputs*; no real-world outcome data exists | `reports/baseline_benchmark.json` | All outcome claims are `[TO VALIDATE]` — nothing here is real-world evidence |
| Business Model | `configs/cost_assumptions.json` (§G-adjacent, see below) | — | No pricing/licensing logic in-repo — fully `[PROPOSED]` |
| Technical Scalability | §G scalability numbers | `evaluation/scalability.py` + report | — |
| Techno-Economic Analysis | `[DOCUMENTED]` `configs/cost_assumptions.json`: shadow pilot $180–650/mo, production HA $900–2,800/mo, 10-hospital regional $4,000–15,000/mo; pilot delivery ₹28–62 lakh across 7 workstreams (sums verified: 5+3+8+4+4+2+2=28 low, 12+6+16+10+8+5+5=62 high); explicit exclusions listed (taxes, devices, EHR interface fees, migration, legal, 24×7 staffing) | `configs/cost_assumptions.json` | Currency conversion uses a fixed USD→INR=96.0 rate as of 2026-08-25 — flag as needing refresh before real use |
| SWOT | Synthesizable from §A–§G, no new evidence needed | — | — |
| Current Prototype/Evidence | §A, §G in full | Test run output, report JSONs | — |
| Implementation Roadmap | Phase-0-is-real (this prototype); phases 1–3 are `[PROPOSED]` | — | No roadmap exists in-repo |
| Risks/Mitigation | Fail-safe fallback (§F) is a real mitigation; RBAC is a real mitigation | LIMITED MODE banner | Risk register itself doesn't exist in-repo — must be authored |
| Governance/Data Protection | `docs/REGULATORY_MAPPING.md` (US/UK/EU mapping), audit chain, RBAC | Audit tab | Regulatory mapping is planning-only, explicitly not a compliance determination |
| Conclusion | — | — | — |

## I. SCREENSHOT OPPORTUNITIES

| Screen/scenario | Best proposal use | What it visually proves |
|---|---|---|
| Nurse Attention/Queue tab, normal scenario | §The Living Queue / §Product & Workflow Design | Exceptions surfaced first, not a raw dataframe — the "what needs attention now" hierarchy |
| Doctor Override tab, mid-flow (recommendation box + form) | §The Living Queue / §Safety & Governance | Human-in-the-loop with a mandatory reason, AI recommendation shown before override |
| Doctor Override tab, post-submit (OVERRIDE RECORDED box with real audit ref) | §Governance/Audit | End-to-end accountability, not just a claim |
| 18-bed board, occupied + one bed selected showing monitoring state | §Product & Workflow Design | Bed-level operational projection, not a generic dashboard |
| Bed board before/after a discharge (occupancy count unchanged, waiting count down) | §The Living Queue | The queue moving in response to capacity change, live |
| Administration Policy Evaluation tab (bar chart + table) | §Technical Scalability / §Impact Measurement | The 6-policy comparison is a real, computed artifact |
| Administration scenario control → SURGE MODE ACTIVE banner | §Adoption / §Risk | Explicit "safety floors remain unchanged during surge" statement, visually |
| Pharmacy or Blood bank standalone view (minimal) | §Value Proposition (minimum-necessary access) | Role-scoped access is visibly enforced, not just described |
| LIMITED MODE banner (CDM-failure toggle on) | §Safety & Governance / §Risk | Fail-safe behavior is demonstrable, not theoretical |

## J. IMPORTANT LINKS

| Title | URL | Why useful |
|---|---|---|
| US HHS HIPAA Security Rule | https://www.hhs.gov/hipaa/for-professionals/security/laws-regulations/index.html | Primary regulatory anchor already chosen for this project |
| US FDA Clinical Decision Support Software guidance | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software | Directly relevant — this is a CDS-adjacent tool |
| UK MHRA software/AI as a medical device | https://www.gov.uk/government/publications/software-and-artificial-intelligence-ai-as-a-medical-device/software-and-artificial-intelligence-ai-as-a-medical-device | Portability-path citation for Appendix D |
| UK ICO special-category data guidance | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-is-special-category-data/ | Portability-path citation |
| EU MDCG software qualification/classification | https://health.ec.europa.eu/latest-updates/update-mdcg-2019-11-rev1-qualification-and-classification-software-regulation-eu-2017745-and-2025-06-17_en | Portability-path citation |
| EU AI Act framework | https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai | Portability-path citation |

*Not links, but existing local collateral worth reusing:* `output/pdf/PatientTriage_AI_Technical_and_Business_Report.pdf`,
`output/presentation/PatientTriage_AI_Hackathon_Pitch.pptx`, `output/video/PatientTriage_AI_Prototype_Walkthrough.mp4`
— all already produced; check them for content/framing before writing new material, to avoid contradicting them.

---

## FINAL OUTPUT

**WHAT I HAVE:** A working, tested (159 tests, 96.19% coverage) prototype with a real
two-tier ranking architecture (hard safety floor + context-dependent CDM), five permission-
enforced role dashboards, a tamper-evident audit chain with live verification, a functioning
clinician-override loop, a real fail-safe/limited-mode path, a reproducible 6-policy baseline
comparison, and a reproducible scalability benchmark (sub-6ms mean latency at 180 synthetic
patients) — all independently re-verified this session, not taken on faith.

**WHAT I DON'T HAVE:** Any real-world/clinical outcome data; any named user research or
persona validation; a written adoption plan, pricing/business model, or risk register (these
exist only as this evidence map's mapping, not as artifacts); a literal before/after
"queue reordering" screenshot; external ED industry statistics with citations; a refreshed
USD→INR rate (fixed at 96.0 as of 2026-08-25).

**WHAT I SHOULD NOT CLAIM YET:** That PatientTriage.ai reduces mortality, wait time, or cost
in reality; that it is clinically validated, regulator-approved, or compliant with HIPAA/GDPR/
MDR; that its confidence score is a calibrated risk probability; that it "outperforms"
acuity-priority ordering on the safety-weighted-delay/starvation metrics specifically (they
tie exactly in the current checked-in scenario data — differentiate on uncertainty visibility
and dynamic context-sensitivity instead); that the 20/60/180 scalability numbers represent
end-to-end system latency (they are ranking-only, in-process, no network/auth/concurrency).
