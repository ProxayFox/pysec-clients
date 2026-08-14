from __future__ import annotations

from ..schemas import ASSET_HARDWARE_FIRMWARE_SCHEMA, FIRMWARE_SCHEMA
from .base import BaseEndpoint, BaseResults
from .machines import MachinesEndpoint


class FirmwareResults(BaseResults):
    """Results from the /api/firmware endpoint."""

    SCHEMA = FIRMWARE_SCHEMA


class AssetHardwareFirmwareResults(BaseResults):
    """Results from the /api/machines/hardwareFirmwareInventoryByMachine/ endpoint."""

    SCHEMA = ASSET_HARDWARE_FIRMWARE_SCHEMA


class FirmwareEndpoint(BaseEndpoint):
    """Endpoint for /api/firmware."""

    _PATH = "/api/firmware"

    def get_all(self) -> FirmwareResults:
        """Retrieves firmware information for devices.

        **Docs:** Null (undocumented endpoint)
        """
        return FirmwareResults(self, {}, single=True)

    def get(self, device_id: str) -> FirmwareResults:
        """Retrieves firmware information for a specific firmware by ID.

        **Docs:** Null (undocumented endpoint)
        """
        return MachinesEndpoint(self._http, self._auth)._deviceFirmware(device_id)

    def firmwareInventoryByMachine(self) -> AssetHardwareFirmwareResults:
        """Get the firmware inventory for machines.

        **Docs:** Null (undocumented endpoint)
        """
        return MachinesEndpoint(self._http, self._auth)._firmwareInventoryByMachine()

    def firmwareInventoryByMachineFiles(self) -> AssetHardwareFirmwareResults:
        """Get the firmware inventory for machines as files.

        Same Results as `firmwareInventoryByMachine` but exported as a file instead of in the response body.
        Recommended for larger data sets, as it returns zipped files with the data instead of returning it in the response body.

        **Docs:** Null (undocumented endpoint)
        """
        return MachinesEndpoint(
            self._http, self._auth
        )._firmwareInventoryByMachineFiles()
