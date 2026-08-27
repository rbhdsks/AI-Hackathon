"""Small policy evaluator for role-based prototype permissions."""

from __future__ import annotations

from patient_triage.domain.enums import Permission, StaffRole
from patient_triage.domain.errors import PermissionDeniedError
from patient_triage.domain.hospital import AccessControlMatrix


class AccessController:
    def __init__(self, matrix: AccessControlMatrix) -> None:
        self.matrix = matrix

    def permissions_for(self, role: StaffRole) -> frozenset[Permission]:
        return self.matrix.policy_for(role).all_permissions

    def require(self, role: StaffRole, permission: Permission) -> None:
        if permission not in self.permissions_for(role):
            raise PermissionDeniedError(
                f"role '{role.value}' does not have permission '{permission.value}'"
            )
