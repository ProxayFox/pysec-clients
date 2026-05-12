"""Tests for alert endpoint write request construction and caching."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx

from mde_client.endpoints.alerts import AlertsEndpoint, AlertsResults
from mde_client.models.action_payloads import (
    BatchUpdateAlertPayload,
    CreateAlertByReferencePayload,
)


def _fake_response(method: str, path: str, body: dict[str, Any]) -> httpx.Response:
    return httpx.Response(
        200,
        json=body,
        request=httpx.Request(method, f"https://fake.api{path}"),
    )


def _make_endpoint() -> AlertsEndpoint:
    http_client = MagicMock(spec=httpx.Client)
    http_client.base_url = "https://fake.api"
    auth = MagicMock()
    auth.token = "fake-token"
    return AlertsEndpoint(http_client, auth)


class _FakeAlertsEndpoint(AlertsEndpoint):
    def __init__(self, body: dict[str, Any]) -> None:
        http_client = MagicMock(spec=httpx.Client)
        http_client.base_url = "https://fake.api"
        auth = MagicMock()
        auth.token = "fake-token"
        super().__init__(http_client, auth)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self._body = body

    async def _arequest(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self.calls.append((method, path, kwargs))
        return _fake_response(method, path, self._body)


def _alert_body(alert_id: str) -> dict[str, Any]:
    return {
        "id": alert_id,
        "severity": "Medium",
        "status": "New",
        "title": "Example alert",
        "description": "Alert description",
        "machineId": "machine-1",
    }


class TestAlertWrites:
    def test_create_alert_by_reference_uses_json_body(self) -> None:
        payload = CreateAlertByReferencePayload(
            machineId="machine-1",
            severity="Medium",
            title="Example alert",
            description="Alert description",
            recommendedAction="Investigate",
            eventTime="2026-01-01T00:00:00Z",
            reportId="report-1",
            category="Malware",
        )

        result = _make_endpoint().createAlertByReference(payload)

        assert isinstance(result, AlertsResults)
        assert result._path == "/api/alerts/CreateAlertByReference"
        assert result._params == {}
        assert result._request_kwargs == {"json": payload.model_dump(exclude_none=True)}

    def test_batch_update_uses_json_body(self) -> None:
        payload = BatchUpdateAlertPayload(
            alertIds=["alert-1"],
            status="InProgress",
            comment="Taking ownership",
        )

        result = _make_endpoint().batchUpdate(payload)

        assert isinstance(result, AlertsResults)
        assert result._path == "/api/alerts/batchUpdate"
        assert result._params == {}
        assert result._request_kwargs == {"json": payload.model_dump(exclude_none=True)}

    def test_create_alert_by_reference_materializes_once(self) -> None:
        endpoint = _FakeAlertsEndpoint(_alert_body("alert-1"))
        payload = CreateAlertByReferencePayload(
            machineId="machine-1",
            severity="Medium",
            title="Example alert",
            description="Alert description",
            recommendedAction="Investigate",
            eventTime="2026-01-01T00:00:00Z",
            reportId="report-1",
            category="Malware",
        )

        results = endpoint.createAlertByReference(payload)

        assert results.to_dicts()[0]["id"] == "alert-1"
        _ = results.to_arrow()

        assert len(endpoint.calls) == 1
        assert endpoint.calls[0][0] == "POST"
        assert endpoint.calls[0][1] == "/api/alerts/CreateAlertByReference"
        assert endpoint.calls[0][2]["json"] == payload.model_dump(exclude_none=True)

    def test_batch_update_materializes_once(self) -> None:
        endpoint = _FakeAlertsEndpoint(_alert_body("alert-2"))
        payload = BatchUpdateAlertPayload(
            alertIds=["alert-2"],
            status="Resolved",
            comment="Closed after triage",
        )

        results = endpoint.batchUpdate(payload)

        assert results.to_dicts()[0]["id"] == "alert-2"
        _ = results.to_polars()

        assert len(endpoint.calls) == 1
        assert endpoint.calls[0][0] == "POST"
        assert endpoint.calls[0][1] == "/api/alerts/batchUpdate"
        assert endpoint.calls[0][2]["json"] == payload.model_dump(exclude_none=True)
