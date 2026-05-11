"""Microsoft Defender for Endpoint authenticated-scan endpoint models and client surface.

This module defines:
- `DeviceAuthenticatedAgentsQuery` and `AuthenticatedDefinitionsQuery` request models.
- `AuthenticatedScanHistoryQuery` for history pagination.
- Payload models for creating, updating, and deleting scan definitions
  (``AuthenticatedDefinitionsAlterPayload``, ``ScannerAgentRefPayload``, etc.).
- `*Results` wrappers mapped to Arrow schemas for scan agents, definitions,
  and history records.
- `DeviceAuthenticatedAgentsEndpoint` and `AuthenticatedDefinitionsEndpoint`
  with methods for retrieving agents, listing/creating/updating/deleting scan
  definitions, and querying scan history by definition or session ID.

Endpoint methods return lazy `BaseResults` subclasses and defer HTTP requests
until a terminal materialization method is called.

**Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-authenticated-scan-agent
"""

from __future__ import annotations

import logging
from typing import Literal


from .base import BaseQuery, BaseEndpoint, BaseResults, BasePayload
from ..schemas import (
    AUTH_SCAN_HISTORY_CONTRACT_SCHEMA,
    DEVICE_AUTHENTICATED_SCAN_DEFINITION_SCHEMA,
    DEVICE_AUTHENTICATED_SCAN_AGENT_SCHEMA,
)
from ..models.auth_params_models import SCANAUTHENTICATIONPARAMS

log = logging.getLogger(__name__)

SCAN_TYPE = Literal["Network", "Windows", "Linux", "AdvancedActive"]
TARGET_TYPE = Literal["Ip", "Hostname", "Combined"]


class DeviceAuthenticatedAgentsQuery(BaseQuery):
    """Query parameters for the /api/DeviceAuthenticatedScanAgents endpoint.

    All fields are optional, omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Doesn't appear to be any filters for this endpoint,
    but the class is left here for consistency and future-proofing.
    """

    pass


class AuthenticatedScanHistoryQuery(BaseQuery):
    """OData query parameters for authenticated scan history actions."""

    model_config = {"extra": "forbid"}
    page_size: int | None = None


class AuthenticatedDefinitionsQuery(BaseQuery):
    """Query parameters for the /api/DeviceAuthenticatedScanDefinitions endpoint.

    All fields are optional, omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Doesn't appear to be any filters for this endpoint,
    but the class is left here for consistency and future-proofing.
    """

    pass


class ScannerAgentRefPayload(BasePayload):
    """Reference to a scanner agent device."""

    id: str
    machineId: str | None = None


class ScanHistoryByDefinitionRequestPayload(BasePayload):
    """Request body for scan history by definition."""

    ScanDefinitionIds: list[str]


class ScanHistoryBySessionRequestPayload(BasePayload):
    """Request body for scan history by session."""

    SessionIds: list[str]


class AuthenticatedDefinitionsAlterPayload(BaseQuery):
    """Query parameters for Add, update, or delete a scan definition on the /api/DeviceAuthenticatedScanDefinitions endpoint.

    All fields are optional, omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Note: This is a placeholder class for future implementation of update operations on authenticated scan definitions.
    The specific fields and validation logic will depend on the requirements of the update operations once they are defined.
    """

    # Not actually a parameter for this endpoint,
    # but included here to test that extraneous fields are properly excluded from the request body.
    page_size: int | None = None

    id: str | None = None
    scanType: SCAN_TYPE | None = None
    scanName: str | None = None
    isActive: bool | None = None
    targets: list[str] | None = None
    intervalInHours: int | None = None
    targetType: TARGET_TYPE | None = None
    scannerAgent: ScannerAgentRefPayload | None = None
    scanAuthenticationParams: SCANAUTHENTICATIONPARAMS | None = None


class AuthenticatedDefinitionsResults(BaseResults):
    SCHEMA = DEVICE_AUTHENTICATED_SCAN_DEFINITION_SCHEMA


