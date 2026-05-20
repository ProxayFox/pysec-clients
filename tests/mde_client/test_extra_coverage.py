"""Extra tests for library, deviceAvHealth, alerts, advancedqueries.

These cover the request-helper paths (delete, error mapping, payload
serialisation, normalisation closures) that the existing focused tests
don't reach.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import orjson
import pytest

from mde_client.endpoints.alerts import (
    AlertsEndpoint,
    BatchUpdateAlertPayload,
    CreateAlertByReferencePayload,
)
from mde_client.endpoints.advancedqueries import AdvancedHuntingQueriesEndpoint
from mde_client.endpoints.deviceAvHealth import DeviceAVHealthResults
from mde_client.endpoints.library import (
    LibraryFilesEndpoint,
    LibraryFilesUpdatePayload,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resp(status: int, *, body: Any = None) -> httpx.Response:
    if body is None:
        return httpx.Response(
            status,
            text="",
            request=httpx.Request("GET", "https://fake.api/x"),
        )
    return httpx.Response(
        status,
        json=body,
        request=httpx.Request("GET", "https://fake.api/x"),
    )


class _Recording:
    def __init__(self, cls, responses: list[httpx.Response]) -> None:
        http = MagicMock(spec=httpx.Client)
        http.base_url = "https://fake.api"
        auth = MagicMock()
        auth.token = "fake-token"
        self.endpoint = cls(http, auth)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self._responses = responses

        async def _arequest(method, path, **kwargs):
            self.calls.append((method, path, kwargs))
            return self._responses.pop(0)

        self.endpoint._arequest = _arequest  # type: ignore[method-assign]


# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------


class TestLibraryUploadHelpers:
    def test_to_request_kwargs_with_parameters(self) -> None:
        payload = LibraryFilesUpdatePayload(
            file_name="run.ps1",
            file_content=b"data",
            description="d",
            parameters_description="p",
            override_if_exists=True,
        )
        kwargs = payload.to_request_kwargs()
        assert kwargs["files"]["File"][0] == "run.ps1"
        assert kwargs["files"]["File"][1] == b"data"
        assert kwargs["data"]["HasParameters"] == "true"
        assert kwargs["data"]["OverrideIfExists"] == "true"

    def test_to_request_kwargs_explicit_has_parameters_false(self) -> None:
        payload = LibraryFilesUpdatePayload(
            file_name="run.ps1",
            file_content=b"data",
            description="d",
            has_parameters=False,
        )
        kwargs = payload.to_request_kwargs()
        assert kwargs["data"]["HasParameters"] == "false"
        assert "OverrideIfExists" not in kwargs["data"]


class TestLibraryUploadErrors:
    def test_400_raises_value_error(self) -> None:
        rec = _Recording(LibraryFilesEndpoint, [_resp(400, body={})])
        payload = LibraryFilesUpdatePayload(
            file_name="r.ps1", file_content=b"x", description="d"
        )
        with pytest.raises(ValueError, match="r.ps1"):
            rec.endpoint.upload(payload)

    def test_other_status_raises_runtime_error(self) -> None:
        rec = _Recording(LibraryFilesEndpoint, [_resp(500, body={})])
        payload = LibraryFilesUpdatePayload(
            file_name="r.ps1", file_content=b"x", description="d"
        )
        with pytest.raises(RuntimeError):
            rec.endpoint.upload(payload)


class TestLibraryDelete:
    def test_204_returns_true(self) -> None:
        rec = _Recording(LibraryFilesEndpoint, [_resp(204)])
        assert rec.endpoint.delete("file.ps1") is True
        assert rec.calls[0] == ("DELETE", "/api/libraryfiles/file.ps1", {})

    def test_404_raises_value_error(self) -> None:
        rec = _Recording(LibraryFilesEndpoint, [_resp(404)])
        with pytest.raises(ValueError, match="file.ps1"):
            rec.endpoint.delete("file.ps1")

    def test_other_status_raises_runtime_error(self) -> None:
        rec = _Recording(LibraryFilesEndpoint, [_resp(500)])
        with pytest.raises(RuntimeError):
            rec.endpoint.delete("file.ps1")


# ---------------------------------------------------------------------------
# DeviceAVHealth normalize_export_record
# ---------------------------------------------------------------------------


class TestDeviceAvHealthNormalize:
    def test_returns_callable(self) -> None:
        assert callable(DeviceAVHealthResults._normalize_export_record())

    def test_flatten_windows_record(self) -> None:
        fn = DeviceAVHealthResults._normalize_export_record()
        assert fn is not None
        nested = {
            "AvMode": "0",
            "AvIsSignatureUptoDate": True,
            "AvScanResults": orjson.dumps(
                {
                    "Quick": {
                        "ScanStatus": "Success",
                        "ErrorCode": "0",
                        "Timestamp": "2025-01-01T00:00:00Z",
                    },
                    "Full": {
                        "ScanStatus": "Failed",
                        "ErrorCode": "5",
                        "Timestamp": "2025-01-02T00:00:00Z",
                    },
                }
            ).decode(),
        }
        record = {
            "DeviceId": "m-1",
            "DeviceName": "host",
            "OsPlatform": "Windows10",
            "DeviceGatheredInfo": orjson.dumps(nested).decode(),
        }
        out = fn(record)
        assert out["machineId"] == "m-1"
        assert out["computerDnsName"] == "host"
        assert out["osKind"] == "windows"
        assert out["avMode"] == "0"
        assert out["avIsSignatureUpToDate"] == "True"
        assert out["quickScanResult"] == "Success"
        assert out["fullScanResult"] == "Failed"
        assert out["id"] == "m-1"

    def test_flatten_linux_uses_dash_placeholder(self) -> None:
        fn = DeviceAVHealthResults._normalize_export_record()
        assert fn is not None
        record = {
            "DeviceId": "m-2",
            "OsPlatform": "Linux",
            "DeviceGatheredInfo": orjson.dumps({"AvMode": "0"}).decode(),
        }
        out = fn(record)
        assert out["osKind"] == "linux"
        assert out["quickScanResult"] == "-"
        assert out["fullScanResult"] == "-"

    def test_flatten_macos_kind(self) -> None:
        fn = DeviceAVHealthResults._normalize_export_record()
        assert fn is not None
        record = {
            "DeviceId": "m-3",
            "OsPlatform": "macOS",
            "DeviceGatheredInfo": orjson.dumps({"AvMode": "0"}).decode(),
        }
        out = fn(record)
        assert out["osKind"] == "mac"

    def test_flatten_handles_malformed_nested_json(self) -> None:
        fn = DeviceAVHealthResults._normalize_export_record()
        assert fn is not None
        record = {
            "DeviceId": "m-4",
            "OsPlatform": "Windows10",
            "DeviceGatheredInfo": "not-json",
        }
        out = fn(record)
        # No exception; record still has id.
        assert out["machineId"] == "m-4"

    def test_flatten_handles_dict_nested(self) -> None:
        fn = DeviceAVHealthResults._normalize_export_record()
        assert fn is not None
        record = {
            "DeviceId": "m-5",
            "OsPlatform": "Windows10",
            "DeviceGatheredInfo": {"AvMode": "1"},
        }
        out = fn(record)
        assert out["avMode"] == "1"

    def test_flatten_handles_missing_nested(self) -> None:
        fn = DeviceAVHealthResults._normalize_export_record()
        assert fn is not None
        record = {"DeviceId": "m-6", "OsPlatform": "Windows10"}
        out = fn(record)
        assert out["machineId"] == "m-6"


# ---------------------------------------------------------------------------
# Alerts: update payload + mutation methods
# ---------------------------------------------------------------------------


class TestAlertsRelations:
    def test_user_path(self) -> None:
        rec = _Recording(AlertsEndpoint, [])
        result = rec.endpoint.user("alert-1")
        assert result._path == "/api/alerts/alert-1/user"

    def test_machines_path(self) -> None:
        rec = _Recording(AlertsEndpoint, [])
        result = rec.endpoint.machines("alert-1")
        assert result._path == "/api/alerts/alert-1/machine"


class TestAlertsBatchUpdate:
    def test_returns_true_on_200(self) -> None:
        rec = _Recording(AlertsEndpoint, [_resp(200, body={})])
        payload = BatchUpdateAlertPayload(alertIds=["a-1", "a-2"], status="Resolved")
        assert rec.endpoint.batchUpdate(payload) is True
        assert rec.calls[0][0] == "POST"
        assert rec.calls[0][1] == "/api/alerts/batchUpdate"
        assert rec.calls[0][2]["json"] == payload.model_dump(exclude_none=True)

    def test_non_200_raises_runtime_error(self) -> None:
        rec = _Recording(AlertsEndpoint, [_resp(500)])
        payload = BatchUpdateAlertPayload(alertIds=["a-1"], status="Resolved")
        with pytest.raises(RuntimeError):
            rec.endpoint.batchUpdate(payload)


class TestCreateAlertByReference:
    def test_path_and_body(self) -> None:
        rec = _Recording(AlertsEndpoint, [])
        payload = CreateAlertByReferencePayload(
            machineId="m-1",
            severity="High",
            title="t",
            description="d",
            recommendedAction="r",
            eventTime="2025-01-01T00:00:00Z",
            reportId="rid",
        )
        result = rec.endpoint.createAlertByReference(payload)
        assert result._path == "/api/alerts/CreateAlertByReference"
        assert result._method == "POST"
        assert result._request_kwargs["json"] == payload.model_dump(exclude_none=True)


# ---------------------------------------------------------------------------
# Advanced hunting queries
# ---------------------------------------------------------------------------


class TestAdvancedQueries:
    def test_run_query_posts_body(self) -> None:
        rec = _Recording(
            AdvancedHuntingQueriesEndpoint,
            [
                _resp(
                    200,
                    body={
                        "Schema": [{"Name": "id", "Type": "string"}],
                        "Results": [{"id": "a"}],
                    },
                )
            ],
        )
        result = rec.endpoint.run("DeviceInfo | take 1")
        result.to_dicts()
        assert rec.calls[0][0] == "POST"
        assert rec.calls[0][1] == "/api/advancedqueries/run"
        assert rec.calls[0][2]["json"] == {"Query": "DeviceInfo | take 1"}
