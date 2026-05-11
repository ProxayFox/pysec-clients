from __future__ import annotations

import logging
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from .base import BaseQuery, BaseEndpoint, BaseResults
from ..schemas import (
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


class DeviceAuthenticatedAgentsQueryResults(BaseResults):
    SCHEMA = DEVICE_AUTHENTICATED_SCAN_AGENT_SCHEMA


class AuthenticatedDefinitionsEndpoint(BaseEndpoint):
    _PATH = "/api/DeviceAuthenticatedScanDefinitions"

    def get_all(
        self, query: AuthenticatedDefinitionsQuery | None = None
    ) -> AuthenticatedDefinitionsResults:
        """Get all authenticated scan definitions."""
        params = query.to_odata_filters if query else {}
        return AuthenticatedDefinitionsResults(self, params)


class DeviceAuthenticatedAgentsEndpoint(BaseEndpoint):
    _PATH = "/api/DeviceAuthenticatedScanAgents"

    def get_all(
        self, query: DeviceAuthenticatedAgentsQuery | None = None
    ) -> DeviceAuthenticatedAgentsQueryResults:
        """Get all device authenticated scan agents."""
        params = query.to_odata_filters if query else {}
        return DeviceAuthenticatedAgentsQueryResults(self, params)
