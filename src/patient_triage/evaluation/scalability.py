"""Repeatable local scalability benchmark for the ranking pipeline."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from time import perf_counter_ns

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from patient_triage.domain.patient import Patient
from patient_triage.services.ranking import RankingService


class ScalabilityPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    patient_count: int = Field(ge=1)
    repetitions: int = Field(ge=1)
    mean_latency_ms: float = Field(ge=0)
    p95_latency_ms: float = Field(ge=0)
    max_latency_ms: float = Field(ge=0)
    throughput_patients_per_second: float = Field(ge=0)


class ScalabilityReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_at: datetime
    benchmark_clock: datetime
    points: list[ScalabilityPoint]
    interpretation: str
    limitation: str


def expand_synthetic_patients(
    templates: list[Patient],
    patient_count: int,
) -> list[Patient]:
    if patient_count < 1:
        raise ValueError("patient_count must be at least one")
    if not templates:
        raise ValueError("at least one patient template is required")
    expanded: list[Patient] = []
    for index in range(patient_count):
        source = templates[index % len(templates)]
        cycle = index // len(templates)
        expanded.append(
            source.model_copy(
                update={
                    "patient_id": f"LOAD-{index + 1:04d}",
                    "arrival_time": source.arrival_time - timedelta(seconds=cycle),
                },
                deep=True,
            )
        )
    return expanded


def benchmark_scalability(
    templates: list[Patient],
    *,
    patient_counts: tuple[int, ...] = (20, 60, 180),
    repetitions: int = 12,
    now: datetime | None = None,
) -> ScalabilityReport:
    if repetitions < 1:
        raise ValueError("repetitions must be at least one")
    if not patient_counts or any(count < 1 for count in patient_counts):
        raise ValueError("patient_counts must contain positive integers")
    observed_at = now or datetime.now(UTC)
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("benchmark time must include a timezone")
    ranking = RankingService()
    points: list[ScalabilityPoint] = []
    for count in patient_counts:
        patients = expand_synthetic_patients(templates, count)
        ranking.rank(patients, now=observed_at)
        samples: list[float] = []
        for _ in range(repetitions):
            start = perf_counter_ns()
            ranking.rank(patients, now=observed_at)
            samples.append((perf_counter_ns() - start) / 1_000_000)
        mean_ms = float(np.mean(samples))
        points.append(
            ScalabilityPoint(
                patient_count=count,
                repetitions=repetitions,
                mean_latency_ms=round(mean_ms, 3),
                p95_latency_ms=round(float(np.percentile(samples, 95)), 3),
                max_latency_ms=round(max(samples), 3),
                throughput_patients_per_second=round(count / (mean_ms / 1000), 1)
                if mean_ms
                else 0.0,
            )
        )
    return ScalabilityReport(
        generated_at=datetime.now(UTC),
        benchmark_clock=observed_at,
        points=points,
        interpretation=(
            "This benchmark isolates in-process ranking latency at increasing queue "
            "sizes so capacity decisions can be based on measured, reproducible data."
        ),
        limitation=(
            "Local synthetic microbenchmark only; it excludes network, persistence, "
            "authentication, concurrent users, and production observability overhead."
        ),
    )