class AuthenticatedScanHistoryResults(BaseResults):
    SCHEMA = AUTH_SCAN_HISTORY_CONTRACT_SCHEMA


class DeviceAuthenticatedAgentsQueryResults(BaseResults):
    SCHEMA = DEVICE_AUTHENTICATED_SCAN_AGENT_SCHEMA


class AuthenticatedDefinitionsEndpoint(BaseEndpoint):
    _PATH = "/api/DeviceAuthenticatedScanDefinitions"

    def get_all(
        self, query: AuthenticatedDefinitionsQuery | None = None
    ) -> AuthenticatedDefinitionsResults:
        """Get all authenticated scan definitions.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-all-scan-definitions
        """
        params = query.to_odata_filters if query else {}
        return AuthenticatedDefinitionsResults(self, params)

    def definition_history(
        self,
        ids: str | list[str],
        query: AuthenticatedScanHistoryQuery | None = None,
    ) -> AuthenticatedScanHistoryResults:
        """Get scan history by definition IDs.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-scan-history-by-definition
        """
        params = query.to_odata_filters if query else {}
        payload = ScanHistoryByDefinitionRequestPayload(
            ScanDefinitionIds=self._id_list(ids)
        ).model_dump()
        path = f"{self._PATH}/GetScanHistoryByScanDefinitionId"
        return AuthenticatedScanHistoryResults(
            self,
            params,
            path=path,
            method="POST",
            request_kwargs={"json": payload},
        )

    def session_history(
        self,
        ids: str | list[str],
        query: AuthenticatedScanHistoryQuery | None = None,
    ) -> AuthenticatedScanHistoryResults:
        """Get scan history by session IDs.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-scan-history-by-session
        """
        params = query.to_odata_filters if query else {}
        payload = ScanHistoryBySessionRequestPayload(
            SessionIds=self._id_list(ids)
        ).model_dump()
        path = f"{self._PATH}/GetScanHistoryBySessionId"
        return AuthenticatedScanHistoryResults(
            self,
            params,
            path=path,
            method="POST",
            request_kwargs={"json": payload},
        )

    def add(
        self, payload: AuthenticatedDefinitionsAlterPayload
    ) -> AuthenticatedDefinitionsResults:
        """Add a new authenticated scan definition.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition#example-request-to-add-a-new-scan
        """
        return AuthenticatedDefinitionsResults(
            self,
            {},
            method="POST",
            request_kwargs={"json": payload.model_dump(exclude_none=True)},
        )

    def update(
        self, payload: AuthenticatedDefinitionsAlterPayload
    ) -> AuthenticatedDefinitionsResults:
        """Update an existing authenticated scan definition.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition#example-request-to-update-a-scan
        """
        return AuthenticatedDefinitionsResults(
            self,
            {},
            method="PATCH",
            request_kwargs={"json": payload.model_dump(exclude_none=True)},
        )

    def delete(self, ids: str | list[str]) -> AuthenticatedDefinitionsResults:
        """Delete existing authenticated scan definition.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition#example-request-to-delete-scans
        """
        return AuthenticatedDefinitionsResults(
            self,
            {},
            method="POST",
            request_kwargs={"json": {"ScanDefinitionIds": self._id_list(ids)}},
        )


class DeviceAuthenticatedAgentsEndpoint(BaseEndpoint):
    _PATH = "/api/DeviceAuthenticatedScanAgents"

    def get_all(
        self, query: DeviceAuthenticatedAgentsQuery | None = None
    ) -> DeviceAuthenticatedAgentsQueryResults:
        """Get all device authenticated scan agents.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-all-scan-agents
        """
        params = query.to_odata_filters if query else {}
        return DeviceAuthenticatedAgentsQueryResults(self, params)

    def get(self, id: str) -> DeviceAuthenticatedAgentsQueryResults:
        """Get a single device authenticated scan agent by ID.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-agent-details
        """
        path = f"{self._PATH}/{id}"
        return DeviceAuthenticatedAgentsQueryResults(self, {}, path=path, single=True)
