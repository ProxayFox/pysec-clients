from __future__ import annotations

from ..schemas import INCIDENT_SCHEMA
from .base import BaseEndpoint, BaseResults


class IncidentResults(BaseResults):
    """Results from the /api/incidents endpoint."""

    SCHEMA = INCIDENT_SCHEMA


class IncidentsEndpoint(BaseEndpoint):
    """Endpoint for /api/incidents."""

    _PATH = "/api/incidents"

    def get_all(self) -> IncidentResults:
        """Get all incidents.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-incidents
        """
        return IncidentResults(self, {})

    def get(self, id: str) -> IncidentResults:
        """Get a single incident by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-incident-by-id
        """
        path = f"{self._PATH}/{id}"
        return IncidentResults(self, {}, path=path, single=True)
