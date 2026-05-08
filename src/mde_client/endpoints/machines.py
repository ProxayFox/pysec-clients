from __future__ import annotations

import logging

from datetime import datetime
from typing import Literal

from .base import BaseQuery, BaseEndpoint, BaseResults
from ..schemas.machines import MACHINES_SCHEMA, LOGON_USERS_BY_MACHINE_SCHEMA

log = logging.getLogger(__name__)

LEVELTYPE = Literal["None", "Informational", "Low", "Medium", "High"]
ONBOARDINGTYPE = Literal[
    "Onboarded", "CanBeOnboarded", "Unsupported", "InsufficientInfo"
]
HEALTHTYPE = Literal[
    "Active",
    "Inactive",
    "ImpairedCommunication",
    "NoSensorData",
    "NoSensorDataImpairedCommunication",
    "Unknown",
]


class MachinesQuery(BaseQuery):
    """Query parameters for the /api/machines endpoint.

    All fields are optional — omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Example:
        query = MachinesQuery(healthStatus="Active", pageSize=500)
    """

    computerDnsName: str | None = None
    id: str | list[str] | None = None
    version: str | None = None
    deviceValue: LEVELTYPE | None = None
    aadDeviceId: str | list[str] | None = None
    machineTags: str | list[str] | None = None
    lastSeen: datetime | None = None
    exposureLevel: LEVELTYPE | None = None
    onboardingStatus: ONBOARDINGTYPE | None = None
    lastIpAddress: str | None = None
    healthStatus: HEALTHTYPE | None = None
    osPlatform: str | None = None
    riskScore: LEVELTYPE | None = None
    rbacGroupId: str | None = None


class MachineResults(BaseResults):
    SCHEMA = MACHINES_SCHEMA


class LogonUserResults(BaseResults):
    SCHEMA = LOGON_USERS_BY_MACHINE_SCHEMA


class MachinesEndpoint(BaseEndpoint):
    """Client for the /api/machines endpoint.
    This is not intended to be used directly. Instead, used through MDEClient.machines.

    Returns a lazy ``MachineResults`` handle, no HTTP request is issued
        until a terminal method is called::

            results = client.machines.get_all(query)
            records = results.to_json()      # list[dict]
            table   = results.to_arrow()     # pa.Table  (requires [arrow])
            df      = results.to_polars()    # DataFrame (requires [polars])

        **Call ``results.refresh()`` to discard cached data and re-fetch.**
    """

    _PATH = "/api/machines"

    def get_all(self, query: MachinesQuery | None = None) -> MachineResults:
        """Get all machines, with optional filtering.
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines
        """
        params = query.to_odata_filters if query else {}
        return MachineResults(self, params)

    def get(self, id: str | None = None):
        """Get machine by ID
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-by-id
        """
        if id is None:
            raise ValueError("id must be provided")
        path = f"{self._PATH}/{id}"
        return MachineResults(self, {}, path=path, single=True)

    def logonusers(self, id: str):
        """Get machine logon users for a machine
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-log-on-users
        """
        path = f"{self._PATH}/{id}/logonusers"
        return LogonUserResults(self, {}, path=path)

    def alerts(self, id: str):
        """Get machine related alerts
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-related-alerts
        """
        # path = f"{self._PATH}/{id}/alerts"
        raise NotImplementedError("alerts endpoint not implemented yet")

    def software(self, id: str):
        """Get installed software
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-installed-software
        """
        # path = f"{self._PATH}/{id}/software"
        raise NotImplementedError("software endpoint not implemented yet")

    def vulnerabilities(self, id: str):
        """Get discovered vulnerabilities for a machine.
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-discovered-vulnerabilities
        """
        # path = f"{self._PATH}/{id}/vulnerabilities"
        raise NotImplementedError("vulnerabilities endpoint not implemented yet")

    def recommendations(self, id: str):
        """Get security recommendations for a machine.
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-security-recommendations
        """
        # path = f"{self._PATH}/{id}/recommendations"
        raise NotImplementedError("recommendations endpoint not implemented yet")

    def tags(self, id: str):
        """Find devices by tag API
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/find-machines-by-tag
        """
        # path = f"{self._PATH}/{id}/tags"
        raise NotImplementedError("tags endpoint not implemented yet")

    def getmissingkbs(self, id: str):
        """Get missing KBs by device ID
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-missing-kbs-machine
        """
        # path = f"{self._PATH}/{id}/getmissingkbs"
        raise NotImplementedError("getmissingkbs endpoint not implemented yet")


class MachineNotFoundError(Exception):
    def __init__(self, machine_id: str) -> None:
        super().__init__(f"Machine '{machine_id}' not found.")
        self.machine_id = machine_id
