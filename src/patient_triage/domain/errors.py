"""Domain-specific errors translated cleanly by the API layer."""


class TriageError(Exception):
    """Base class for expected prototype errors."""


class DuplicatePatientError(TriageError):
    pass


class PatientNotFoundError(TriageError):
    pass


class InvalidTimelineError(TriageError):
    pass


class InvalidOverrideError(TriageError):
    pass


class PermissionDeniedError(TriageError):
    pass


class CoordinationTaskNotFoundError(TriageError):
    pass
