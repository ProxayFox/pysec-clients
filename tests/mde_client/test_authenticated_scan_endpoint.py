"""Tests for authenticated scan endpoint request construction and POST results."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx

from mde_client.endpoints.authenticatedScan import (
    AuthenticatedDefinitionsEndpoint,
    AuthenticatedScanHistoryQuery,
    AuthenticatedScanHistoryResults,
    DeviceAuthenticatedAgentsEndpoint,
)


def _make_definitions_endpoint() -> AuthenticatedDefinitionsEndpoint:
    http_client = MagicMock(spec=httpx.Client)
    http_client.base_url = "https://fake.api"
    auth = MagicMock()
    auth.token = "fake-token"
    return AuthenticatedDefinitionsEndpoint(http_client, auth)


def _make_agents_endpoint() -> DeviceAuthenticatedAgentsEndpoint:
    http_client = MagicMock(spec=httpx.Client)
    http_client.base_url = "https://fake.api"
    auth = MagicMock()
    auth.token = "fake-token"
    return DeviceAuthenticatedAgentsEndpoint(http_client, auth)


def _fake_response(method: str, path: str, body: dict[str, Any]) -> httpx.Response:
    return httpx.Response(
        200,
        json=body,
        request=httpx.Request(method, f"https://fake.api{path}"),
    )


class _FakeDefinitionsEndpoint(AuthenticatedDefinitionsEndpoint):
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


class TestAuthenticatedScanHistoryQuery:
    def test_defaults_do_not_include_page_size(self) -> None:
        params = AuthenticatedScanHistoryQuery().to_odata_filters
        print(params)
        assert "pageSize" not in params

    def test_top_and_skip_are_forwarded(self) -> None:
        params = AuthenticatedScanHistoryQuery(top=10, skip=20).to_odata_filters
        assert params["$top"] == "10"
        assert params["$skip"] == "20"


class TestDefinitionsHistory:
    def test_returns_history_results(self) -> None:
        result = _make_definitions_endpoint().definition_history("scan-1")
        assert isinstance(result, AuthenticatedScanHistoryResults)

    def test_history_uses_definitions_action_path(self) -> None:
        result = _make_definitions_endpoint().definition_history("scan-1")
        assert (
            result._path
            == "/api/DeviceAuthenticatedScanDefinitions/GetScanHistoryByScanDefinitionId"
        )
        assert result._method == "POST"
        assert result._request_kwargs == {"json": {"ScanDefinitionIds": ["scan-1"]}}

    def test_session_history_uses_session_action_path(self) -> None:
        result = _make_definitions_endpoint().session_history(["session-1"])
        assert (
            result._path
            == "/api/DeviceAuthenticatedScanDefinitions/GetScanHistoryBySessionId"
        )
        assert result._method == "POST"
        assert result._request_kwargs == {"json": {"SessionIds": ["session-1"]}}

    def test_post_history_fetches_value_array(self) -> None:
        endpoint = _FakeDefinitionsEndpoint(
            {
                "value": [
                    {
                        "orgId": "org-1",
                        "scanDefinitionId": "scan-1",
                        "sessionId": "session-1",
                        "scannerId": "scanner-1",
                        "numberOfSuccessfullyScannedTargets": 2,
                        "numberOfTargets": 3,
                        "scanStatus": "Success",
                        "generalErrorMessage": None,
                        "scannedTargets": [],
                    }
                ]
            }
        )

        records = endpoint.definition_history("scan-1").to_json()

        assert records[0]["scanDefinitionId"] == "scan-1"
        assert endpoint.calls[0][0] == "POST"
        assert (
            endpoint.calls[0][1]
            == "/api/DeviceAuthenticatedScanDefinitions/GetScanHistoryByScanDefinitionId"
        )
        assert endpoint.calls[0][2]["json"] == {"ScanDefinitionIds": ["scan-1"]}
