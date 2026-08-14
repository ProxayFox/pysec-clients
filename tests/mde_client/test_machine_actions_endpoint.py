"""Tests for MachineActionsEndpoint request construction.

The endpoint mostly delegates to private ``_*`` helpers on
``MachinesEndpoint`` — we exercise both the direct query/get methods and a
representative spread of delegated actions to confirm the helpers route to
the expected paths with the expected JSON bodies.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from mde_client.endpoints.machineActions import (
    ActionAvailabilityStatusResults,
    MachineActionsEndpoint,
    MachineActionsQuery,
    MachineActionsResults,
)
from mde_client.models.action_payloads import (
    CancelPayload,
    CollectInvestigationPackagePayload,
    IsolatePayload,
    OffBoardPayload,
    RestrictCodeExecutionPayload,
    RunAntiVirusScanPayload,
    RunLiveResponsePayload,
    StopAndQuarantineFilePayload,
    UnisolatePayload,
    UnrestrictCodeExecutionPayload,
)


class _Recording(MachineActionsEndpoint):
    def __init__(self, *, status: int = 200, body: Any | None = None) -> None:
        http_client = MagicMock(spec=httpx.Client)
        http_client.base_url = "https://fake.api"
        auth = MagicMock()
        auth.token = "fake-token"
        super().__init__(http_client, auth)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self._status = status
        self._body = body if body is not None else {}

    async def _arequest(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self.calls.append((method, path, kwargs))
        return httpx.Response(
            self._status,
            json=self._body,
            request=httpx.Request(method, f"https://fake.api{path}"),
        )


class TestGetAll:
    def test_path(self, make_endpoint) -> None:
        result = make_endpoint(MachineActionsEndpoint).get_all()
        assert isinstance(result, MachineActionsResults)
        assert result._path == "/api/machineactions"

    def test_query_filter(self, make_endpoint) -> None:
        result = make_endpoint(MachineActionsEndpoint).get_all(
            MachineActionsQuery(
                id=None,
                status="Pending",
                machineId=None,
                type=None,
                requestor=None,
                creationDateTimeUtc=None,
            )
        )
        assert "status eq 'Pending'" in result._params["$filter"]


class TestGet:
    def test_path(self, make_endpoint) -> None:
        result = make_endpoint(MachineActionsEndpoint).get("act-1")
        assert result._path == "/api/machineactions/act-1"


def _comment(extra: dict[str, Any] | None = None) -> dict[str, Any]:
    d: dict[str, Any] = {"Comment": "test"}
    if extra:
        d.update(extra)
    return d


class TestDelegatedActions:
    """Confirm each helper builds the expected path + POST body."""

    @pytest.mark.parametrize(
        "method,payload_factory,expected_suffix",
        [
            (
                "collectInvestigationPackage",
                lambda: CollectInvestigationPackagePayload(Comment="t"),
                "collectInvestigationPackage",
            ),
            (
                "isolate",
                lambda: IsolatePayload(Comment="t"),
                "isolate",
            ),
            (
                "unisolate",
                lambda: UnisolatePayload(Comment="t"),
                "unisolate",
            ),
            (
                "restrictCodeExecution",
                lambda: RestrictCodeExecutionPayload(Comment="t"),
                "restrictCodeExecution",
            ),
            (
                "unrestrictCodeExecution",
                lambda: UnrestrictCodeExecutionPayload(Comment="t"),
                "unrestrictCodeExecution",
            ),
            (
                "runAntiVirusScan",
                lambda: RunAntiVirusScanPayload(Comment="t", ScanType="Quick"),
                "runAntiVirusScan",
            ),
            (
                "runLiveResponse",
                lambda: RunLiveResponsePayload(Comment="t", Commands=["a"]),
                "runliveresponse",
            ),
            (
                "offBoard",
                lambda: OffBoardPayload(Comment="t"),
                "offboard",
            ),
            (
                "stopAndQuarantineFile",
                lambda: StopAndQuarantineFilePayload(Comment="t", Sha1="abc"),
                "StopAndQuarantineFile",
            ),
        ],
    )
    def test_action_path_and_body(
        self, make_endpoint, method: str, payload_factory, expected_suffix: str
    ) -> None:
        ep = make_endpoint(MachineActionsEndpoint)
        payload = payload_factory()
        result = getattr(ep, method)("device-1", payload)
        assert isinstance(result, MachineActionsResults)
        assert result._path == f"/api/machines/device-1/{expected_suffix}"
        assert result._method == "POST"
        assert result._request_kwargs["json"] == payload.model_dump()

    def test_get_machine_actions(self, make_endpoint) -> None:
        result = make_endpoint(MachineActionsEndpoint).getMachineActions("m-1")
        assert result._path == "/api/machines/m-1/machineActions"

    def test_latest_machine_actions(self, make_endpoint) -> None:
        result = make_endpoint(MachineActionsEndpoint).latestMachineActions("m-1")
        assert result._path == "/api/machines/m-1/latestMachineActions"

    def test_available_machine_actions(self, make_endpoint) -> None:
        result = make_endpoint(MachineActionsEndpoint).availableMachineActions("m-1")
        assert isinstance(result, ActionAvailabilityStatusResults)
        assert result._path == "/api/machines/m-1/availableMachineActions"


class TestCancel:
    def test_path_and_body(self, make_endpoint) -> None:
        payload = CancelPayload(Comment="cancelling")
        result = make_endpoint(MachineActionsEndpoint).cancel("act-1", payload)
        assert isinstance(result, MachineActionsResults)
        assert result._path == "/api/machineactions/act-1/cancel"
        assert result._method == "POST"
        assert result._request_kwargs["json"] == payload.model_dump(exclude_none=True)


class TestGetPackage:
    def test_200_returns_value(self) -> None:
        endpoint = _Recording(status=200, body={"value": "https://sas/url"})
        assert endpoint.getPackage("act-1") == "https://sas/url"
        assert endpoint.calls[0][0] == "GET"
        assert endpoint.calls[0][1] == "/api/machineactions/act-1/GetPackageUri"

    def test_404_raises_value_error(self) -> None:
        endpoint = _Recording(status=404, body={"error": "missing"})
        with pytest.raises(ValueError):
            endpoint.getPackage("act-1")

    def test_500_raises_runtime_error(self) -> None:
        endpoint = _Recording(status=500, body={"error": "boom"})
        with pytest.raises(RuntimeError):
            endpoint.getPackage("act-1")


class TestGetLiveResponseResultDownloadLink:
    def test_200_default_index(self) -> None:
        endpoint = _Recording(status=200, body={"value": "https://sas/url"})
        assert endpoint.getLiveResponseResultDownloadLink("act-1") == "https://sas/url"
        assert (
            endpoint.calls[0][1]
            == "/api/machineactions/act-1/GetLiveResponseResultDownloadLink(index=0)"
        )

    def test_200_custom_index(self) -> None:
        endpoint = _Recording(status=200, body={"value": "u"})
        endpoint.getLiveResponseResultDownloadLink("act-1", index=3)
        assert endpoint.calls[0][1].endswith("(index=3)")

    def test_404_raises_value_error(self) -> None:
        endpoint = _Recording(status=404, body={"error": "missing"})
        with pytest.raises(ValueError):
            endpoint.getLiveResponseResultDownloadLink("act-1")

    def test_500_raises_runtime_error(self) -> None:
        endpoint = _Recording(status=500, body={"error": "boom"})
        with pytest.raises(RuntimeError):
            endpoint.getLiveResponseResultDownloadLink("act-1")
