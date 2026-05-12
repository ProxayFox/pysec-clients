"""Microsoft Defender for Endpoint alerts endpoint models and client surface.

This module defines:
- `AlertsQuery`, `AlertCreateQuery`, and `AlertUpdateQuery` request models.
- `*Results` wrappers mapped to Arrow schemas for alerts and related entities.
- `AlertsEndpoint` methods for retrieving alerts and related domains, files,
  IPs, machines, and users.

Most endpoint methods return lazy `BaseResults` subclasses and defer HTTP
requests until a terminal materialization method is called. Create/update
operations are declared but currently marked as not implemented.

Note: Needs further Testing and implementation of POST methods for alert creation and updates.

**Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/alerts
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .base import BaseEndpoint, BaseQuery, BaseResults
from ..schemas import (
    ALERT_SCHEMA,
    IP_SCHEMA,
    USER_SCHEMA,
)
from ..models.enums import (
    ALERT_SEVERITY,
    ALERT_STATUS,
    IOA_CATEGORY,
)
from ..models.action_payloads import (
    CreateAlertByReferencePayload,
    BatchUpdateAlertPayload,
)

if TYPE_CHECKING:
    from .domain import DomainResults
    from .files import FileResults
    from .machines import MachineResults

log = logging.getLogger(__name__)


class AlertsQuery(BaseQuery):
    """Query parameters for the /api/alerts endpoint.

    Example:
    ```python
        query = AlertsQuery(severity="Medium", pageSize=500)
        query = AlertsQuery(severity=["Medium", "High"], pageSize=500)
    ```
    """

    id: str | list[str] | None = None
    alertCreationTime: datetime | None = None
    lastUpdateTime: datetime | None = None
    incidentId: int | list[int] | None = None
    InvestigationId: int | list[int] | None = None
    assignedTo: str | list[str] | None = None
    detectionSource: str | list[str] | None = None
    lastEventTime: datetime | None = None
    status: ALERT_STATUS | list[ALERT_STATUS] | None = None
    severity: ALERT_SEVERITY | list[ALERT_SEVERITY] | None = None
    category: str | list[str] | None = None


class AlertCreateQuery(BaseQuery):
    """Query parameters for creating an alert by reference. **All fields are required.**

    Example:
    ```python
        query = AlertCreateQuery(referenceId="12345", referenceType="CustomReference" ... , category="Malware")
    ```
    """

    eventTime: datetime
    reportId: str
    machineId: str

    severity: ALERT_STATUS
    title: str
    description: str
    recommendedAction: str
    category: IOA_CATEGORY

    def model_post_init(self, __context: Any) -> None:
        """Validate that the category is not 'Unknown' because alert creation does not allow 'Unknown' category."""
        if "Unknown" in self.category:
            raise ValueError(
                "Category cannot be 'Unknown'. Please choose a valid category."
            )


class AlertsResults(BaseResults):
    """Results from the /api/alerts endpoint."""

    SCHEMA = ALERT_SCHEMA


class IPResults(BaseResults):
    """Results from the /api/alerts/{id}/ips endpoint.

    TODO: Move to ips.py once the endpoint is setup
    """

    SCHEMA = IP_SCHEMA


class UserResults(BaseResults):
    """Results from the /api/alerts/{id}/user endpoint.

    TODO: Move to users.py once the endpoint is setup
    """

    SCHEMA = USER_SCHEMA


class AlertsEndpoint(BaseEndpoint):
    """Client for the /api/alerts endpoint.

    Methods:
        - get_all: Get all alerts matching the query parameters.
        - get: Get a single alert by ID.
        - domains: Get the domains associated with an alert.
        - files: Get the files associated with an alert.
        - ips: Get the IPs associated with an alert.
        - machines: Get the machines associated with an alert.
        - user: Get the user associated with an alert.
        - createAlertByReference: Create an alert by reference.
        - batchUpdate: Batch update alerts.
        - update: Update alerts (alias for batch update).
    """

    _PATH = "/api/alerts"

    def get_all(self, query: AlertsQuery | None = None) -> AlertsResults:
        """Get all alerts matching the query parameters.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-alerts
        """
        params = query.to_odata_filters if query else {}
        return AlertsResults(self, params)

    def get(self, id: str) -> AlertsResults:
        """Get a single alert by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-alert-info-by-id
        """
        path = f"{self._PATH}/{id}"
        return AlertsResults(self, {}, path=path, single=True)

    def domains(self, id: str) -> DomainResults:
        """Get the domains associated with an alert.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-alert-related-domain-info
        """
        from .domain import DomainResults

        path = f"{self._PATH}/{id}/domains"
        return DomainResults(self, {}, path=path)

    def files(self, id: str) -> FileResults:
        """Get the files associated with an alert.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-alert-related-files-info
        """
        from .files import FileResults

        path = f"{self._PATH}/{id}/files"
        return FileResults(self, {}, path=path)

    def ips(self, id: str) -> IPResults:
        """Get the IPs associated with an alert.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-alert-related-ip-info
        """
        path = f"{self._PATH}/{id}/ips"
        return IPResults(self, {}, path=path)

    def machines(self, id: str) -> MachineResults:
        """Get the machines associated with an alert.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-alert-related-machine-info
        """
        from .machines import MachineResults

        path = f"{self._PATH}/{id}/machines"
        return MachineResults(self, {}, path=path)

    def user(self, id: str) -> UserResults:
        """Get the user associated with an alert.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-alert-related-user-info
        """
        path = f"{self._PATH}/{id}/user"
        return UserResults(self, {}, path=path)

    def createAlertByReference(
        self, payload: CreateAlertByReferencePayload
    ) -> AlertsResults:
        """Create alert

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/create-alert-by-reference
        """
        path = f"{self._PATH}/CreateAlertByReference"
        return AlertsResults(
            self,
            {},
            path=path,
            single=True,
            method="POST",
            request_kwargs={"json": payload.model_dump(exclude_none=True)},
        )

    def batchUpdate(self, payload: BatchUpdateAlertPayload) -> AlertsResults:
        """Batch update alerts

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/batch-update-alerts
        """
        path = f"{self._PATH}/batchUpdate"
        return AlertsResults(
            self,
            {},
            path=path,
            single=True,
            method="POST",
            request_kwargs={"json": payload.model_dump(exclude_none=True)},
        )

    def update(self, payload: BatchUpdateAlertPayload) -> AlertsResults:
        """Update alerts (alias for batch update)

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/update-alert
        """
        return self.batchUpdate(payload)
