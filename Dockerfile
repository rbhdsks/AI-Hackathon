FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

COPY dashboard ./dashboard
COPY assets ./assets
COPY configs ./configs
COPY data ./data
COPY reports ./reports

EXPOSE 8000 8501

CMD ["python", "-m", "uvicorn", "patient_triage.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
