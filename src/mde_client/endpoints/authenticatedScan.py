from __future__ import annotations

import logging
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .base import BaseQuery, BaseEndpoint, BaseResults
from ..schemas import (
    AUTH_SCAN_HISTORY_CONTRACT_SCHEMA,
    DEVICE_AUTHENTICATED_SCAN_DEFINITION_SCHEMA,
    DEVICE_AUTHENTICATED_SCAN_AGENT_SCHEMA,
)

log = logging.getLogger(__name__)

# ── Auth-param type literals (mirror upstream enum values) ────────────────────

WINDOWS_AUTH_TYPE = Literal["Negotiate", "Kerberos", "Ntlm"]
LINUX_AUTH_TYPE = Literal["Password", "PrivateKey"]
SNMP_AUTH_TYPE = Literal["CommunityString", "NoAuthNoPriv", "AuthNoPriv", "AuthPriv"]
SCAN_TYPE = Literal["Network", "Windows", "Linux", "AdvancedActive"]
TARGET_TYPE = Literal["Ip", "Hostname", "Combined"]

# ── Auth-param request models ─────────────────────────────────────────────────


class _AuthParamsBase(BaseModel):
    """Shared key-vault fields present on every auth-param variant."""

    model_config = {"extra": "forbid"}

    keyVaultUri: str | None = None
    keyVaultSecretName: str | None = None


class WindowsAuthParams(_AuthParamsBase):
    """Windows authentication parameters.

    **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition
    """

    type: WINDOWS_AUTH_TYPE
    username: str | None = None
    password: str | None = None
    domain: str | None = None
    isgmsaUser: bool = False
    packetPrivacy: bool = False
    packetIntegrity: bool = False


class LinuxAuthParams(_AuthParamsBase):
    """Linux authentication parameters.

    **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition
    """

    type: LINUX_AUTH_TYPE
    username: str | None = None
    password: str | None = None
    privateKey: str | None = None


class SnmpAuthParams(_AuthParamsBase):
    """SNMP authentication parameters.

    **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition
    """

    type: SNMP_AUTH_TYPE
    communityString: str | None = None
    username: str | None = None
    authProtocol: str | None = None
    authPassword: str | None = None
    privProtocol: str | None = None
    privPassword: str | None = None


ScanAuthenticationParams = Annotated[
    WindowsAuthParams | LinuxAuthParams | SnmpAuthParams,
    Field(discriminator="type"),
]

# ── Scanner agent model ──────────────────────────────────────────────────────


class ScannerAgentRef(BaseModel):
    """Reference to a scanner agent device."""

    model_config = {"extra": "forbid"}

    id: str
    machineId: str | None = None


