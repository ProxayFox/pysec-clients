from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from .base import BaseEndpoint, BaseResults, BaseQuery
from ..schemas import (
    VULNERABILITY_SCHEMA,
    ASSET_VULNERABILITY_SCHEMA,
    DELTA_ASSET_VULNERABILITY_SCHEMA,
    PUBLIC_ASSET_VULNERABILITY_DTO_SCHEMA,
    PUBLIC_VULNERABILITY_DTO_SCHEMA,
)

if TYPE_CHECKING:
    from .machines import MachineReferencesResults


class VulnerabilitiesQuery(BaseQuery):
    """Query parameters for the /api/vulnerabilities endpoint."""

    id: str | list[str] | None = None
    name: str | list[str] | None = None
    description: str | list[str] | None = None
    cvssV3: str | list[str] | None = None
    publishedOn: datetime | None = None
    severity: str | list[str] | None = None
    updatedOn: datetime | None = None


class VulnerabilitiesByMachineAndSoftwareQuery(BaseQuery):
    """Query parameters for the /api/vulnerabilities/machinesVulnerabilities endpoint."""

    id: str | list[str] | None = None
    cveId: str | list[str] | None = None
    machineId: str | list[str] | None = None
    fixingKbId: str | list[str] | None = None
    productName: str | list[str] | None = None
    productVersion: str | list[str] | None = None
    severity: str | list[str] | None = None
    productVendor: str | list[str] | None = None


class VulnerabilityResults(BaseResults):
    """Results from the /api/vulnerabilities endpoint."""

    SCHEMA = VULNERABILITY_SCHEMA


class AssetVulnerabilityResults(BaseResults):
    """Results from the /api/machines/SoftwareVulnerabilitiesByMachine endpoint."""

    SCHEMA = ASSET_VULNERABILITY_SCHEMA


class DeltaAssetVulnerabilityResults(BaseResults):
    """Results from the /api/machines/SoftwareVulnerabilityChangesByMachine endpoint with delta query parameters."""

    SCHEMA = DELTA_ASSET_VULNERABILITY_SCHEMA


class VulnerabilitiesByMachineAndSoftwareResults(BaseResults):
    """Results from the /api/vulnerabilities/machinesVulnerabilities endpoint."""

    SCHEMA = PUBLIC_ASSET_VULNERABILITY_DTO_SCHEMA


class VulnerabilityDTOResults(BaseResults):
    """Results from the /api/machines/{id}/vulnerabilities endpoint."""

    SCHEMA = PUBLIC_VULNERABILITY_DTO_SCHEMA


class VulnerabilityEndpoint(BaseEndpoint):
    """Endpoint for /api/vulnerabilities."""

    _PATH = "/api/vulnerabilities"

    def get_all(
        self, query: VulnerabilitiesQuery | None = None
    ) -> VulnerabilityResults:
        """Get all vulnerabilities.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-all-vulnerabilities
        """
        if query is None:
            query = VulnerabilitiesQuery()
        params = query.to_odata_filters
        return VulnerabilityResults(self, params, use_concurrent_skip_pagination=True)

    def get(self, id: str) -> VulnerabilityResults:
        """Get a vulnerability by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-vulnerability-by-id
        """
        path = f"{self._PATH}/{id}"
        return VulnerabilityResults(self, {}, path=path, single=True)

    def machineReferences(self, id: str) -> MachineReferencesResults:
        """Get machine references from a Vulnerability CVE ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines-by-vulnerability
        """
        from .machines import MachineReferencesResults

        path = f"{self._PATH}/{id}/machinereferences"
        return MachineReferencesResults(self, {}, path=path)

    def machinesVulnerabilities(
        self, query: VulnerabilitiesByMachineAndSoftwareQuery | None = None
    ) -> VulnerabilitiesByMachineAndSoftwareResults:
        """Get machines with a vulnerability

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-all-vulnerabilities-by-machines
        """
        path = f"{self._PATH}/machinesVulnerabilities"
        if query is None:
            query = VulnerabilitiesByMachineAndSoftwareQuery()
        params = query.to_odata_filters
        return VulnerabilitiesByMachineAndSoftwareResults(
            self,
            params,
            path=path,
            use_concurrent_skip_pagination=True,
            skip_page_size=10000,
        )

    def softwareVulnerabilitiesByMachine(
        self, page_size: int = 50000
    ) -> AssetVulnerabilityResults:
        """Get vulnerabilities for a machine with software references.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-software-vulnerabilities
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-software-vulnerabilities#1-export-software-vulnerabilities-assessment-json-response
        """
        from .machines import MachinesEndpoint

        return MachinesEndpoint(
            self._http, self._auth
        )._softwareVulnerabilitiesByMachine(page_size)

    def softwareVulnerabilitiesByMachineFiles(self) -> AssetVulnerabilityResults:
        """Get vulnerabilities for a machine with software references.

        Same Results as `softwareVulnerabilitiesByMachine` but exported as a file instead of in the response body.
        Recommended for larger data sets, as it returns zipped files with the data instead of returning it in the response body.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-software-vulnerabilities
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-software-vulnerabilities#2-export-software-vulnerabilities-assessment-via-files
        """
        from .machines import MachinesEndpoint

        return MachinesEndpoint(self._http, self._auth)._softwareVulnerabilitiesExport()

    def softwareVulnerabilityChangesByMachine(
        self, page_size: int = 50000, since: datetime | int | str | None = None
    ) -> DeltaAssetVulnerabilityResults:
        """Get vulnerabilities for a machine with software references.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-software-vulnerabilities
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-software-vulnerabilities#3-delta-export-software-vulnerabilities-assessment-json-response
        """
        from .machines import MachinesEndpoint

        return MachinesEndpoint(
            self._http, self._auth
        )._softwareVulnerabilityChangesByMachine(page_size, since)
