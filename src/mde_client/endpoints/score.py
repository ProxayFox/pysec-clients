from __future__ import annotations


from .base import BaseEndpoint, BaseResults
from ..schemas import CONFIGURATION_SCORE_SCHEMA


class ScoreResults(BaseResults):
    """Results from the /api/exposureScore endpoint."""

    SCHEMA = CONFIGURATION_SCORE_SCHEMA


class ScoreEndpoint(BaseEndpoint):
    """Endpoint for /api/exposureScore."""

    _PATH = "/api/exposureScore"

    def get(self) -> ScoreResults:
        """Get the current configuration score."""
        return ScoreResults(self, {})

    def byMachineGroups(self) -> ScoreResults:
        """Get the current configuration score by machine groups."""
        path = f"{self._PATH}/ByMachineGroups"
        return ScoreResults(self, {}, path=path)

    def configurationScore(self) -> ScoreResults:
        """Alias for get()."""
        path = "/api/configurationScore"
        return ScoreResults(self, {}, path=path)
