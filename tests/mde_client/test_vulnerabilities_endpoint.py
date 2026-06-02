"""Tests for VulnerabilityEndpoint request construction and delegation."""

from __future__ import annotations

from mde_client.endpoints.machines import MachineResults, MachinesEndpoint
from mde_client.endpoints.vulnerabilities import (
    VulnerabilitiesByMachineAndSoftwareResults,
    VulnerabilitiesQuery,
    VulnerabilityEndpoint,
    VulnerabilityResults,
)


class TestGetAll:
    def test_returns_results(self, make_endpoint) -> None:
        result = make_endpoint(VulnerabilityEndpoint).get_all()
        assert isinstance(result, VulnerabilityResults)
        assert result._path == "/api/vulnerabilities"
        assert result._single is False
        assert result._params["pageSize"] == "10000"

    def test_query_filter(self, make_endpoint) -> None:
        result = make_endpoint(VulnerabilityEndpoint).get_all(
            VulnerabilitiesQuery(severity="High")
        )
        assert result._params["pageSize"] == "10000"
        assert "severity eq 'High'" in result._params["$filter"]


class TestGet:
    def test_path_and_single(self, make_endpoint) -> None:
        result = make_endpoint(VulnerabilityEndpoint).get("CVE-2025-0001")
        assert result._path == "/api/vulnerabilities/CVE-2025-0001"
        assert result._single is True


class TestMachineReferences:
    def test_path(self, make_endpoint) -> None:
        result = make_endpoint(VulnerabilityEndpoint).machineReferences("CVE-2025-0001")
        assert isinstance(result, MachineResults)
        assert result._path == "/api/vulnerabilities/CVE-2025-0001/machinereferences"


class TestMachinesVulnerabilities:
    def test_path(self, make_endpoint) -> None:
        result = make_endpoint(VulnerabilityEndpoint).machinesVulnerabilities()
        assert isinstance(result, VulnerabilitiesByMachineAndSoftwareResults)
        assert result._path == "/api/vulnerabilities/machinesVulnerabilities"
        assert result._params["pageSize"] == "10000"


class TestDelegatedExports:
    def test_software_vulns_by_machine_delegates(
        self, make_endpoint, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_softwareVulnerabilitiesByMachine",
            lambda self, page_size=50000: "sentinel",
        )
        assert (
            make_endpoint(VulnerabilityEndpoint).softwareVulnerabilitiesByMachine()
            == "sentinel"
        )

    def test_software_vulns_by_machine_files_delegates(
        self, make_endpoint, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_softwareVulnerabilitiesExport",
            lambda self: "sentinel-files",
        )
        assert (
            make_endpoint(VulnerabilityEndpoint).softwareVulnerabilitiesByMachineFiles()
            == "sentinel-files"
        )

    def test_software_vuln_changes_by_machine_delegates(
        self, make_endpoint, monkeypatch
    ) -> None:
        monkeypatch.setattr(
            MachinesEndpoint,
            "_softwareVulnerabilityChangesByMachine",
            lambda self, page_size=50000, since=None: "sentinel-delta",
        )
        assert (
            make_endpoint(VulnerabilityEndpoint).softwareVulnerabilityChangesByMachine()
            == "sentinel-delta"
        )
