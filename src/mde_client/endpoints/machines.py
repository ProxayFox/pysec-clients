"""Microsoft Defender for Endpoint machines endpoint models and client surface.

This module defines:
- `MachinesQuery`: an OData-style query model for filtering machine listings.
- `*Results` wrappers: lazy result containers bound to Arrow schemas.
- `MachinesEndpoint`: endpoint methods for machine retrieval and related resources,
  including logon users, alerts, software, vulnerabilities, recommendations,
  missing KBs, and lookup helpers (`findbyip`, `tag`).

Endpoint methods return lazy `BaseResults` subclasses and do not issue HTTP
requests until a terminal materialization method is called.

**Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/machine
"""

from __future__ import annotations

import logging

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .base import BaseQuery, BaseEndpoint, BaseResults
from ..schemas import (
    MACHINE_SCHEMA,
    USER_SCHEMA,
    ALERT_SCHEMA,
    SOFTWARE_SCHEMA,
    VULNERABILITY_SCHEMA,
    RECOMMENDATION_SCHEMA,
    PUBLIC_PRODUCT_FIX_DTO_SCHEMA,
)
from ..models.enums import (
    DEVICE_VALUE,
    EXPOSURE_LEVEL,
    MACHINE_HEALTH_STATUS,
    ONBOARDING_STATUS,
    RISK_SCORE,
)

from ..models.action_payloads import StartInvestigationPayload

if TYPE_CHECKING:
    from .browserExtension import BrowserExtensionResults
    from .investigations import InvestigationResults
    from .deviceAvHealth import DeviceAVHealthResults

log = logging.getLogger(__name__)


class MachinesQuery(BaseQuery):
    """Query parameters for the /api/machines endpoint.

    All fields are optional — omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Example:
    ```python
    query = MachinesQuery(healthStatus="Active", pageSize=500)
    query = MachinesQuery(exposureLevel=["Medium", "High"], pageSize=500)
    ```
    """

    computerDnsName: str | list[str] | None = None
    id: str | list[str] | None = None
    version: str | list[str] | None = None
    deviceValue: DEVICE_VALUE | list[DEVICE_VALUE] | None = None
    aadDeviceId: str | list[str] | None = None
    machineTags: str | list[str] | None = None
    lastSeen: datetime | None = None
    exposureLevel: EXPOSURE_LEVEL | list[EXPOSURE_LEVEL] | None = None
    onboardingStatus: ONBOARDING_STATUS | list[ONBOARDING_STATUS] | None = None
    lastIpAddress: str | list[str] | None = None
    healthStatus: MACHINE_HEALTH_STATUS | list[MACHINE_HEALTH_STATUS] | None = None
    osPlatform: str | list[str] | None = None
    riskScore: RISK_SCORE | list[RISK_SCORE] | None = None
    rbacGroupId: str | list[str] | None = None


class MachineResults(BaseResults):
    """Results from the /api/machines endpoint."""
    SCHEMA = MACHINE_SCHEMA


class LogonUserResults(BaseResults):
    """Results from the /api/machines/{id}/logonusers endpoint."""
    SCHEMA = USER_SCHEMA


class AlertResults(BaseResults):
    """Results from the /api/machines/{id}/alerts endpoint."""
    SCHEMA = ALERT_SCHEMA


class SoftwareResults(BaseResults):
    """Results from the /api/machines/{id}/software endpoint."""
    SCHEMA = SOFTWARE_SCHEMA


class VulnerabilityResults(BaseResults):
    """Results from the /api/machines/{id}/vulnerabilities endpoint."""
    SCHEMA = VULNERABILITY_SCHEMA


class RecommendationResults(BaseResults):
    """Results from the /api/machines/{id}/recommendations endpoint."""
    SCHEMA = RECOMMENDATION_SCHEMA


