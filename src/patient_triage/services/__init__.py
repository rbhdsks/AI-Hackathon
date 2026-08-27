"""Application services."""

from patient_triage.services.ranking import RankingService
from patient_triage.services.triage import TriageService

__all__ = ["RankingService", "TriageService"]
