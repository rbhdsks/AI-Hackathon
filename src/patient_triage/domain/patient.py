"""Validated patient and vital-sign models for synthetic data only."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from patient_triage.domain.enums import (
    AcuityLevel,
    AgeGroup,
    Consciousness,
    PatientStatus,
    Symptom,
)

PatientId = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
    ),
]


def require_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone")
    return value


class VitalSigns(BaseModel):
    """A single vital-sign observation; individual measurements may be missing."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    heart_rate_bpm: int | None = Field(default=None, ge=0, le=300)
    respiratory_rate_bpm: int | None = Field(default=None, ge=0, le=100)
    systolic_bp_mm_hg: int | None = Field(default=None, ge=30, le=300)
    diastolic_bp_mm_hg: int | None = Field(default=None, ge=10, le=200)
    oxygen_saturation_pct: float | None = Field(default=None, ge=0, le=100)
    temperature_c: float | None = Field(default=None, ge=25, le=45)
    consciousness: Consciousness | None = None
    recorded_at: datetime

    @field_validator("recorded_at")
    @classmethod
    def validate_recorded_at(cls, value: datetime) -> datetime:
        return require_aware(value, "recorded_at")

    @model_validator(mode="after")
    def validate_blood_pressure(self) -> VitalSigns:
        if (
            self.systolic_bp_mm_hg is not None
            and self.diastolic_bp_mm_hg is not None
            and self.diastolic_bp_mm_hg >= self.systolic_bp_mm_hg
        ):
            raise ValueError("diastolic pressure must be below systolic pressure")
        return self

    def missing_measurements(self) -> list[str]:
        names = (
            "heart_rate_bpm",
            "respiratory_rate_bpm",
            "systolic_bp_mm_hg",
            "oxygen_saturation_pct",
            "temperature_c",
            "consciousness",
        )
        return [name for name in names if getattr(self, name) is None]


class Patient(BaseModel):
    """Minimum patient record used by the prototype.

    There is deliberately no patient name, address, phone number, or government
    identifier. ``expected_acuity`` and ``scenario_tags`` are synthetic-only
    evaluation metadata and are never model features.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    patient_id: PatientId
    age_years: float = Field(ge=0, le=130)
    arrival_time: datetime
    symptoms: list[Symptom] = Field(min_length=1, max_length=12)
    pain_score: int | None = Field(default=None, ge=0, le=10)
    observed_distress: bool = False
    has_prior_record: bool = False
    pregnancy: bool | None = None
    vitals: VitalSigns
    previous_vitals: VitalSigns | None = None
    last_clinical_review_at: datetime | None = None
    status: PatientStatus = PatientStatus.WAITING
    expected_acuity: AcuityLevel | None = None
    scenario_tags: list[str] = Field(default_factory=list, max_length=12)

    @field_validator("arrival_time", "last_clinical_review_at")
    @classmethod
    def validate_datetimes(cls, value: datetime | None, info) -> datetime | None:
        if value is None:
            return None
        return require_aware(value, info.field_name)

    @field_validator("symptoms")
    @classmethod
    def remove_duplicate_symptoms(cls, value: list[Symptom]) -> list[Symptom]:
        return list(dict.fromkeys(value))

    @field_validator("scenario_tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        cleaned = [
            tag.strip().lower().replace(" ", "_") for tag in value if tag.strip()
        ]
        return list(dict.fromkeys(cleaned))

    @model_validator(mode="after")
    def validate_timeline(self) -> Patient:
        if (
            self.last_clinical_review_at is not None
            and self.last_clinical_review_at < self.arrival_time
        ):
            raise ValueError("last clinical review cannot be before arrival")
        if (
            self.previous_vitals is not None
            and self.previous_vitals.recorded_at > self.vitals.recorded_at
        ):
            raise ValueError("previous vitals must not be newer than current vitals")
        return self

    @property
    def age_group(self) -> AgeGroup:
        if self.age_years < 18:
            return AgeGroup.PEDIATRIC
        if self.age_years >= 65:
            return AgeGroup.GERIATRIC
        return AgeGroup.ADULT
