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

from pydantic import Field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from .alerts import AlertsResults
from .base import BaseEndpoint, BaseQuery, BaseResults
from ..schemas import (
    MACHINE_SCHEMA,
    PUBLIC_ASSET_DTO_SCHEMA,
    ASSET_BASELINE_ASSESSMENT_SCHEMA,
)
from ..models.enums import (
    DEVICE_VALUE,
    EXPOSURE_LEVEL,
    MACHINE_HEALTH_STATUS,
    ONBOARDING_STATUS,
    RISK_SCORE,
)

from ..models.action_payloads import (
    StartInvestigationPayload,
    CollectInvestigationPackagePayload,
    IsolatePayload,
    UnisolatePayload,
    RestrictCodeExecutionPayload,
    RunLiveResponsePayload,
    StopAndQuarantineFilePayload,
    UnrestrictCodeExecutionPayload,
    RunAntiVirusScanPayload,
    OffBoardPayload,
)

if TYPE_CHECKING:
    from .browserExtension import BrowserExtensionResults
    from .certificateInventory import CertificateInventoryResults
    from .deviceAvHealth import DeviceAVHealthResults
    from .investigations import InvestigationResults
    from .machineActions import MachineActionsResults
    from .misc import ProductDTOResults
    from .recommendations import RecommendationResults
    from .securityBaseline import AssetConfigurationResults
    from .software import (
        SoftwareResults,
        AssetSoftwareResults,
        AssetNonCPESoftwareResults,
    )
    from .users import UserResults
    from .vulnerabilities import VulnerabilityDTOResults

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


class MachinesExportQuery(BaseQuery):
    """Query parameters for machines export endpoints.

    See `MachinesEndpoint._baselineComplianceAssessmentExport` for an example of usage.
    """

    page_size: int | None = Field(default=50_000, ge=1, le=200_000)


class AssetBaselineAssessmentResults(BaseResults):
    """Results from the /api/machines/{id}/BaselineComplianceAssessmentByMachine endpoint."""

    SCHEMA = ASSET_BASELINE_ASSESSMENT_SCHEMA


class MachineReferencesResults(BaseResults):
    """Results from the /api/recommendations/{id}/machinereferences endpoint."""

    SCHEMA = PUBLIC_ASSET_DTO_SCHEMA


