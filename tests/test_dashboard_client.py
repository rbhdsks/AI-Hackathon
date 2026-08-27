from __future__ import annotations

from typing import Any, ClassVar

import httpx2

from dashboard.client import APIClient


class _Response:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, str]:
        return {"status": "ok"}


class _Client:
    captured_init: ClassVar[dict[str, Any]] = {}
    captured_request: ClassVar[tuple[str, str] | None] = None

    def __init__(self, **kwargs: Any) -> None:
        self.captured_init.update(kwargs)

    def __enter__(self) -> _Client:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def request(self, method: str, path: str, **_kwargs: Any) -> _Response:
        self.captured_request = (method, path)
        type(self).captured_request = self.captured_request
        return _Response()


def test_client_ignores_proxy_environment_for_configured_api(monkeypatch) -> None:
    monkeypatch.setattr(httpx2, "Client", _Client)

    response = APIClient("http://localhost:8000/").health()

    assert response == {"status": "ok"}
    assert _Client.captured_init == {
        "base_url": "http://localhost:8000",
        "timeout": 10,
        "trust_env": False,
        "headers": {"X-Demo-Role": "doctor"},
    }
    assert _Client.captured_request == ("GET", "/health")


def test_role_client_routes(monkeypatch) -> None:
    monkeypatch.setattr(httpx2, "Client", _Client)
    client = APIClient("http://localhost:8000", role="pharmacy")

    assert client.infrastructure() == {"status": "ok"}
    assert _Client.captured_init["headers"] == {"X-Demo-Role": "pharmacy"}
    client.coordination("pharmacy")
    assert _Client.captured_request == ("GET", "/v1/coordination/pharmacy")
    client.acknowledge(
        domain="pharmacy",
        task_id="pharmacy:SYN-001",
        actor_id="pharmacist_01",
    )
    assert _Client.captured_request == (
        "POST",
        "/v1/coordination/pharmacy/pharmacy:SYN-001/acknowledge",
    )
