from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseEndpoint, BaseResults
from ..schemas import DOMAIN_SCHEMA, IN_ORG_DOMAIN_STATS_SCHEMA

if TYPE_CHECKING:
    from .alerts import AlertsResults
    from .machines import MachineResults


class DomainResults(BaseResults):
    """Results for the /api/domains endpoint."""

    SCHEMA = DOMAIN_SCHEMA


class DomainStatsResults(BaseResults):
    """Results for the /api/alerts/{id}/domains/stats endpoint."""

    SCHEMA = IN_ORG_DOMAIN_STATS_SCHEMA


class DomainEndpoint(BaseEndpoint):
    """Endpoint for interacting with alert-related domain information."""

    _PATH = "/api/domains"

    def alerts(self, domain: str) -> AlertsResults:
        """Get the alerts associated with a domain.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-domain-related-alerts
        """
        from .alerts import AlertsResults

        path = f"{self._PATH}/{domain}/alerts"
        return AlertsResults(self, {}, path=path)

    def machines(self, domain: str) -> MachineResults:
        """Get the machines associated with a domain.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-domain-related-machines
        """
        from .machines import MachineResults

        path = f"{self._PATH}/{domain}/machines"
        return MachineResults(self, {}, path=path)

    def stats(self, domain: str) -> DomainStatsResults:
        """Get the in-organization stats for a domain.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-domain-statistics
        """
        path = f"{self._PATH}/{domain}/stats"
        return DomainStatsResults(self, {}, path=path)
