from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseEndpoint, BaseResults
from ..schemas import USER_SCHEMA

if TYPE_CHECKING:
    from .alerts import AlertsResults
    from .machines import MachineResults


class UserResults(BaseResults):
    """Results from the /api/users endpoint."""

    SCHEMA = USER_SCHEMA


class UserEndpoint(BaseEndpoint):
    """Endpoint for /api/users."""

    _PATH = "/api/users"

    def alerts(self, id: str) -> AlertsResults:
        """Get alerts related to a specific user.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-user-related-alerts
        """
        path = f"{self._PATH}/{id}/alerts"
        return AlertsResults(self, {}, path=path)

    def machines(self, id: str) -> MachineResults:
        """Get machines related to a specific user.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-user-related-machines
        """
        path = f"{self._PATH}/{id}/machines"
        return MachineResults(self, {}, path=path)
