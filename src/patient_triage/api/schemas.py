"""Small API-specific response models."""

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    app: str
    model_version: str
    prototype_only: bool


class AuditVerificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool


class ScenarioResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: str
    patient_count: int
