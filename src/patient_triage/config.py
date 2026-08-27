"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    """Runtime settings with safe prototype defaults."""

    app_name: str = "PatientTriage.ai"
    environment: str = "development"
    database_path: Path = Path("data/patient_triage.db")
    hospital_profile_path: Path = Path("configs/district_hospital.json")
    rbac_path: Path = Path("configs/rbac.json")
    bootstrap_demo_data: bool = True
    normal_capacity: int = 20
    surge_multiplier: int = 3
    model_version: str = "feature-cdm-v1"
    allowed_clock_skew_minutes: int = 5

    @classmethod
    def from_env(cls) -> Settings:
        """Create settings without relying on a deprecated settings API."""

        defaults = cls()
        return cls(
            app_name=os.getenv("PATIENT_TRIAGE_APP_NAME", defaults.app_name),
            environment=os.getenv("PATIENT_TRIAGE_ENVIRONMENT", defaults.environment),
            database_path=Path(
                os.getenv("PATIENT_TRIAGE_DATABASE_PATH", str(defaults.database_path))
            ),
            hospital_profile_path=Path(
                os.getenv(
                    "PATIENT_TRIAGE_HOSPITAL_PROFILE_PATH",
                    str(defaults.hospital_profile_path),
                )
            ),
            rbac_path=Path(
                os.getenv("PATIENT_TRIAGE_RBAC_PATH", str(defaults.rbac_path))
            ),
            bootstrap_demo_data=_as_bool(
                os.getenv("PATIENT_TRIAGE_BOOTSTRAP_DEMO_DATA"),
                defaults.bootstrap_demo_data,
            ),
            normal_capacity=int(
                os.getenv("PATIENT_TRIAGE_NORMAL_CAPACITY", defaults.normal_capacity)
            ),
            surge_multiplier=int(
                os.getenv("PATIENT_TRIAGE_SURGE_MULTIPLIER", defaults.surge_multiplier)
            ),
            model_version=os.getenv(
                "PATIENT_TRIAGE_MODEL_VERSION", defaults.model_version
            ),
            allowed_clock_skew_minutes=int(
                os.getenv(
                    "PATIENT_TRIAGE_ALLOWED_CLOCK_SKEW_MINUTES",
                    defaults.allowed_clock_skew_minutes,
                )
            ),
        )
