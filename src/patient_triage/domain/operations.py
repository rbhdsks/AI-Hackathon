"""Operational bed-board and cross-department readiness models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from patient_triage.domain.enums import (
    BedStatus,
    CoordinationDomain,
    TaskStatus,
)
from patient_triage.domain.patient import PatientId, require_aware


class BedSlot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    bed_id: str = Field(pattern=r"^ED-\d{2,3}$")
    zone: str = Field(min_length=2, max_length=80)
    status: BedStatus
    patient_id: PatientId | None = None
    queue_position: int | None = Field(default=None, ge=1)
    acuity_label: str | None = None
    wait_minutes: float | None = Field(default=None, ge=0)
    state: str | None = None

    @model_validator(mode="after")
    def validate_occupancy(self) -> BedSlot:
        if self.status is BedStatus.EMPTY and self.patient_id is not None:
            raise ValueError("empty bed cannot contain a patient")
        if self.status is BedStatus.OCCUPIED and self.patient_id is None:
            raise ValueError("occupied bed requires a patient")
        return self


class WaitingForBed(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    patient_id: PatientId
    queue_position: int = Field(ge=1)
    acuity_label: str
    wait_minutes: float = Field(ge=0)
    state: str


class BedBoard(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_at: datetime
    profile_id: str
    total_beds: int = Field(ge=1)
    occupied_beds: int = Field(ge=0)
    empty_beds: int = Field(ge=0)
    waiting_for_bed: int = Field(ge=0)
    occupancy_percent: float = Field(ge=0, le=100)
    beds: list[BedSlot]
    waiting_patients: list[WaitingForBed]
    projection_notice: str


class CoordinationTask(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    task_id: str = Field(pattern=r"^[a-z_]+:[A-Za-z0-9_-]+$")
    domain: CoordinationDomain
    patient_id: PatientId
    priority: int = Field(ge=1, le=5)
    summary: str = Field(min_length=3, max_length=160)
    reason: str = Field(min_length=5, max_length=300)
    status: TaskStatus
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None

    @model_validator(mode="after")
    def validate_acknowledgement(self) -> CoordinationTask:
        if self.acknowledged_at is not None:
            require_aware(self.acknowledged_at, "acknowledged_at")
        if self.status is TaskStatus.ACKNOWLEDGED and not self.acknowledged_by:
            raise ValueError("acknowledged task requires an actor")
        return self


class TaskAcknowledgement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    actor_id: str = Field(min_length=2, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
