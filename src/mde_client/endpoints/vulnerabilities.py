from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from .base import BaseEndpoint, BaseResults, BaseQuery
from ..schemas import (
    VULNERABILITY_SCHEMA,
    PUBLIC_ASSET_VULNERABILITY_DTO_SCHEMA,
    PUBLIC_VULNERABILITY_DTO_SCHEMA,
)

if TYPE_CHECKING:
    from .machines import MachineResults


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
        params = query.to_odata_filters if query else {}
        return VulnerabilityResults(self, params)

    def get(self, id: str) -> VulnerabilityResults:
        """Get a vulnerability by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-vulnerability-by-id
        """
        path = f"{self._PATH}/{id}"
        return VulnerabilityResults(self, {}, path=path, single=True)

    def machineReferences(self, id: str) -> MachineResults:
        """Get machine references for a vulnerability

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines-by-vulnerability
        """
        from .machines import MachineResults

        path = f"{self._PATH}/{id}/machinereferences"
        return MachineResults(self, {}, path=path)

    def machinesVulnerabilities(
        self, id: str
    ) -> VulnerabilitiesByMachineAndSoftwareResults:
        """Get machines with a vulnerability

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-all-vulnerabilities-by-machines
        """
        path = f"{self._PATH}/machinesVulnerabilities"
        return VulnerabilitiesByMachineAndSoftwareResults(self, {}, path=path)
