"""Configurable operational thresholds for the synthetic prototype."""

from patient_triage.domain.enums import AcuityLevel, QueueMode

_NORMAL_WAIT_MINUTES: dict[AcuityLevel, float] = {
    AcuityLevel.CRITICAL: 0,
    AcuityLevel.EMERGENT: 10,
    AcuityLevel.URGENT: 30,
    AcuityLevel.LESS_URGENT: 60,
    AcuityLevel.NON_URGENT: 120,
}


def max_wait_minutes(acuity: AcuityLevel, mode: QueueMode) -> float:
    """Return prototype reassessment thresholds, not clinical guidance."""

    base = _NORMAL_WAIT_MINUTES[acuity]
    if mode is QueueMode.SURGE and base > 0:
        return base / 2
    return base


def stale_after_minutes(mode: QueueMode) -> float:
    return 15 if mode is QueueMode.SURGE else 30
