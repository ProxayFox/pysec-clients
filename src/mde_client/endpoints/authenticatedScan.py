from __future__ import annotations

import logging
from datetime import datetime
from typing import Literal, Any

from .base import BaseQuery, BaseEndpoint, BaseResults
from ..schemas import (
    DEVICE_AUTHENTICATED_SCAN_DEFINITION_SCHEMA,
    DEVICE_AUTHENTICATED_SCAN_AGENT_SCHEMA
)

log = logging.getLogger(__name__)

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
    scanType: str | None = None
    scanName: str | None = None
    isActive: bool | None = None
    targets: list[str] | None = None
    intervalInHours: int | None = None
    targetType: str | None = None
    scannerAgent: dict[str, str] | None = None
    scanAuthenticationParams: dict | None = None

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
    
    def get_all(self, query: AuthenticatedDefinitionsQuery | None = None) -> AuthenticatedDefinitionsResults:
        """Get all authenticated scan definitions."""
        params = query.to_odata_filters if query else {}
        return AuthenticatedDefinitionsResults(self, params)
        
class DeviceAuthenticatedAgentsEndpoint(BaseEndpoint):
    
    _PATH = "/api/DeviceAuthenticatedScanAgents"
    
    def get_all(self, query: DeviceAuthenticatedAgentsQuery | None = None) -> DeviceAuthenticatedAgentsQueryResults:
        """Get all device authenticated scan agents."""
        params = query.to_odata_filters if query else {}
        return DeviceAuthenticatedAgentsQueryResults(self, params)
