"""Small HTTP client used by the Streamlit dashboard."""

from __future__ import annotations

from typing import Any

import httpx2


class APIClient:
    def __init__(self, base_url: str, role: str = "doctor") -> None:
        self.base_url = base_url.rstrip("/")
        self.role = role

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        with httpx2.Client(
            base_url=self.base_url,
            timeout=10,
            trust_env=False,
            headers={"X-Demo-Role": self.role},
        ) as client:
            response = client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def access(self) -> dict[str, Any]:
        return self._request("GET", "/v1/access")

    def infrastructure(self) -> dict[str, Any]:
        return self._request("GET", "/v1/infrastructure")

    def patients(self) -> list[dict[str, Any]]:
        return self._request("GET", "/v1/patients")

    def queue(self, *, model_failure: bool = False) -> dict[str, Any]:
        return self._request(
            "GET",
            "/v1/queue",
            params={"simulate_model_failure": model_failure},
        )

    def load_scenario(self, scenario: str) -> dict[str, Any]:
        return self._request("POST", f"/v1/simulations/{scenario}")

    def beds(self, *, model_failure: bool = False) -> dict[str, Any]:
        return self._request(
            "GET",
            "/v1/beds",
            params={"simulate_model_failure": model_failure},
        )

    def baselines(self) -> dict[str, Any]:
        return self._request("GET", "/v1/evaluation/baselines")

    def coordination(self, domain: str) -> list[dict[str, Any]]:
        return self._request("GET", f"/v1/coordination/{domain}")

    def acknowledge(
        self,
        *,
        domain: str,
        task_id: str,
        actor_id: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            f"/v1/coordination/{domain}/{task_id}/acknowledge",
            json={"actor_id": actor_id},
        )

    def deteriorate(self, patient_id: str) -> dict[str, Any]:
        return self._request("POST", f"/v1/simulations/deteriorate/{patient_id}")

    def discharge(self, patient_id: str) -> dict[str, Any]:
        return self._request(
            "PATCH",
            f"/v1/patients/{patient_id}/status",
            params={"patient_status": "discharged"},
        )

    def override(
        self,
        *,
        patient_id: str,
        target_position: int,
        clinician_id: str,
        reason: str,
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/queue/overrides",
            json={
                "patient_id": patient_id,
                "target_position": target_position,
                "clinician_id": clinician_id,
                "reason": reason,
            },
        )

    def audit(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._request("GET", "/v1/audit", params={"limit": limit})

    def verify_audit(self) -> dict[str, Any]:
        return self._request("GET", "/v1/audit/verify")
