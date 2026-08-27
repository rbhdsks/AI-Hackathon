# Verification report

Verified on 25 August 2026 with Python 3.12.13 on Linux.

## Automated checks

```text
Ruff format check: passed
Ruff lint check: passed
pytest: 159 passed
Statement/branch coverage: 96.19%
DeprecationWarning policy: treated as errors; passed
pip check: no broken requirements
Wheel build: passed
Docker Compose YAML structural check: passed
Docker image build: not executed because no Docker engine is installed in the workspace
PowerPoint overflow test: passed
PDF visual render inspection: passed
```

The full edge-case matrix is documented in [TEST_MATRIX.md](TEST_MATRIX.md). It covers validation boundaries, missing measurements, pediatric and geriatric adjustments, context-sensitive CDM behavior, hard safety floors, deterioration, stale observations, surge mode, model failure, clinician overrides, hash-chain tampering, five-role authorization, 18-bed normal/surge projections, readiness acknowledgements, all six scheduling baselines, scalability input validation, API errors, empty queues, deterministic ties, and the packaged 20/60-patient fixtures.

## Runtime smoke tests

- FastAPI application startup and shutdown completed successfully.
- `/health`, `/v1/queue`, `/v1/beds`, `/v1/evaluation/baselines`, pharmacy readiness, and blood-bank readiness returned valid responses for their permitted roles.
- The normal endpoint loaded 20 patients and returned 20 ranked queue entries.
- The queue reported the CDM as ready.
- The default nurse Streamlit view rendered with 3 tabs and zero application exceptions.
- The scripted demo validated 20-patient normal, 60-patient surge, clinician override, deterioration, audit-chain, and model-fallback outcomes.
- Reproducible CSV/JSON baseline and scalability reports were generated.
- The branded PDF rendered to 10 inspected A4 pages and remained below 20 MB.
- The 13-slide pitch deck passed the presentation overflow test and visual review.
- The 81-second 1080p MP4 decoded as H.264/AAC and was sampled visually.

## Reproduce

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
PYTHONWARNINGS="error::DeprecationWarning" python -m pytest
python -m ruff format --check .
python -m ruff check .
python -m pip check
```

Passing software tests do not establish clinical safety, efficacy, or regulatory compliance. This project uses synthetic data and illustrative thresholds only.
