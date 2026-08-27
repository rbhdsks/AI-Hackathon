.PHONY: setup test lint format check api dashboard demo reports clean

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e ".[dev]"

test:
	.venv/bin/python -m pytest

lint:
	.venv/bin/python -m ruff check .

format:
	.venv/bin/python -m ruff format .
	.venv/bin/python -m ruff check --fix .

check: lint test

api:
	.venv/bin/python -m uvicorn patient_triage.api.app:app --reload --port 8000

dashboard:
	.venv/bin/python -m streamlit run dashboard/streamlit_app.py

demo:
	.venv/bin/python -m patient_triage.simulations.run_demo --output demo/sample_run.json

reports:
	.venv/bin/python -m patient_triage.simulations.generate_reports --output reports

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage build dist *.egg-info
