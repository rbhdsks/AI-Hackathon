"""Shared enumerations."""

from enum import IntEnum, StrEnum


class AgeGroup(StrEnum):
    PEDIATRIC = "pediatric"
    ADULT = "adult"
    GERIATRIC = "geriatric"


class AcuityLevel(IntEnum):
    """Five-level prototype acuity; smaller values are more urgent."""

    CRITICAL = 1
    EMERGENT = 2
    URGENT = 3
    LESS_URGENT = 4
    NON_URGENT = 5

    @property
    def label(self) -> str:
        return {
            1: "critical",
            2: "emergent",
            3: "urgent",
            4: "less_urgent",
            5: "non_urgent",
        }[int(self)]


class ConfidenceLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Consciousness(StrEnum):
    ALERT = "alert"
    RESPONDS_TO_VOICE = "responds_to_voice"
    RESPONDS_TO_PAIN = "responds_to_pain"
    UNRESPONSIVE = "unresponsive"


class PatientStatus(StrEnum):
    WAITING = "waiting"
    IN_TREATMENT = "in_treatment"
    DISCHARGED = "discharged"


class QueueMode(StrEnum):
    NORMAL = "normal"
    SURGE = "surge"


class QueueState(StrEnum):
    STABLE = "stable"
    REASSESSMENT_DUE = "reassessment_due"
    DETERIORATING = "deteriorating"
    CRITICAL_ESCALATION = "critical_escalation"
    STALE_INFORMATION = "stale_information"
    MANUAL_REVIEW = "manual_review"


class HospitalLevel(StrEnum):
    WARD = "ward"
    DISTRICT = "district"
    STATE = "state"
    REGIONAL = "regional"


class StaffRole(StrEnum):
    NURSE = "nurse"
    DOCTOR = "doctor"
    PHARMACY = "pharmacy"
    ADMINISTRATION = "administration"
    BLOOD_BANK = "blood_bank"


class Permission(StrEnum):
    FACILITY_READ = "facility.read"
    PATIENT_READ = "patient.read"
    QUEUE_READ = "queue.read"
    BED_READ = "bed.read"
    INTAKE_WRITE = "intake.write"
    VITALS_WRITE = "vitals.write"
    BED_WRITE = "bed.write"
    OVERRIDE_WRITE = "override.write"
    DISPOSITION_WRITE = "disposition.write"
    PHARMACY_READ = "pharmacy.read"
    PHARMACY_ACKNOWLEDGE = "pharmacy.acknowledge"
    BLOOD_BANK_READ = "blood_bank.read"
    BLOOD_BANK_ACKNOWLEDGE = "blood_bank.acknowledge"
    ANALYTICS_READ = "analytics.read"
    AUDIT_READ = "audit.read"
    SCENARIO_WRITE = "scenario.write"


class BedStatus(StrEnum):
    EMPTY = "empty"
    OCCUPIED = "occupied"


class CoordinationDomain(StrEnum):
    PHARMACY = "pharmacy"
    BLOOD_BANK = "blood_bank"


class TaskStatus(StrEnum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"


class Symptom(StrEnum):
    CHEST_PAIN = "chest_pain"
    SHORTNESS_OF_BREATH = "shortness_of_breath"
    SEVERE_BLEEDING = "severe_bleeding"
    ALTERED_MENTAL_STATUS = "altered_mental_status"
    SEIZURE = "seizure"
    FEVER = "fever"
    ABDOMINAL_PAIN = "abdominal_pain"
    HEADACHE = "headache"
    TRAUMA = "trauma"
    VOMITING = "vomiting"
    WEAKNESS = "weakness"
    RASH = "rash"
    MINOR_INJURY = "minor_injury"
    COUGH = "cough"
    DIZZINESS = "dizziness"
    UNKNOWN = "unknown"
