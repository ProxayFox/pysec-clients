from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseEndpoint, BaseQuery, BaseResults

from ..schemas import (
    RECOMMENDATION_SCHEMA,
)
from ..models.enums import PUBLIC_RECOMMENDATION_EXCEPTION_STATUS


if TYPE_CHECKING:
    from .vulnerabilities import VulnerabilityDTOResults
    from .machines import MachineReferencesResults
    from .misc import ProductDTOResults


class RecommendationQuery(BaseQuery):
    """Query parameters for the /api/recommendations endpoint."""

    id: str | list[str] | None
    productName: str | list[str] | None
    vendor: str | list[str] | None
    recommendedVersion: str | list[str] | None
    recommendationCategory: str | list[str] | None
    subCategory: str | list[str] | None
    severityScore: int | list[int] | None
    remediationType: str | list[str] | None
    recommendedProgram: str | list[str] | None
    recommendedVendor: str | list[str] | None
    status: (
        PUBLIC_RECOMMENDATION_EXCEPTION_STATUS
        | list[PUBLIC_RECOMMENDATION_EXCEPTION_STATUS]
        | None
    )


class RecommendationResults(BaseResults):
    """Results from the /api/recommendations endpoint."""

    SCHEMA = RECOMMENDATION_SCHEMA


class RecommendationsEndpoint(BaseEndpoint):
    """Endpoint for /api/recommendations."""

    _PATH = "/api/recommendations"

    def get_all(
        self, query: RecommendationQuery | None = None
    ) -> RecommendationResults:
        """Get all recommendations matching the query parameters.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-all-recommendations
        """
        params = query.to_odata_filters if query else {}
        return RecommendationResults(self, params)

    def get(self, id: str) -> RecommendationResults:
        """Get a single recommendation by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-recommendation-by-id
        """
        path = f"{self._PATH}/{id}"
        return RecommendationResults(self, {}, path=path)

    def software(self, id: str) -> ProductDTOResults:
        """Get software details for a recommendation by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/list-recommendation-software
        """
        from .misc import ProductDTOResults

        path = f"{self._PATH}/{id}/software"
        return ProductDTOResults(self, {}, path=path)

    def machineReferences(self, id: str) -> MachineReferencesResults:
        """Get machine references for a recommendation by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/list-recommendation-machine-references
        """
        from .machines import MachineReferencesResults

        path = f"{self._PATH}/{id}/machinereferences"
        return MachineReferencesResults(self, {}, path=path)

    def vulnerabilities(self, id: str) -> VulnerabilityDTOResults:
        """Get vulnerability details for a recommendation by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/list-recommendation-vulnerabilities
        """
        path = f"{self._PATH}/{id}/vulnerabilities"
        return VulnerabilityDTOResults(self, {}, path=path)
