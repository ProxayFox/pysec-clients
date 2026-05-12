from __future__ import annotations

import logging
import orjson
from typing import Any

from .base import BaseEndpoint, BaseQuery, BaseResults
from ..schemas import DEVICE_AV_INFO_SCHEMA
from ..viaFiles import RecordTransform

log = logging.getLogger(__name__)


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

    SCHEMA = DEVICE_AV_INFO_SCHEMA

    @staticmethod
    def _normalize_export_record() -> RecordTransform | None:
        """Flatten and rename the via-files export record to match the JSON schema.

        The file export wraps AV health fields inside ``DeviceGatheredInfo``
        as a **JSON-encoded string**, uses PascalCase field names at the top
        level (``DeviceId``, ``DeviceName``, …), and inside the nested blob
        uses names like ``AvMode``, ``AvIsSignatureUptoDate`` that differ
        from the JSON-API camelCase equivalents.
        """

        # Map export top-level / nested keys → schema keys.
        _FIELD_MAP: dict[str, str] = {
            "DeviceId": "machineId",
            "DeviceName": "computerDnsName",
            "OsPlatform": "osPlatform",
            "OsVersion": "osVersion",
            "LastSeenTime": "lastSeenTime",
            "RbacGroupId": "rbacGroupId",
            "RbacGroupName": "rbacGroupName",
            # Fields inside DeviceGatheredInfo
            "AvMode": "avMode",
            "AvSignatureVersion": "avSignatureVersion",
            "AvEngineVersion": "avEngineVersion",
            "AvPlatformVersion": "avPlatformVersion",
            "AvEngineUpdateTime": "avEngineUpdateTime",
            "AvSignatureUpdateTime": "avSignatureUpdateTime",
            "AvPlatformUpdateTime": "avPlatformUpdateTime",
            "AvIsSignatureUptoDate": "avIsSignatureUpToDate",
            "AvIsEngineUptodate": "avIsEngineUpToDate",
            "AvIsPlatformUptodate": "avIsPlatformUpToDate",
            "AvSignaturePublishTime": "avSignaturePublishTime",
            "AvSignatureDataRefreshTime": "avSignatureDataRefreshTime",
            "AvModeDataRefreshTime": "avModeDataRefreshTime",
            "CloudProtectionState": "cloudProtectionState",
            "Timestamp": "dataRefreshTimestamp",
        }

        # Derive osKind from OsPlatform.
        _OS_KIND_MAP: dict[str, str] = {
            "windows": "windows",
            "linux": "linux",
            "macos": "mac",
        }

        def _flatten(record: dict[str, Any]) -> dict[str, Any]:
            # Parse the nested JSON string.
            raw_nested = record.pop("DeviceGatheredInfo", None)
            if isinstance(raw_nested, str):
                try:
                    nested = orjson.loads(raw_nested)
                except Exception:
                    log.debug("Failed to parse DeviceGatheredInfo as JSON")
                    nested = {}
            elif isinstance(raw_nested, dict):
                nested = raw_nested
            else:
                nested = {}

            # Determine platform to set correct scan field defaults.
            os_platform = record.get("OsPlatform") or ""
            is_non_windows = os_platform.lower().startswith(("macos", "linux"))
            scan_empty = "-" if is_non_windows else ""

            # Extract scan results from the nested AvScanResults JSON string.
            av_scan_raw = nested.pop("AvScanResults", None)
            if isinstance(av_scan_raw, str):
                try:
                    scans = orjson.loads(av_scan_raw)
                    quick = scans.get("Quick") or {}
                    full = scans.get("Full") or {}
                    nested.setdefault(
                        "quickScanResult", quick.get("ScanStatus") or scan_empty
                    )
                    nested.setdefault(
                        "quickScanError", quick.get("ErrorCode") or scan_empty
                    )
                    nested.setdefault("quickScanTime", quick.get("Timestamp"))
                    nested.setdefault(
                        "fullScanResult", full.get("ScanStatus") or scan_empty
                    )
                    nested.setdefault(
                        "fullScanError", full.get("ErrorCode") or scan_empty
                    )
                    nested.setdefault("fullScanTime", full.get("Timestamp"))
                except Exception:
                    pass
            elif is_non_windows:
                # Non-Windows devices without AvScanResults use '-' placeholder.
                nested.setdefault("quickScanResult", scan_empty)
                nested.setdefault("quickScanError", scan_empty)
                nested.setdefault("fullScanResult", scan_empty)
                nested.setdefault("fullScanError", scan_empty)

            # Merge nested into top-level (top-level keys win on conflict).
            nested.update(record)
            record = nested

            # Derive osKind from OsPlatform.
            os_platform = record.get("OsPlatform") or record.get("osPlatform") or ""
            for prefix, kind in _OS_KIND_MAP.items():
                if os_platform.lower().startswith(prefix):
                    record.setdefault("osKind", kind)
                    break

            # Set machineId = id when not present (export uses DeviceId).
            mid = record.get("machineId") or record.get("DeviceId")
            if mid:
                record.setdefault("id", mid)

            # Normalise booleans to strings for schema compatibility.
            for key in (
                "AvIsSignatureUptoDate",
                "AvIsEngineUptodate",
                "AvIsPlatformUptodate",
                "avIsSignatureUpToDate",
                "avIsEngineUpToDate",
                "avIsPlatformUpToDate",
            ):
                val = record.get(key)
                if isinstance(val, bool):
                    record[key] = str(val)

            # Rename PascalCase → camelCase per schema.
            out: dict[str, Any] = {}
            for k, v in record.items():
                out[_FIELD_MAP.get(k, k)] = v

            return out

        return _flatten


class DeviceAVHealthEndpoint(BaseEndpoint):
    """Endpoint for /api/deviceavinfo"""

    def get_all(
        self, query: DeviceAVHealthQuery | None = None
    ) -> DeviceAVHealthResults:
        """Get device AV health with optional filters.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/device-health-export-antivirus-health-report-api
            - https://learn.microsoft.com/en-us/defender-endpoint/api/device-health-export-antivirus-health-report-api#1-export-health-reporting-json-response
        """
        path = "/api/deviceavinfo"
        params = query.to_odata_filters if query else {}
        return DeviceAVHealthResults(self, params, path=path)

    def get_all_files(self) -> DeviceAVHealthResults:
        """Get device AV health report as a file.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/device-health-export-antivirus-health-report-api
            - https://learn.microsoft.com/en-us/defender-endpoint/api/device-health-export-antivirus-health-report-api#2-export-health-reporting-via-files
        """
        from .machines import MachinesEndpoint

        return MachinesEndpoint(self._http, self._auth)._infoGatheringExport()
