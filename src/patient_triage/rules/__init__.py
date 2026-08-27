"""Explicit prototype safety and waiting-time rules."""

from patient_triage.rules.safety_rules import RuleHit, SafetyAssessment, evaluate_safety
from patient_triage.rules.thresholds import max_wait_minutes, stale_after_minutes

__all__ = [
    "RuleHit",
    "SafetyAssessment",
    "evaluate_safety",
    "max_wait_minutes",
    "stale_after_minutes",
]
