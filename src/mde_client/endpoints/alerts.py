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

from .base import BaseEndpoint, BasePayload, BaseQuery, BaseResults
from ..schemas import (
    ALERT_SCHEMA,
    USER_SCHEMA,
)
from ..models.enums import (
    ALERT_CLASSIFICATION,
    ALERT_DETERMINATION,
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
    from .ips import IPResults

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


class UpdateAlertPayload(BasePayload):
    """Payload for updating a single alert using one alert ID."""

    alertId: str
    status: ALERT_STATUS | None = None
    assignedTo: str | None = None
    classification: ALERT_CLASSIFICATION | None = None
    determination: ALERT_DETERMINATION | None = None
    comment: str | None = None


class AlertsResults(BaseResults):
    """Results from the /api/alerts endpoint."""

    SCHEMA = ALERT_SCHEMA


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
        from .ips import IPResults

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

    def batchUpdate(self, payload: BatchUpdateAlertPayload) -> bool:
        """Batch update alerts

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/batch-update-alerts
                - If successful, this method returns 200 OK, with an empty response body.
        """
        path = f"{self._PATH}/batchUpdate"
        result = self._request("POST", path, json=payload.model_dump(exclude_none=True))
        match result.status_code:
            case 200:
                return True
            case _:
                try:
                    result.raise_for_status()
                except Exception as e:
                    raise RuntimeError(f"Failed to batch update alerts: {e}") from e
                return False

    def update(self, payload: UpdateAlertPayload) -> AlertsResults:
        """Update alerts (alias for batch update)

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/update-alert
        """
        path = f"{self._PATH}/{payload.alertId}"
        pl = payload.model_dump(exclude_none=True).pop("alertId")
        return AlertsResults(
            self,
            {},
            path=path,
            single=True,
            method="PATCH",
            request_kwargs={"json": pl},
        )
