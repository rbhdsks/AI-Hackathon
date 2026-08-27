"""Operational queue-policy baselines for the synthetic demonstration."""

from __future__ import annotations

import heapq
from enum import StrEnum

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from patient_triage.domain.enums import AcuityLevel
from patient_triage.domain.hospital import HospitalProfile
from patient_triage.domain.patient import Patient
from patient_triage.domain.queue import QueueEntry, QueueSnapshot


class BaselineStrategy(StrEnum):
    FCFS = "fcfs"
    ACUITY = "acuity_priority"
    SJF = "sjf_like"
    WAITING = "waiting_time_priority"
    ACUITY_WAIT = "acuity_plus_waiting"
    PATIENT_TRIAGE = "patienttriage_ai"


DESCRIPTIONS: dict[BaselineStrategy, str] = {
    BaselineStrategy.FCFS: "First arrival is served first.",
    BaselineStrategy.ACUITY: "Highest current five-level acuity is served first.",
    BaselineStrategy.SJF: "Shortest synthetic service-time estimate is served first.",
    BaselineStrategy.WAITING: "Longest current wait is served first.",
    BaselineStrategy.ACUITY_WAIT: "Acuity and elapsed waiting time are combined.",
    BaselineStrategy.PATIENT_TRIAGE: (
        "Safety floors followed by context-dependent ranking and monitoring."
    ),
}


class BaselineResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    strategy: BaselineStrategy
    display_name: str
    description: str
    mean_additional_wait_minutes: float = Field(ge=0)
    p95_additional_wait_minutes: float = Field(ge=0)
    mean_total_wait_minutes: float = Field(ge=0)
    critical_mean_additional_wait_minutes: float | None = Field(default=None, ge=0)
    high_risk_top_five_rate: float | None = Field(default=None, ge=0, le=1)
    starvation_count: int = Field(ge=0)
    completed_within_120_minutes: int = Field(ge=0)
    safety_weighted_delay: float = Field(ge=0)


class BaselineBenchmarkReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    patient_count: int = Field(ge=0)
    treatment_teams: int = Field(ge=1)
    horizon_minutes: int = Field(ge=1)
    results: list[BaselineResult]
    interpretation: str
    limitation: str


DISPLAY_NAMES = {
    BaselineStrategy.FCFS: "FIFO / FCFS",
    BaselineStrategy.ACUITY: "Priority queue",
    BaselineStrategy.SJF: "SJF-like",
    BaselineStrategy.WAITING: "Waiting-time priority",
    BaselineStrategy.ACUITY_WAIT: "Acuity + waiting",
    BaselineStrategy.PATIENT_TRIAGE: "PatientTriage.ai",
}


def _service_minutes(entry: QueueEntry) -> float:
    return {
        AcuityLevel.CRITICAL: 50.0,
        AcuityLevel.EMERGENT: 40.0,
        AcuityLevel.URGENT: 28.0,
        AcuityLevel.LESS_URGENT: 16.0,
        AcuityLevel.NON_URGENT: 9.0,
    }[entry.acuity]


def _orders(
    patients: list[Patient],
    snapshot: QueueSnapshot,
) -> dict[BaselineStrategy, list[QueueEntry]]:
    patient_by_id = {patient.patient_id: patient for patient in patients}
    entries = list(snapshot.entries)
    return {
        BaselineStrategy.FCFS: sorted(
            entries,
            key=lambda entry: (
                patient_by_id[entry.patient_id].arrival_time,
                entry.patient_id,
            ),
        ),
        BaselineStrategy.ACUITY: sorted(
            entries,
            key=lambda entry: (
                int(entry.acuity),
                patient_by_id[entry.patient_id].arrival_time,
                entry.patient_id,
            ),
        ),
        BaselineStrategy.SJF: sorted(
            entries,
            key=lambda entry: (
                _service_minutes(entry),
                patient_by_id[entry.patient_id].arrival_time,
                entry.patient_id,
            ),
        ),
        BaselineStrategy.WAITING: sorted(
            entries,
            key=lambda entry: (-entry.wait_minutes, entry.patient_id),
        ),
        BaselineStrategy.ACUITY_WAIT: sorted(
            entries,
            key=lambda entry: (
                -((6 - int(entry.acuity)) * 30 + entry.wait_minutes),
                entry.patient_id,
            ),
        ),
        BaselineStrategy.PATIENT_TRIAGE: sorted(
            entries,
            key=lambda entry: entry.position,
        ),
    }


