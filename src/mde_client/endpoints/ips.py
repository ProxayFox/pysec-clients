from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseEndpoint, BaseResults
from ..schemas import IP_SCHEMA, IN_ORG_IP_STATS_SCHEMA

if TYPE_CHECKING:
    from .alerts import AlertsResults


class IPResults(BaseResults):
    """Results from the /api/ips endpoint."""

    SCHEMA = IP_SCHEMA


class InOrgIPStatsResults(BaseResults):
    """Results from the /api/ips/{ip}/stats endpoint."""

    SCHEMA = IN_ORG_IP_STATS_SCHEMA


class IPEndpoint(BaseEndpoint):
    """Endpoint for /api/ips"""

    _PATH = "/api/ips"

    def alerts(self, ip: str) -> AlertsResults:
        """Get alerts related to a specific IP address.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-ip-related-alerts
        """
        path = f"{self._PATH}/{ip}/alerts"
        return AlertsResults(self, {}, path=path)

    def stats(self, ip: str) -> InOrgIPStatsResults:
        """Get stats for a specific IP address.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-ip-stats
        """
        path = f"{self._PATH}/{ip}/stats"
        return InOrgIPStatsResults(self, {}, path=path)
