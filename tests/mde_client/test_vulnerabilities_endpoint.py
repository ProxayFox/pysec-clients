"""Tests for VulnerabilityEndpoint request construction and delegation."""

from __future__ import annotations

from mde_client.endpoints.machines import MachinesEndpoint, MachineReferencesResults
from mde_client.endpoints.vulnerabilities import (
    VulnerabilitiesByMachineAndSoftwareQuery,
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
        assert isinstance(result, MachineReferencesResults), (
            f"{result} is not a MachineReferencesResults"
        )
        assert result._path == "/api/vulnerabilities/CVE-2025-0001/machinereferences"


class TestMachinesVulnerabilities:
    def test_path(self, make_endpoint) -> None:
        result = make_endpoint(VulnerabilityEndpoint).machinesVulnerabilities()
        assert isinstance(result, VulnerabilitiesByMachineAndSoftwareResults)
        assert result._path == "/api/vulnerabilities/machinesVulnerabilities"
        assert result._params["pageSize"] == "10000"

    def test_query_filter(self, make_endpoint) -> None:
        result = make_endpoint(VulnerabilityEndpoint).machinesVulnerabilities(
            VulnerabilitiesByMachineAndSoftwareQuery(
                cveId="CVE-2025-0001", severity="High"
            )
        )

        assert result._params["pageSize"] == "10000"
        assert "cveId eq 'CVE-2025-0001'" in result._params["$filter"]
        assert "severity eq 'High'" in result._params["$filter"]
        assert result._use_concurrent_skip_pagination is True
        assert result._skip_page_size == 10000

    def test_list_query_filter(self, make_endpoint) -> None:
        result = make_endpoint(VulnerabilityEndpoint).machinesVulnerabilities(
            VulnerabilitiesByMachineAndSoftwareQuery(
                cveId=["CVE-2025-0001", "CVE-2025-0002"],
                productName=["Windows", "Edge"],
            )
        )

        assert (
            "cveId in ('CVE-2025-0001', 'CVE-2025-0002')" in result._params["$filter"]
        )
        assert "productName in ('Windows', 'Edge')" in result._params["$filter"]


class TestDelegatedExports:
    def test_software_vulns_by_machine_delegates(
        self, make_endpoint, monkeypatch
    ) -> None:
        captured: dict[str, int] = {}

        def fake_software_vulnerabilities_by_machine(
            self, page_size: int = 50000
        ) -> str:
            captured["page_size"] = page_size
            return "sentinel"

        monkeypatch.setattr(
            MachinesEndpoint,
            "_softwareVulnerabilitiesByMachine",
            fake_software_vulnerabilities_by_machine,
        )
        assert (
            make_endpoint(VulnerabilityEndpoint).softwareVulnerabilitiesByMachine(
                page_size=25000
            )
            == "sentinel"
        )
        assert captured == {"page_size": 25000}

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
        captured: dict[str, int | str | None] = {}

        def fake_software_vulnerability_changes_by_machine(
            self, page_size: int = 50000, since: int | str | None = None
        ) -> str:
            captured["page_size"] = page_size
            captured["since"] = since
            return "sentinel-delta"

        monkeypatch.setattr(
            MachinesEndpoint,
            "_softwareVulnerabilityChangesByMachine",
            fake_software_vulnerability_changes_by_machine,
        )
        assert (
            make_endpoint(VulnerabilityEndpoint).softwareVulnerabilityChangesByMachine(
                page_size=25000,
                since="2026-06-01",
            )
            == "sentinel-delta"
        )
        assert captured == {"page_size": 25000, "since": "2026-06-01"}