class PublicProductFixResults(BaseResults):
    """Results from the /api/machines/{id}/getmissingkbs endpoint."""
    SCHEMA = PUBLIC_PRODUCT_FIX_DTO_SCHEMA


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

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines
        """
        params = query.to_odata_filters if query else {}
        return MachineResults(self, params)

    def get(self, id: str) -> MachineResults:
        """Get machine by ID

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-by-id
        """
        path = f"{self._PATH}/{id}"
        return MachineResults(self, {}, path=path, single=True)

    def logonusers(self, id: str) -> LogonUserResults:
        """Get machine logon users for a machine

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-log-on-users
        """
        path = f"{self._PATH}/{id}/logonusers"
        return LogonUserResults(self, {}, path=path)

    def alerts(self, id: str) -> AlertResults:
        """Get machine related alerts

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-related-alerts
        """
        path = f"{self._PATH}/{id}/alerts"
        return AlertResults(self, {}, path=path)

    def software(self, id: str) -> SoftwareResults:
        """Get installed software

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-installed-software
        """
        path = f"{self._PATH}/{id}/software"
        return SoftwareResults(self, {}, path=path)

    def vulnerabilities(self, id: str) -> VulnerabilityResults:
        """Get discovered vulnerabilities for a machine.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-discovered-vulnerabilities
        """
        path = f"{self._PATH}/{id}/vulnerabilities"
        return VulnerabilityResults(self, {}, path=path)

    def recommendations(self, id: str) -> RecommendationResults:
        """Get security recommendations for a machine.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-security-recommendations
        """
        path = f"{self._PATH}/{id}/recommendations"
        return RecommendationResults(self, {}, path=path)

    def getmissingkbs(self, id: str) -> PublicProductFixResults:
        """Get missing KBs by device ID

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-missing-kbs-machine
        """
        path = f"{self._PATH}/{id}/getmissingkbs"
        return PublicProductFixResults(self, {}, path=path)

    def findbyip(self, ip: str, timestamp: datetime) -> MachineResults:
        """Find devices by internal IP

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/find-machines-by-ip

        Args:
            ip(str): The internal IP address to search for.
            timestamp(datetime): UTC ISO 8601 timestamp to search for.
        """
        timestamp_utc = (
            timestamp.astimezone(timezone.utc)
            if timestamp.tzinfo is not None
            else timestamp.replace(tzinfo=timezone.utc)
        )
        timestamp_iso = timestamp_utc.isoformat().replace("+00:00", "Z")
        path = f"{self._PATH}/findbyip(ip='{ip}',timestamp={timestamp_iso})"
        return MachineResults(self, {}, path=path)

    def tag(self, tag: str, useStartsWithFilter: bool = False) -> MachineResults:
        """Find devices by tag API

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/find-machines-by-tag

        Args:
            tag(str): The tag to search for. Can be a full tag or a prefix if useStartsWithFilter is true.
            useStartsWithFilter(bool): Whether to use startswith filter or exact match. Default is false (exact match).
        """
        path = f"{self._PATH}/findbytag"
        params = {
            "tag": tag,
            "useStartsWithFilter": str(useStartsWithFilter).lower(),
        }
        return MachineResults(self, params, path=path)

    # === Browser Extension related endpoints ===
    # Browser Extension endpoints are on the MachinesEndpoint, intended to use the browserExtensions() method to access, but we can also expose them here if needed.
    def _browserExtensionsInventoryByMachine(self) -> BrowserExtensionResults:
        """Get browser extensions for a machine.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-browser-extensions
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-browser-extensions#1-export-browser-extensions-assessment-json-response
        """
        from .browserExtension import BrowserExtensionResults

        path = f"{self._PATH}/BrowserExtensionsInventoryByMachine"
        return BrowserExtensionResults(self, {}, path=path)

    def _browserextensionsinventoryExport(self) -> BrowserExtensionResults:
        """Get browser extensions for a machine.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-browser-extensions
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-browser-extensions#2-export-browser-extension-assessment-via-files
        """
        from .browserExtension import BrowserExtensionResults

        path = f"{self._PATH}/browserextensionsinventoryExport"
        return BrowserExtensionResults(self, {}, path=path, files=True)

    def _infoGatheringExport(self) -> DeviceAVHealthResults:
        """Get device AV health report as a file.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/device-health-export-antivirus-health-report-api
            - https://learn.microsoft.com/en-us/defender-endpoint/api/device-health-export-antivirus-health-report-api#2-export-health-reporting-via-files
        """
        from .deviceAvHealth import DeviceAVHealthResults

        path = f"{self._PATH}/InfoGatheringExport"
        return DeviceAVHealthResults(self, {}, path=path, files=True)

    # === Investigations related endpoints ===
    def _startInvestigation(
        self, id: str, payload: StartInvestigationPayload | None = None
    ) -> InvestigationResults:
        """Start Investigation

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/initiate-autoir-investigation
        """
        path = f"{self._PATH}/{id}/startInvestigation"
        return InvestigationResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump() if payload else {}},
        )


class MachineNotFoundError(Exception):
    def __init__(self, machine_id: str) -> None:
        super().__init__(f"Machine '{machine_id}' not found.")
        self.machine_id = machine_id
