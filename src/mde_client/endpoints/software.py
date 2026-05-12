from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseEndpoint, BaseResults, BaseQuery
from ..schemas import (
    SOFTWARE_SCHEMA,
    PUBLIC_DISTRIBUTION_DTO_SCHEMA,
)

if TYPE_CHECKING:
    from .machines import MachineReferencesResults
    from .vulnerabilities import VulnerabilityDTOResults
    from .misc import ProductDTOResults


class SoftwareQuery(BaseQuery):
    """Query parameters for the /api/Software endpoint."""

    id: str | list[str] | None = None
    name: str | list[str] | None = None
    vendor: str | list[str] | None = None


class SoftwareResults(BaseResults):
    """Results from the /api/Software endpoint."""

    SCHEMA = SOFTWARE_SCHEMA


class DistributionDTOResults(BaseResults):
    """Results from the /api/Software/{id}/distributions endpoint."""

    SCHEMA = PUBLIC_DISTRIBUTION_DTO_SCHEMA


class SoftwareEndpoint(BaseEndpoint):
    """Endpoint for /api/Software."""

    _PATH = "/api/Software"

    def get_all(self, query: SoftwareQuery | None = None) -> SoftwareResults:
        """Get all software inventory records.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-software
        """
        params = query.to_odata_filters if query else {}
        return SoftwareResults(self, params)

    def get(self, id: str) -> SoftwareResults:
        """Get a specific software inventory record by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-software-by-id
        """
        path = f"{self._PATH}/{id}"
        return SoftwareResults(self, {}, path=path)

    def distributions(self, id: str) -> DistributionDTOResults:
        """Get software distribution records for a specific software inventory record.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-software-ver-distribution
        """
        path = f"{self._PATH}/{id}/distributions"
        return DistributionDTOResults(self, {}, path=path)

    def machineReferences(self, id: str) -> MachineReferencesResults:
        """Get machine references for a specific software inventory record.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines-by-software
        """
        path = f"{self._PATH}/{id}/machineReferences"
        return MachineReferencesResults(self, {}, path=path)

    def vulnerabilities(self, id: str) -> VulnerabilityDTOResults:
        """Get vulnerability records for a specific software inventory record.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-vuln-by-software
        """
        path = f"{self._PATH}/{id}/vulnerabilities"
        return VulnerabilityDTOResults(self, {}, path=path)

    def getmissingkbs(self, id: str) -> ProductDTOResults:
        """Get missing KBs for a specific software inventory record.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-missing-kbs-software
        """
        from .misc import ProductDTOResults

        path = f"{self._PATH}/{id}/getmissingkbs"
        return ProductDTOResults(self, {}, path=path)
