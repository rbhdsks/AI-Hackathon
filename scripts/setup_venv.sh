#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest

printf '%s\n' "Setup complete."
printf '%s\n' "Activate with: source .venv/bin/activate"
