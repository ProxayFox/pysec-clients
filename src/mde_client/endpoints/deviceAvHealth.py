from __future__ import annotations


from .base import BaseQuery, BaseEndpoint, BaseResults
from ..schemas import INVESTIGATION_SCHEMA


class DeviceAVHealthQuery(BaseQuery):
    """Query parameters for the /api/deviceavinfo endpoint."""

    machineId: str
    computerDnsName: str
    osKind: str
    osPlatform: str
    osVersion: str
    avMode: str
    avSignatureVersion: str
    avEngineVersion: str
    avPlatformVersion: str
    quickScanResult: str
    quickScanError: str
    fullScanResult: str
    fullScanError: str
    avIsSignatureUpToDate: str
    avIsEngineUpToDate: str
    avIsPlatformUpToDate: str
    rbacGroupId: str


class DeviceAVHealthResults(BaseResults):
    """Results from the /api/deviceavinfo endpoint."""

    SCHEMA = INVESTIGATION_SCHEMA


class DeviceAVHealthEndpoint(BaseEndpoint):
    """Endpoint for /api/deviceavinfo"""

    def get_all(
        self, query: DeviceAVHealthQuery | None = None
    ) -> DeviceAVHealthResults:
        """Get device AV health with optional filters.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-device-av-health
        """
        path = "/api/deviceavinfo"
        params = query.to_odata_filters if query else {}
        return DeviceAVHealthResults(self, params, path=path)

    def get_all_files(self) -> DeviceAVHealthResults:
        path = "/api/InfoGatheringExport"
        return DeviceAVHealthResults(self, {}, path=path, files=True)
