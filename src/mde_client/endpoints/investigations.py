from __future__ import annotations

import logging

from datetime import datetime, timezone
from typing import Literal, TYPE_CHECKING

from .base import BasePayload, BaseQuery, BaseEndpoint, BaseResults
from ..schemas import INVESTIGATION_SCHEMA
from .machines import MachinesEndpoint

STATE_TYPE = Literal[
    "Unknown", 
    "Terminated", 
    "SuccessfullyRemediated", 
    "Benign", 
    "Failed", 
    "PartiallyRemediated", 
    "Running", 
    "PendingApproval", 
    "PendingResource", 
    "PartiallyInvestigated", 
    "TerminatedByUser", 
    "TerminatedBySystem", 
    "Queued", 
    "InnerFailure", 
    "PreexistingAlert", 
    "UnsupportedOs", 
    "UnsupportedAlertType", 
    "SuppressedAlert"
]

class InvestigationsQuery(BaseQuery):
    """Query parameters for the /api/investigations endpoint.

    All fields are optional — omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Example:
    ```python
    query = InvestigationsQuery(status="Active", pageSize=500)
    query = InvestigationsQuery(severity=["Medium", "High"], pageSize=500)
    ```
    """

    id: str | list[str] | None = None
    startTime: datetime | None = None
    state: STATE_TYPE | list[STATE_TYPE] | None = None
    machineId: str | list[str] | None = None
    triggeringAlertId: str | list[str] | None = None

class InvestigationStartPayload(BasePayload):
    """Payload for starting an investigation."""

    machineId: str
    Comment: str
    ExternalId: str | None = None
    RequestSource: str | None = None
    Title: str | None = None

class InvestigationResults(BaseResults):
    """Results from the /api/investigations endpoint."""

    SCHEMA = INVESTIGATION_SCHEMA
    
class InvestigationsEndpoint(BaseEndpoint):
    """Endpoint for /api/investigations"""

    _PATH = "/api/investigations"

    def get_all(self, query: InvestigationsQuery | None = None) -> InvestigationResults:
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
    
    def startInvestigation(self, deviceId: str) -> None:
        """Start an investigation.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/initiate-autoir-investigation
        """
                