def _simulate(
    strategy: BaselineStrategy,
    ordered: list[QueueEntry],
    treatment_teams: int,
    horizon_minutes: int,
) -> BaselineResult:
    team_available = [0.0] * treatment_teams
    heapq.heapify(team_available)
    starts: list[float] = []
    completions: list[float] = []
    total_waits: list[float] = []
    critical_starts: list[float] = []
    weighted_delays: list[float] = []
    for entry in ordered:
        start = heapq.heappop(team_available)
        completion = start + _service_minutes(entry)
        heapq.heappush(team_available, completion)
        starts.append(start)
        completions.append(completion)
        total_waits.append(entry.wait_minutes + start)
        weighted_delays.append(start * float((6 - int(entry.acuity)) ** 2))
        if entry.acuity is AcuityLevel.CRITICAL:
            critical_starts.append(start)
    high_risk_ids = {
        entry.patient_id
        for entry in ordered
        if int(entry.acuity) <= int(AcuityLevel.EMERGENT)
    }
    high_risk_in_top_five = sum(
        entry.patient_id in high_risk_ids for entry in ordered[:5]
    )
    top_five_rate = (
        high_risk_in_top_five / len(high_risk_ids) if high_risk_ids else None
    )
    return BaselineResult(
        strategy=strategy,
        display_name=DISPLAY_NAMES[strategy],
        description=DESCRIPTIONS[strategy],
        mean_additional_wait_minutes=round(float(np.mean(starts)), 2)
        if starts
        else 0.0,
        p95_additional_wait_minutes=round(float(np.percentile(starts, 95)), 2)
        if starts
        else 0.0,
        mean_total_wait_minutes=round(float(np.mean(total_waits)), 2)
        if total_waits
        else 0.0,
        critical_mean_additional_wait_minutes=(
            round(float(np.mean(critical_starts)), 2) if critical_starts else None
        ),
        high_risk_top_five_rate=(
            round(top_five_rate, 4) if top_five_rate is not None else None
        ),
        starvation_count=sum(wait > 120 for wait in total_waits),
        completed_within_120_minutes=sum(
            completion <= horizon_minutes for completion in completions
        ),
        safety_weighted_delay=round(float(np.mean(weighted_delays)), 2)
        if weighted_delays
        else 0.0,
    )


def compare_baselines(
    patients: list[Patient],
    snapshot: QueueSnapshot,
    profile: HospitalProfile,
    *,
    horizon_minutes: int = 120,
) -> BaselineBenchmarkReport:
    orders = _orders(patients, snapshot)
    results = [
        _simulate(
            strategy,
            orders[strategy],
            profile.treatment_teams,
            horizon_minutes,
        )
        for strategy in BaselineStrategy
    ]
    return BaselineBenchmarkReport(
        patient_count=len(snapshot.entries),
        treatment_teams=profile.treatment_teams,
        horizon_minutes=horizon_minutes,
        results=results,
        interpretation=(
            "No single queue policy should be expected to win every metric: SJF-like "
            "policies favour throughput, waiting-time policies favour age of wait, and "
            "safety-constrained policies favour urgent cases."
        ),
        limitation=(
            "Synthetic non-preemptive queue simulation with illustrative service times; "
            "it does not establish clinical effectiveness or hospital savings."
        ),
    )