class AuthenticatedScanHistoryQuery(BaseModel):
    """OData query parameters for authenticated scan history actions."""

    model_config = {"extra": "forbid"}

    top: int | None = Field(default=None, ge=1, le=10000)
    skip: int | None = Field(default=None, ge=0)

    @property
    def to_odata_filters(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self.top is not None:
            params["$top"] = str(self.top)
        if self.skip is not None:
            params["$skip"] = str(self.skip)
        return params


class ScanHistoryByDefinitionRequest(BaseModel):
    """Request body for scan history by definition."""

    model_config = {"extra": "forbid"}

    ScanDefinitionIds: list[str]


class ScanHistoryBySessionRequest(BaseModel):
    """Request body for scan history by session."""

    model_config = {"extra": "forbid"}

    SessionIds: list[str]


def _as_id_list(ids: str | list[str]) -> list[str]:
    return [ids] if isinstance(ids, str) else ids


class AuthenticatedDefinitionsQuery(BaseQuery):
    """Query parameters for the /api/DeviceAuthenticatedScanDefinitions endpoint.

    All fields are optional, omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Doesn't appear to be any filters for this endpoint,
    but the class is left here for consistency and future-proofing.
    """

    pass


class AuthenticatedDefinitionsAlterQuery(BaseQuery):
    """Query parameters for Add, update, or delete a scan definition on the /api/DeviceAuthenticatedScanDefinitions endpoint.

    All fields are optional, omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Note: This is a placeholder class for future implementation of update operations on authenticated scan definitions.
    The specific fields and validation logic will depend on the requirements of the update operations once they are defined.
    """

    id: str | None = None
    scanType: SCAN_TYPE | None = None
    scanName: str | None = None
    isActive: bool | None = None
    targets: list[str] | None = None
    intervalInHours: int | None = None
    targetType: TARGET_TYPE | None = None
    scannerAgent: ScannerAgentRef | None = None
    scanAuthenticationParams: (
        WindowsAuthParams | LinuxAuthParams | SnmpAuthParams | None
    ) = None


class DeviceAuthenticatedAgentsQuery(BaseQuery):
    """Query parameters for the /api/DeviceAuthenticatedScanAgents endpoint.

    All fields are optional, omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Doesn't appear to be any filters for this endpoint,
    but the class is left here for consistency and future-proofing.
    """

    pass


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

    def history(
        self,
        ids: str | list[str],
        query: AuthenticatedScanHistoryQuery | None = None,
    ) -> AuthenticatedScanHistoryResults:
        """Get scan history by definition IDs.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-scan-history-by-definition
        """
        params = query.to_odata_filters if query else {}
        payload = ScanHistoryByDefinitionRequest(
            ScanDefinitionIds=_as_id_list(ids)
        ).model_dump()
        path = f"{self._PATH}/GetScanHistoryByScanDefinitionId"
        return AuthenticatedScanHistoryResults(
            self,
            params,
            path=path,
            method="POST",
            request_kwargs={"json": payload},
        )

    def history_by_session(
        self,
        ids: str | list[str],
        query: AuthenticatedScanHistoryQuery | None = None,
    ) -> AuthenticatedScanHistoryResults:
        """Get scan history by session IDs.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-scan-history-by-session
        """
        params = query.to_odata_filters if query else {}
        payload = ScanHistoryBySessionRequest(SessionIds=_as_id_list(ids)).model_dump()
        path = f"{self._PATH}/GetScanHistoryBySessionId"
        return AuthenticatedScanHistoryResults(
            self,
            params,
            path=path,
            method="POST",
            request_kwargs={"json": payload},
        )

    def add(
        self, query: AuthenticatedDefinitionsAlterQuery
    ) -> AuthenticatedDefinitionsResults:
        """Add a new authenticated scan definition.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition#example-request-to-add-a-new-scan
        """
        # return AuthenticatedDefinitionsResults(self, {})
        raise NotImplementedError(
            "Add operation for authenticated scan definitions is not yet implemented."
        )

    def update(
        self, query: AuthenticatedDefinitionsAlterQuery
    ) -> AuthenticatedDefinitionsResults:
        """Update an existing authenticated scan definition.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition#example-request-to-update-a-scan
        """
        # if not query.id:
        # raise ValueError("ID is required for updating an authenticated scan definition.")
        # path = f"{self._PATH}/{query.id}"

        # return AuthenticatedDefinitionsResults(self, {}, path=path)
        raise NotImplementedError(
            "Update operation for authenticated scan definitions is not yet implemented."
        )

    def delete(self, ids: str | list[str]) -> AuthenticatedDefinitionsAlterQuery:
        """Delete existing authenticated scan definition.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition
            - https://learn.microsoft.com/en-us/defender-endpoint/api/add-a-new-scan-definition#example-request-to-delete-scans
        """
        # ids = [ids] if isinstance(ids, str) else ids
        # path = f"{self._PATH}/BatchDelete"
        # return AuthenticatedDefinitionsAlterQuery()
        raise NotImplementedError(
            "Delete operation for authenticated scan definitions is not yet implemented."
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

    def history(
        self,
        ids: str | list[str],
        query: AuthenticatedScanHistoryQuery | None = None,
    ) -> AuthenticatedScanHistoryResults:
        """Compatibility shim for the definitions-bound scan history action."""
        return AuthenticatedDefinitionsEndpoint(self._http, self._auth).history(
            ids,
            query,
        )
