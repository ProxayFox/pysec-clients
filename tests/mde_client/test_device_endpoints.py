"""Tests for DeviceGroupsEndpoint, BrowserExtensionEndpoint, CertificateInventoryEndpoint,
FirmwareEndpoint, DeviceAVHealthEndpoint construction and delegation."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
from mde_client.endpoints.browserExtension import (
    BrowserExtensionEndpoint,
    BrowserExtensionsPermissionsInfoQuery,
    BrowserExtensionsPermissionsInfoResults,
)
from mde_client.endpoints.certificateInventory import CertificateInventoryEndpoint
from mde_client.endpoints.deviceAvHealth import (
    DeviceAVHealthEndpoint,
    DeviceAVHealthResults,
)
from mde_client.endpoints.deviceGroups import (
    DeviceGroupResults,
    DeviceGroupsEndpoint,
)
from mde_client.endpoints.firmware import (
    FirmwareEndpoint,
    FirmwareResults,
)
from mde_client.endpoints.machines import MachinesEndpoint
from mde_client.models.action_payloads import (
    AddDeviceGroupsPayload,
    DeleteDeviceGroupsPayload,
    PostDeviceGroupsPayload,
)


class _Recording(DeviceGroupsEndpoint):
    def __init__(self) -> None:
        http_client = MagicMock(spec=httpx.Client)
        http_client.base_url = "https://fake.api"
        auth = MagicMock()
        auth.token = "fake-token"
        super().__init__(http_client, auth)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _arequest(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self.calls.append((method, path, kwargs))
        return httpx.Response(
            200,
            json={},
            request=httpx.Request(method, f"https://fake.api{path}"),
        )


class TestDeviceGroups:
    def test_get_all(self, make_endpoint) -> None:
        result = make_endpoint(DeviceGroupsEndpoint).get_all()
        assert isinstance(result, DeviceGroupResults)
        assert result._path == "/api/deviceGroups"

    def test_get(self, make_endpoint) -> None:
        result = make_endpoint(DeviceGroupsEndpoint).get("g-1")
        assert result._path == "/api/deviceGroups/g-1"
        assert result._single is True

    def test_add_posts_payload(self) -> None:
        endpoint = _Recording()
        payload = AddDeviceGroupsPayload(deviceGroups=["g-1"])
        endpoint.add(payload)
        assert endpoint.calls[0][0] == "POST"
        assert endpoint.calls[0][1] == "/api/deviceGroups/addDeviceGroups"
        assert endpoint.calls[0][2]["json"] == payload.model_dump()

    def test_delete_posts_payload(self) -> None:
        endpoint = _Recording()
        payload = DeleteDeviceGroupsPayload(ids=[1, 2])
        endpoint.delete(payload)
        assert endpoint.calls[0][1] == "/api/deviceGroups/deleteDeviceGroups"

    def test_post_posts_payload(self) -> None:
        endpoint = _Recording()
        payload = PostDeviceGroupsPayload(
            additionsCount=1, deletionsCount=0, deviceGroups=["g-1"]
        )
        endpoint.post(payload)
        assert endpoint.calls[0][1] == "/api/deviceGroups/postDeviceGroups"


class TestBrowserExtension:
    def test_get_all_delegates(self, make_endpoint, monkeypatch) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_browserExtensionsInventoryByMachine",
            lambda self: "sentinel",
        )
        assert make_endpoint(BrowserExtensionEndpoint).get_all() == "sentinel"

    def test_get_all_files_delegates(self, make_endpoint, monkeypatch) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_browserextensionsinventoryExport",
            lambda self: "sentinel",
        )
        assert make_endpoint(BrowserExtensionEndpoint).get_all_files() == "sentinel"

    def test_permissionsinfo(self, make_endpoint) -> None:
        result = make_endpoint(BrowserExtensionEndpoint).permissionsinfo()
        assert isinstance(result, BrowserExtensionsPermissionsInfoResults)
        assert result._path == "/api/browserExtensions/permissionsinfo"

    def test_permissionsinfo_query_filter(self, make_endpoint) -> None:
        result = make_endpoint(BrowserExtensionEndpoint).permissionsinfo(
            BrowserExtensionsPermissionsInfoQuery(severity="High")
        )
        assert "severity eq 'High'" in result._params["$filter"]


class TestCertificateInventory:
    def test_get_all_delegates(self, make_endpoint, monkeypatch) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_certificateAssessmentByMachine",
            lambda self: "sentinel",
        )
        assert make_endpoint(CertificateInventoryEndpoint).get_all() == "sentinel"

    def test_get_all_files_delegates(self, make_endpoint, monkeypatch) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_certificateAssessmentExport",
            lambda self: "sentinel",
        )
        assert make_endpoint(CertificateInventoryEndpoint).get_all_files() == "sentinel"


class TestFirmware:
    def test_get_all(self, make_endpoint) -> None:
        result = make_endpoint(FirmwareEndpoint).get_all()
        assert isinstance(result, FirmwareResults)
        assert result._path == "/api/firmware"
        assert result._single is True

    def test_get_delegates(self, make_endpoint, monkeypatch) -> None:
        captured: dict[str, str] = {}

        def fake(self: MachinesEndpoint, device_id: str):
            captured["device_id"] = device_id
            return "sentinel"

        monkeypatch.setattr(MachinesEndpoint, "_deviceFirmware", fake)
        assert make_endpoint(FirmwareEndpoint).get("d-1") == "sentinel"
        assert captured["device_id"] == "d-1"

    def test_inventory_by_machine_delegates(self, make_endpoint, monkeypatch) -> None:
        monkeypatch.setattr(
            MachinesEndpoint, "_firmwareInventoryByMachine", lambda self: "sentinel"
        )
        assert (
            make_endpoint(FirmwareEndpoint).firmwareInventoryByMachine() == "sentinel"
        )

    def test_inventory_by_machine_files_delegates(
        self, make_endpoint, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_firmwareInventoryByMachineFiles",
            lambda self: "sentinel",
        )
        assert (
            make_endpoint(FirmwareEndpoint).firmwareInventoryByMachineFiles()
            == "sentinel"
        )


class TestDeviceAvHealth:
    def test_get_all_path(self, make_endpoint) -> None:
        result = make_endpoint(DeviceAVHealthEndpoint).get_all()
        assert isinstance(result, DeviceAVHealthResults)
        assert result._path == "/api/deviceAvInfo"

    def test_get_all_files_delegates(self, make_endpoint, monkeypatch) -> None:
        monkeypatch.setattr(
            MachinesEndpoint, "_infoGatheringExport", lambda self: "sentinel"
        )
        assert make_endpoint(DeviceAVHealthEndpoint).get_all_files() == "sentinel"
