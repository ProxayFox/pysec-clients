from __future__ import annotations

from ..schemas import CONFIGURATION_SCORE_SCHEMA
from .base import BaseEndpoint, BaseResults


class ScoreResults(BaseResults):
    """Results from the /api/exposureScore endpoint."""

    SCHEMA = CONFIGURATION_SCORE_SCHEMA


class ScoreEndpoint(BaseEndpoint):
    """Endpoint for /api/exposureScore."""

    _PATH = "/api/exposureScore"

    def get(self) -> ScoreResults:
        """Retrieves the organizational exposure score.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-exposure-score
        """
        return ScoreResults(self, {}, single=True)

    def byMachineGroups(self) -> ScoreResults:
        """Retrieves the exposure score for each machine group.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-group-exposure-score
        """
        path = f"{self._PATH}/ByMachineGroups"
        return ScoreResults(self, {}, path=path)

    def configurationScore(self) -> ScoreResults:
        """Retrieves Microsoft Secure Score for Devices.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-device-secure-score
        """
        path = "/api/configurationScore"
        return ScoreResults(self, {}, path=path)

    def configurationScoreById(self, id: str) -> ScoreResults:
        """Retrieves Microsoft Secure Score for Devices by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-device-secure-score
        """
        path = f"/api/configurationScore/{id}"
        return ScoreResults(self, {}, path=path)
