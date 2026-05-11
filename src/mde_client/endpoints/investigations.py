from __future__ import annotations

from datetime import datetime

from .base import BaseQuery, BaseEndpoint, BaseResults
from .machines import MachinesEndpoint
from ..schemas import INVESTIGATION_SCHEMA
from ..models.enums import INVESTIGATION_STATE
from ..models.action_payloads import StartInvestigationPayload


class InvestigationQuery(BaseQuery):
    """Query parameters for the /api/investigations endpoint.

    All fields are optional — omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Example:
    ```python
    query = InvestigationQuery(status="Active", pageSize=500)
    query = InvestigationQuery(severity=["Medium", "High"], pageSize=500)
    ```
    """

    id: str | list[str] | None = None
    startTime: datetime | None = None
    state: INVESTIGATION_STATE | list[INVESTIGATION_STATE] | None = None
    machineId: str | list[str] | None = None
    triggeringAlertId: str | list[str] | None = None


class InvestigationResults(BaseResults):
    """Results from the /api/investigations endpoint."""

    SCHEMA = INVESTIGATION_SCHEMA


class InvestigationsEndpoint(BaseEndpoint):
    """Endpoint for /api/investigations"""

    _PATH = "/api/investigations"

    def get_all(self, query: InvestigationQuery | None = None) -> InvestigationResults:
        """Get investigations with optional filters.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-investigations
        """
        params = query.to_odata_filters if query else {}
        return InvestigationResults(self, params)

    def get(self, id: str) -> InvestigationResults:
        """Get a specific investigation by ID.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-investigation-by-id
        """
        path = f"{self._PATH}/{id}"
        return InvestigationResults(self, {}, path=path, single=True)

    def startInvestigation(
        self, deviceId: str, payload: StartInvestigationPayload | None = None
    ) -> InvestigationResults:
        """Start an investigation.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/initiate-autoir-investigation
        """
        return MachinesEndpoint(self._http, self._auth)._startInvestigation(
            deviceId, payload
        )