class MachineResults(BaseResults):
    """Results from the /api/machines endpoint."""

    SCHEMA = MACHINE_SCHEMA


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

    def logonusers(self, id: str) -> UserResults:
        """Get machine logon users for a machine

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-log-on-users
        """
        path = f"{self._PATH}/{id}/logonusers"
        return UserResults(self, {}, path=path)

    def alerts(self, id: str) -> AlertsResults:
        """Get machine related alerts

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-related-alerts
        """
        from .alerts import AlertsResults

        path = f"{self._PATH}/{id}/alerts"
        return AlertsResults(self, {}, path=path)

    def software(self, id: str) -> SoftwareResults:
        """Get installed software

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-installed-software
        """
        from .software import SoftwareResults

        path = f"{self._PATH}/{id}/software"
        return SoftwareResults(self, {}, path=path)

    def vulnerabilities(self, id: str) -> VulnerabilityDTOResults:
        """Get discovered vulnerabilities for a machine.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-discovered-vulnerabilities
        """
        path = f"{self._PATH}/{id}/vulnerabilities"
        return VulnerabilityDTOResults(self, {}, path=path)

    def recommendations(self, id: str) -> RecommendationResults:
        """Get security recommendations for a machine.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-security-recommendations
        """
        from .recommendations import RecommendationResults

        path = f"{self._PATH}/{id}/recommendations"
        return RecommendationResults(self, {}, path=path)

    def getmissingkbs(self, id: str) -> ProductDTOResults:
        """Get missing KBs by device ID

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-missing-kbs-machine
        """
        from .misc import ProductDTOResults

        path = f"{self._PATH}/{id}/getmissingkbs"
        return ProductDTOResults(self, {}, path=path)

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

    # === Certificate Inventory related endpoints ===
    def _certificateAssessmentByMachine(self) -> CertificateInventoryResults:
        """Get the certificate inventory for a machine.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-certificate-inventory-assessment
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-certificate-inventory-assessment#1-export-certificate-assessment-json-response
        """
        from .certificateInventory import CertificateInventoryResults

        path = f"{self._PATH}/certificateAssessmentByMachine"
        return CertificateInventoryResults(self, {}, path=path)

    def _certificateAssessmentExport(self) -> CertificateInventoryResults:
        """Get the certificate inventory for a machine as a file.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-certificate-inventory-assessment
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-certificate-inventory-assessment#2-export-certificate-assessment-via-files
        """
        from .certificateInventory import CertificateInventoryResults

        path = f"{self._PATH}/certificateAssessmentExport"
        return CertificateInventoryResults(self, {}, path=path, files=True)

    # === Device AV Health related endpoints ===
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
        self, id: str, payload: StartInvestigationPayload
    ) -> InvestigationResults:
        """Start Investigation

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/initiate-autoir-investigation
        """
        from .investigations import InvestigationResults

        path = f"{self._PATH}/{id}/startInvestigation"
        return InvestigationResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump()},
        )

    # === Machine Action related endpoints ===
    def _collectInvestigationPackage(
        self, id: str, payload: CollectInvestigationPackagePayload
    ) -> MachineActionsResults:
        """Collect investigation package for a machine

        If successful, this method returns 201 - Created response code and Machine Action in the response body. If a collection is already running, this returns 400 Bad Request.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/collect-investigation-package
        """
        from .machineActions import MachineActionsResults

        path = f"{self._PATH}/{id}/collectInvestigationPackage"
        return MachineActionsResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump()},
        )

    def _isolate(self, id: str, payload: IsolatePayload) -> MachineActionsResults:
        """Isolate a machine

        If successful, this method returns 201 - Created response code and Machine Action in the response body.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/isolate-machine
        """
        from .machineActions import MachineActionsResults

        path = f"{self._PATH}/{id}/isolate"
        return MachineActionsResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump()},
        )

    def _unisolate(self, id: str, payload: UnisolatePayload) -> MachineActionsResults:
        """Unisolate a machine

        If successful, this method returns 201 - Created response code and Machine Action in the response body.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/unisolate-machine
        """
        from .machineActions import MachineActionsResults

        path = f"{self._PATH}/{id}/unisolate"
        return MachineActionsResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump()},
        )

    def _restrictCodeExecution(
        self, id: str, payload: RestrictCodeExecutionPayload
    ) -> MachineActionsResults:
        """Restrict code execution on a machine

        If successful, this method returns 201 - Created response code and Machine Action in the response body.\n
        If you send multiple API calls to restrict app execution for the same device, it returns "pending machine action" or HTTP 400 with the message "Action is already in progress".

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/restrict-code-execution
        """
        from .machineActions import MachineActionsResults

        path = f"{self._PATH}/{id}/restrictCodeExecution"
        return MachineActionsResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump()},
        )

    def _unrestrictCodeExecution(
        self, id: str, payload: UnrestrictCodeExecutionPayload
    ) -> MachineActionsResults:
        """Unrestrict code execution on a machine

        If successful, this method returns 201 - Created response code and Machine Action in the response body.\n
        If you send multiple API calls to remove app restrictions for the same device, it returns "pending machine action" or HTTP 400 with the message "Action is already in progress".

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/unrestrict-code-execution
        """
        from .machineActions import MachineActionsResults

        path = f"{self._PATH}/{id}/unrestrictCodeExecution"
        return MachineActionsResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump()},
        )

    def _runAntiVirusScan(
        self, id: str, payload: RunAntiVirusScanPayload
    ) -> MachineActionsResults:
        """Run antivirus scan on a machine

        If successful, this method returns 201, Created response code and MachineAction object in the response body.\n
        If you send multiple API calls to run an antivirus scan for the same device, it returns "pending machine action" or HTTP 400 with the message "Action is already in progress".

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/run-av-scan
        """
        from .machineActions import MachineActionsResults

        path = f"{self._PATH}/{id}/runAntiVirusScan"
        return MachineActionsResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump()},
        )

    def _runLiveResponse(
        self, id: str, payload: RunLiveResponsePayload
    ) -> MachineActionsResults:
        """Run live response on a machine

        If successful, this method returns 201, Created response code and MachineAction object in the response body.\n
        If you send multiple API calls to run live response for the same device, it returns "pending machine action" or HTTP 400 with the message "Action is already in progress".

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/run-live-response
        """
        from .machineActions import MachineActionsResults

        path = f"{self._PATH}/{id}/runliveresponse"
        return MachineActionsResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump()},
        )

    def _offBoard(self, id: str, payload: OffBoardPayload) -> MachineActionsResults:
        """Offboard a machine

        If successful, this method returns 200 - Created response code and Machine Action in the response body.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/offboard-machine-api
        """
        from .machineActions import MachineActionsResults

        path = f"{self._PATH}/{id}/offboard"
        return MachineActionsResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump()},
        )

    def _stopAndQuarantineFile(
        self, id: str, payload: StopAndQuarantineFilePayload
    ) -> MachineActionsResults:
        """Stop and quarantine a file on a machine

        If successful, this method returns 201, Created response code and MachineAction object in the response body.\n
        If you send multiple API calls to stop and quarantine the same file for the same device, it returns "pending machine action" or HTTP 400 with the message "Action is already in progress".

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/stop-and-quarantine-file
        """
        from .machineActions import MachineActionsResults

        path = f"{self._PATH}/{id}/StopAndQuarantineFile"
        return MachineActionsResults(
            self,
            {},
            path=path,
            method="POST",
            request_kwargs={"json": payload.model_dump()},
        )

    # === Security Baseline related endpoints ===
    def _baselineComplianceAssessmentByMachine(self) -> AssetBaselineAssessmentResults:
        """Get the security baseline compliance assessment for a machine.

        Returns all security baselines assessments for all devices, on a per-device basis.\n
        It returns a table with a separate entry for every unique combination of DeviceId, ProfileId, ConfigurationId.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-security-baseline-assessment
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-security-baseline-assessment#1-export-security-baselines-assessment-json-response
        """
        path = f"{self._PATH}/baselineComplianceAssessmentByMachine"
        return AssetBaselineAssessmentResults(self, {}, path=path)

    def _baselineComplianceAssessmentExport(self) -> AssetBaselineAssessmentResults:
        """Get the security baseline compliance assessment for a machine as a file.

        Returns all security baselines assessments for all devices, on a per-device basis.\n
        It returns a table with a separate entry for every unique combination of DeviceId, ProfileId, ConfigurationId.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-security-baseline-assessment
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-security-baseline-assessment#2-export-security-baselines-assessment-via-files
        """
        path = f"{self._PATH}/BaselineComplianceAssessmentExport"
        return AssetBaselineAssessmentResults(self, {}, path=path, files=True)

    def _secureConfigurationsAssessmentByMachine(self) -> AssetConfigurationResults:
        """Get the secure configuration assessment for a machine.

        This response contains the Secure Configuration Assessment on your exposed devices,
        and returns an entry for every unique combination of DeviceId, ConfigurationId.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-secure-config
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-secure-config#1-export-secure-configuration-assessment-json-response
        """
        from .securityBaseline import AssetConfigurationResults

        path = f"{self._PATH}/SecureConfigurationsAssessmentByMachine"
        return AssetConfigurationResults(self, {}, path=path)

    def _secureConfigurationsAssessmentExport(self) -> AssetConfigurationResults:
        """Get the secure configuration assessment for a machine as a file.

        This response contains the Secure Configuration Assessment on your exposed devices,
        and returns an entry for every unique combination of DeviceId, ConfigurationId.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-secure-config
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-secure-config#2-export-secure-configuration-assessment-via-files
        """
        from .securityBaseline import AssetConfigurationResults

        path = f"{self._PATH}/SecureConfigurationsAssessmentExport"
        return AssetConfigurationResults(self, {}, path=path, files=True)

    # === Software Related endpoints ===
    def _softwareInventoryByMachine(
        self, page_size: int = 50000, since: datetime | None = None
    ) -> AssetSoftwareResults:
        """Get software inventory records for a specific machine.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-software-inventory-by-machine
        """
        from .software import AssetSoftwareResults

        path = f"{self._PATH}/SoftwareInventoryByMachine"
        return AssetSoftwareResults(self, {}, path=path)

    def _softwareInventoryExport(self) -> AssetSoftwareResults:
        """Get software inventory records for a specific machine as a file.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-software-inventory-by-machine#2-export-software-inventory-by-machine-via-files
        """
        from .software import AssetSoftwareResults

        path = f"{self._PATH}/SoftwareInventoryExport"
        return AssetSoftwareResults(self, {}, path=path, files=True)

    def _softwareInventoryNoProductCodeByMachine(
        self, page_size: int = 50000, since: datetime | int | str | None = None
    ) -> AssetNonCPESoftwareResults:
        """Get software inventory records that do not have a product code for a specific machine.

        Args:
            page_size(int): Pagination size for the results. Default is 50k, Max is 200k.
            since(datetime | int | str | None):
                - datetime: The datetime object representing the that date and forward
                - int: Number of days to look back from now (e.g. since=30 returns records seen in the last 30 days)
                - str: Needs to look like "2024-01-01" - Year-Month-Day format, representing that date and forward
                - None: No time-based filtering, return all records regardless of when they were seen.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-non-cpe-software-inventory
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-non-cpe-software-inventory#1-export-non-product-code-software-inventory-assessment-json-response
        """
        from .software import AssetNonCPESoftwareResults

        params = (
            MachinesExportQuery(page_size=page_size, sinceTime=since)
            .to_datetime_format(regex=r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
            .to_odata_filters
        )
        path = f"{self._PATH}/SoftwareInventoryNoProductCodeByMachine"
        return AssetNonCPESoftwareResults(self, params, path=path)

    def _softwareInventoryNonCpeExport(self) -> AssetNonCPESoftwareResults:
        """Get software inventory records that do not have a product code for a specific machine exported from files.

        Same Results as `_softwareInventoryNoProductCodeByMachine` but exported as a file instead of in the response body.
        Recommended for larger data sets, as it returns zipped files with the data instead of returning it in the response body.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-non-cpe-software-inventory
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-non-cpe-software-inventory#2-export-non-product-code-software-inventory-assessment-via-files
        """
        from .software import AssetNonCPESoftwareResults

        path = f"{self._PATH}/SoftwareInventoryNonCpeExport"
        return AssetNonCPESoftwareResults(self, {}, path=path, files=True)


class MachineNotFoundError(Exception):
    def __init__(self, machine_id: str) -> None:
        super().__init__(f"Machine '{machine_id}' not found.")
        self.machine_id = machine_id
