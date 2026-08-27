# Synthetic scenario files

These records are deterministic demonstration fixtures generated at the reference time `2026-08-25T12:00:00Z`.

- `patients_normal.json` contains 20 curated patients.
- `patients_surge.json` contains the same core cases plus 40 deterministic arrivals.

The records contain only synthetic identifiers. `expected_acuity` and `scenario_tags` are evaluation metadata and are never supplied to safety rules, feature extraction, urgency scoring, or the Context-Dependent Model.

These files and all included thresholds are for software demonstration only and must not be used for patient care.
