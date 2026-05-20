"""Tests for MachinesEndpoint sub-resource lookups and helper construction."""

from __future__ import annotations

from datetime import datetime, timezone

from mde_client.endpoints.machines import (
    MachineResults,
    MachinesEndpoint,
)
from mde_client.endpoints.alerts import AlertsResults
from mde_client.endpoints.recommendations import RecommendationResults
from mde_client.endpoints.software import SoftwareResults
from mde_client.endpoints.users import UserResults
from mde_client.endpoints.vulnerabilities import VulnerabilityDTOResults
from mde_client.endpoints.misc import ProductDTOResults
from mde_client.models.action_payloads import (
    AddOrRemoveTagForMultipleMachinesPayload,
)


class TestSubResourceLookups:
    def test_logonusers(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).logonusers("m-1")
        assert isinstance(r, UserResults)
        assert r._path == "/api/machines/m-1/logonusers"

    def test_alerts(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).alerts("m-1")
        assert isinstance(r, AlertsResults)
        assert r._path == "/api/machines/m-1/alerts"

    def test_software(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).software("m-1")
        assert isinstance(r, SoftwareResults)
        assert r._path == "/api/machines/m-1/software"

    def test_vulnerabilities(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).vulnerabilities("m-1")
        assert isinstance(r, VulnerabilityDTOResults)
        assert r._path == "/api/machines/m-1/vulnerabilities"

    def test_recommendations(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).recommendations("m-1")
        assert isinstance(r, RecommendationResults)
        assert r._path == "/api/machines/m-1/recommendations"

    def test_getmissingkbs(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).getmissingkbs("m-1")
        assert isinstance(r, ProductDTOResults)
        assert r._path == "/api/machines/m-1/getmissingkbs"


class TestQueryHelpers:
    def test_bigpagesize_path(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).bigPageSize()
        assert isinstance(r, MachineResults)
        assert r._path == "/api/machines/bigPageSize"

    def test_get_single_path(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).get("m-1")
        assert r._single is True
        assert r._path == "/api/machines/m-1"

    def test_untagged_path(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).unTaggedMachines()
        assert r._path == "/api/machines/unTaggedMachines"

    def test_findbytag_default_filter(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).findbytag("prod")
        assert r._path == "/api/machines/findbytag"
        assert r._params == {"tag": "prod", "useStartsWithFilter": "false"}

    def test_findbytag_starts_with(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint).findbytag("env-", useStartsWithFilter=True)
        assert r._params["useStartsWithFilter"] == "true"

    def test_findbyip_serializes_timestamp(self, make_endpoint) -> None:
        ts = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        r = make_endpoint(MachinesEndpoint).findbyip("10.0.0.1", ts)
        assert (
            "/api/machines/findbyip(ip='10.0.0.1',timestamp=2025-01-02T03:04:05Z)"
            == r._path
        )

    def test_findbyip_naive_timestamp_assumed_utc(self, make_endpoint) -> None:
        ts = datetime(2025, 1, 2, 3, 4, 5)
        r = make_endpoint(MachinesEndpoint).findbyip("10.0.0.1", ts)
        assert "timestamp=2025-01-02T03:04:05Z" in r._path


class TestMutations:
    def test_add_or_remove_tag_post_body(self, make_endpoint) -> None:
        payload = AddOrRemoveTagForMultipleMachinesPayload(
            MachineIds=["m-1", "m-2"], Action="Add", Value="prod"
        )
        r = make_endpoint(MachinesEndpoint).addOrRemoveTagForMultipleMachines(payload)
        assert r._path == "/api/machines/addOrRemoveTagForMultipleMachines"
        assert r._method == "POST"
        assert r._request_kwargs["json"] == payload.model_dump()


class TestExportFileHelpers:
    """Coverage for the internal export-file path constants."""

    def test_browser_extension_inventory_path(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint)._browserExtensionsInventoryByMachine()
        assert r._path.endswith("/BrowserExtensionsInventoryByMachine")
        assert r._files is False

    def test_browser_extension_export_files(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint)._browserextensionsinventoryExport()
        assert r._files is True

    def test_certificate_assessment(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint)._certificateAssessmentByMachine()
        assert r._path.endswith("/certificateAssessmentByMachine")

    def test_certificate_assessment_export(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint)._certificateAssessmentExport()
        assert r._files is True

    def test_info_gathering_export(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint)._infoGatheringExport()
        assert r._files is True

    def test_device_firmware(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint)._deviceFirmware("m-1")
        assert r._path == "/api/machines/m-1/firmware"

    def test_firmware_inventory(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint)._firmwareInventoryByMachine()
        assert r._path.endswith("/hardwareFirmwareInventoryByMachine")

    def test_firmware_inventory_files(self, make_endpoint) -> None:
        r = make_endpoint(MachinesEndpoint)._firmwareInventoryByMachineFiles()
        assert r._files is True
