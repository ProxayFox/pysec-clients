"""Tests for SoftwareEndpoint request construction and delegation."""

from __future__ import annotations

from mde_client.endpoints.machines import MachineReferencesResults, MachinesEndpoint
from mde_client.endpoints.misc import ProductDTOResults
from mde_client.endpoints.software import (
    DistributionDTOResults,
    SoftwareEndpoint,
    SoftwareQuery,
    SoftwareResults,
)
from mde_client.endpoints.vulnerabilities import VulnerabilityDTOResults


class TestGetAll:
    def test_path(self, make_endpoint) -> None:
        result = make_endpoint(SoftwareEndpoint).get_all()
        assert isinstance(result, SoftwareResults)
        assert result._path == "/api/Software"

    def test_query_filter(self, make_endpoint) -> None:
        result = make_endpoint(SoftwareEndpoint).get_all(SoftwareQuery(vendor="msft"))
        assert "vendor eq 'msft'" in result._params["$filter"]


class TestGet:
    def test_path(self, make_endpoint) -> None:
        result = make_endpoint(SoftwareEndpoint).get("sw-1")
        assert result._path == "/api/Software/sw-1"


class TestSubResources:
    def test_distributions(self, make_endpoint) -> None:
        result = make_endpoint(SoftwareEndpoint).distributions("sw-1")
        assert isinstance(result, DistributionDTOResults)
        assert result._path == "/api/Software/sw-1/distributions"

    def test_machine_references(self, make_endpoint) -> None:
        result = make_endpoint(SoftwareEndpoint).machineReferences("sw-1")
        assert isinstance(result, MachineReferencesResults)
        assert result._path == "/api/Software/sw-1/machineReferences"

    def test_vulnerabilities(self, make_endpoint) -> None:
        result = make_endpoint(SoftwareEndpoint).vulnerabilities("sw-1")
        assert isinstance(result, VulnerabilityDTOResults)
        assert result._path == "/api/Software/sw-1/vulnerabilities"

    def test_missing_kbs(self, make_endpoint) -> None:
        result = make_endpoint(SoftwareEndpoint).getmissingkbs("sw-1")
        assert isinstance(result, ProductDTOResults)
        assert result._path == "/api/Software/sw-1/getmissingkbs"


class TestDelegation:
    def test_inventory_by_machine_delegates(self, make_endpoint, monkeypatch) -> None:
        captured: dict[str, int] = {}

        def fake(self: MachinesEndpoint, *, page_size: int):
            captured["page_size"] = page_size
            return "sentinel"

        monkeypatch.setattr(MachinesEndpoint, "_softwareInventoryByMachine", fake)
        result = make_endpoint(SoftwareEndpoint).inventoryByMachine(page_size=123)
        assert result == "sentinel"
        assert captured["page_size"] == 123

    def test_inventory_by_machine_files_delegates(
        self, make_endpoint, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            MachinesEndpoint, "_softwareInventoryExport", lambda self: "sentinel"
        )
        assert make_endpoint(SoftwareEndpoint).inventoryByMachineFiles() == "sentinel"

    def test_inventory_no_cpe_delegates(self, make_endpoint, monkeypatch) -> None:
        captured: dict[str, object] = {}

        def fake(self: MachinesEndpoint, *, page_size: int, since):
            captured["page_size"] = page_size
            captured["since"] = since
            return "sentinel"

        monkeypatch.setattr(
            MachinesEndpoint, "_softwareInventoryNoProductCodeByMachine", fake
        )
        result = make_endpoint(SoftwareEndpoint).inventoryNoProductCodeByMachine(
            page_size=99, since=7
        )
        assert result == "sentinel"
        assert captured == {"page_size": 99, "since": 7}

    def test_inventory_no_cpe_files_delegates(self, make_endpoint, monkeypatch) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_softwareInventoryNonCpeExport",
            lambda self: "sentinel",
        )
        assert (
            make_endpoint(SoftwareEndpoint).inventoryNoProductCodeByMachineFiles()
            == "sentinel"
        )
