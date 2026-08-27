# Five-minute demo script

## Preparation

```bash
source .venv/bin/activate
python -m uvicorn patient_triage.api.app:app --port 8000
```

In a second terminal:

```bash
source .venv/bin/activate
python -m streamlit run dashboard/streamlit_app.py
```

## 0:00–0:40 — Positioning

Say:

> PatientTriage.ai is not diagnosing patients. It is a synthetic, clinician-controlled queue assistant. Safety rules protect red flags, while a Context-Dependent Model updates relative priority as the room changes.

Show the warning banner and queue summary.

## 0:40–1:30 — Normal queue

Load **20 patients**. Point out:

- critical safety-floor cases at the top;
- the ambiguous zero-history record;
- confidence and missing measurements; and
- base utility versus context effect.

Explain that CDM works inside the acuity constraint and cannot downgrade a critical rule.

## 1:30–2:20 — Deterioration

Select a stable patient and click **Simulate deterioration**. Show:

- new vital-sign observation;
- deterioration alert;
- changed acuity or position; and
- an explanation tied to the changed observation.

## 2:20–3:00 — Clinician authority

Move the ambiguous patient to position 5. Enter a clear reason. Open the audit tab and show the override event and valid hash chain.

Say:

> The assistant recommends; the clinician decides. The system records who changed the order and why.

## 3:00–3:40 — Surge

Load **3× surge**. Show 60 patients, surge mode, queue pressure, shorter prototype reassessment intervals, and overdue alerts.

## 3:40–4:20 — Failure

Enable **Simulate CDM failure**. Show:

- rule-only fallback;
- stale markers;
- manual-review actions; and
- critical patients still protected.

Explain that a new critical arrival is evaluated in the fallback rather than omitted by blindly replaying an old queue.

## 4:20–5:00 — Evidence and limits

Show the automated test result and `demo/sample_run.json`. End with:

> These results demonstrate software behavior on synthetic data, not clinical effectiveness. Real use would require local protocol approval, security, integration, and independent clinical validation.
