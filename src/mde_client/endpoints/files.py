from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseEndpoint, BaseResults
from ..schemas import FILE_SCHEMA, IN_ORG_FILE_STATS_SCHEMA

if TYPE_CHECKING:
    from .alerts import AlertsResults
    from .machines import MachineResults


class FileResults(BaseResults):
    """Results for the /api/files/{id} endpoint."""

    SCHEMA = FILE_SCHEMA


class FileStatsResults(BaseResults):
    """Results for the /api/files/{id}/stats endpoint."""

    SCHEMA = IN_ORG_FILE_STATS_SCHEMA


class FileEndpoint(BaseEndpoint):
    """Endpoint for interacting with file information."""

    _PATH = "/api/files"

    def get(self, hash: str) -> FileResults:
        """Get information about a file by its ID (hash).

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-file-information
        """
        path = f"{self._PATH}/{hash}"
        return FileResults(self, {}, path=path)

    def alerts(self, hash: str) -> AlertsResults:
        """Get the alerts associated with a file.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-file-related-alerts
        """
        from .alerts import AlertsResults

        path = f"{self._PATH}/{hash}/alerts"
        return AlertsResults(self, {}, path=path)

    def machines(self, hash: str) -> MachineResults:
        """Get the machines associated with a file.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-file-related-machines
        """
        from .machines import MachineResults

        path = f"{self._PATH}/{hash}/machines"
        return MachineResults(self, {}, path=path)

    def stats(self, hash: str) -> FileStatsResults:
        """Get the in-organization stats for a file.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-file-statistics
        """
        path = f"{self._PATH}/{hash}/stats"
        return FileStatsResults(self, {}, path=path)
