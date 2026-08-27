#!/usr/bin/env bash
set -euo pipefail

.venv/bin/python -m uvicorn patient_triage.api.app:app --reload --port 8000
