# Synthetic data dictionary

## Patient

| Field | Type | Validation | Model input |
|---|---|---|---|
| `patient_id` | String | 1–64 safe identifier characters | Tie-break only |
| `age_years` | Number | 0–130 | Yes, through age-aware features |
| `arrival_time` | Aware datetime | Must not be materially in the future | Yes, waiting feature |
| `symptoms` | List of enum values | 1–12, duplicates removed | Yes |
| `pain_score` | Integer or null | 0–10 | Yes |
| `observed_distress` | Boolean | Required default false | Yes, safety rules |
| `has_prior_record` | Boolean | Required default false | Yes, uncertainty only |
| `pregnancy` | Boolean or null | Optional | No in this prototype |
| `vitals` | VitalSigns | Required observation object | Yes |
| `previous_vitals` | VitalSigns or null | Cannot be newer than current | Yes, deterioration |
| `last_clinical_review_at` | Aware datetime or null | Cannot be before arrival | Monitoring only |
| `status` | Enum | waiting, in treatment, discharged | Queue inclusion |
| `expected_acuity` | Integer 1–5 or null | Synthetic label | No; evaluation only |
| `scenario_tags` | List of strings | Normalized and deduplicated | No; demo metadata only |

## VitalSigns

| Field | Unit | Allowed prototype range | Missing allowed |
|---|---|---:|---|
| `heart_rate_bpm` | beats/min | 0–300 | Yes |
| `respiratory_rate_bpm` | breaths/min | 0–100 | Yes |
| `systolic_bp_mm_hg` | mmHg | 30–300 | Yes |
| `diastolic_bp_mm_hg` | mmHg | 10–200 and below systolic | Yes |
| `oxygen_saturation_pct` | percent | 0–100 | Yes |
| `temperature_c` | °C | 25–45 | Yes |
| `consciousness` | enum | alert, voice, pain, unresponsive | Yes |
| `recorded_at` | aware datetime | Required | No |

Missing values are preserved. They lower confidence and may trigger conservative safety behavior; they are not silently replaced with normal values.

## Excluded identity data

The domain model intentionally has no name, address, phone number, email address, government identifier, insurance identifier, or free-text clinical note. This reduces demo risk but does not itself establish legal compliance.
