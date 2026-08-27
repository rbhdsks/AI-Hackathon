"""Configurable hospital, RBAC, and shift models for the demonstration."""

from __future__ import annotations

import json
from datetime import time
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from patient_triage.domain.enums import HospitalLevel, Permission, StaffRole


class ShiftProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str = Field(min_length=2, max_length=100)
    start_time: time
    end_time: time

    @property
    def duration_hours(self) -> float:
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        duration = (end_minutes - start_minutes) % (24 * 60)
        return duration / 60 if duration else 24.0


class ZoneProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=2, max_length=80)
    bed_count: int = Field(ge=1, le=1000)


class StaffingProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    emergency_physicians: int = Field(ge=0, le=1000)
    resident_doctors: int = Field(ge=0, le=1000)
    triage_nurses: int = Field(ge=0, le=1000)
    staff_nurses: int = Field(ge=0, le=5000)
    pharmacists: int = Field(ge=0, le=1000)
    blood_bank_technicians: int = Field(ge=0, le=1000)
    administrators: int = Field(ge=0, le=1000)

    @property
    def clinical_staff(self) -> int:
        return (
            self.emergency_physicians
            + self.resident_doctors
            + self.triage_nurses
            + self.staff_nurses
        )


class HospitalProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    profile_id: str = Field(pattern=r"^[a-z0-9][a-z0-9_-]+$")
    display_name: str = Field(min_length=3, max_length=160)
    hospital_level: HospitalLevel
    assumption_notice: str = Field(min_length=20, max_length=500)
    catchment_population: int = Field(ge=1)
    total_hospital_beds: int = Field(ge=1)
    ed_beds: int = Field(ge=1)
    treatment_teams: int = Field(ge=1)
    normal_shift_arrivals: int = Field(ge=1)
    surge_shift_arrivals: int = Field(ge=1)
    shift: ShiftProfile
    zones: list[ZoneProfile] = Field(min_length=1)
    staffing: StaffingProfile
    model_components: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_capacity(self) -> HospitalProfile:
        if self.ed_beds > self.total_hospital_beds:
            raise ValueError("ED beds cannot exceed total hospital beds")
        if sum(zone.bed_count for zone in self.zones) != self.ed_beds:
            raise ValueError("zone bed counts must equal ED bed count")
        if self.surge_shift_arrivals < self.normal_shift_arrivals:
            raise ValueError("surge arrivals cannot be below normal arrivals")
        if self.treatment_teams > self.staffing.clinical_staff:
            raise ValueError("treatment teams cannot exceed clinical staff")
        return self


class RolePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    role: StaffRole
    display_name: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=10, max_length=300)
    read_permissions: list[Permission] = Field(default_factory=list)
    write_permissions: list[Permission] = Field(default_factory=list)

    @property
    def all_permissions(self) -> frozenset[Permission]:
        return frozenset(self.read_permissions + self.write_permissions)


class AccessControlMatrix(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    prototype_notice: str = Field(min_length=20, max_length=500)
    roles: list[RolePolicy] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_roles(self) -> AccessControlMatrix:
        role_names = [policy.role for policy in self.roles]
        if len(role_names) != len(set(role_names)):
            raise ValueError("RBAC roles must be unique")
        return self

    def policy_for(self, role: StaffRole) -> RolePolicy:
        try:
            return next(policy for policy in self.roles if policy.role is role)
        except StopIteration as exc:
            raise ValueError(f"role '{role}' has no access policy") from exc


ModelT = TypeVar("ModelT", bound=BaseModel)


def _load_model(path: Path, model_type: type[ModelT]) -> ModelT:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return model_type.model_validate(payload)


def load_hospital_profile(path: Path) -> HospitalProfile:
    return _load_model(path, HospitalProfile)


def load_access_control(path: Path) -> AccessControlMatrix:
    return _load_model(path, AccessControlMatrix)
