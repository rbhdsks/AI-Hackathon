"""Audit event model."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    occurred_at: datetime
    actor_id: str
    event_type: str
    patient_id: str | None
    payload: dict[str, Any]
    model_version: str
    previous_hash: str
    event_hash: str
