from __future__ import annotations


from .base import BaseEndpoint, BaseResults
from ..schemas import IN_ORG_DOMAIN_STATS_SCHEMA, MACHINE_SCHEMA, ALERT_SCHEMA


class DomainAlertsResults(BaseResults):
    """Results for the /api/alerts/{id}/domains endpoint."""

    SCHEMA = ALERT_SCHEMA


class DomainMachinesResults(BaseResults):
    """Results for the /api/alerts/{id}/domains/{domain}/machines endpoint."""

    SCHEMA = MACHINE_SCHEMA


class DomainStatsResults(BaseResults):
    """Results for the /api/alerts/{id}/domains/stats endpoint."""

    SCHEMA = IN_ORG_DOMAIN_STATS_SCHEMA


class DomainEndpoint(BaseEndpoint):
    """Endpoint for interacting with alert-related domain information."""

    _PATH = "/api/domains"

    def alerts(self, domain: str) -> DomainAlertsResults:
        """Get the alerts associated with a domain.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-domain-related-alerts
        """
        path = f"{self._PATH}/{domain}/alerts"
        return DomainAlertsResults(self, {}, path=path)

    def machines(self, domain: str) -> DomainMachinesResults:
        """Get the machines associated with a domain.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-domain-related-machines
        """
        path = f"{self._PATH}/{domain}/machines"
        return DomainMachinesResults(self, {}, path=path)

    def stats(self, domain: str) -> DomainStatsResults:
        """Get the in-organization stats for a domain.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-domain-statistics
        """
        path = f"{self._PATH}/{domain}/stats"
        return DomainStatsResults(self, {}, path=path)
