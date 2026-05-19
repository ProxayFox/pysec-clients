from __future__ import annotations


from .base import BaseEndpoint, BaseResults
from ..schemas import DATA_EXPORT_SETTINGS_SCHEMA


class DataExportSettingsResults(BaseResults):
    """Results from the /api/dataExportSettings endpoint."""

    SCHEMA = DATA_EXPORT_SETTINGS_SCHEMA


class DataExportSettingsEndpoint(BaseEndpoint):
    """Endpoint for /api/dataExportSettings."""

    _PATH = "/api/dataExportSettings"

    def dataExportSettings(self) -> DataExportSettingsResults:
        """Retrieves the data export settings for the tenant.

        **Docs:** Null (undocumented endpoint)
        """
        return DataExportSettingsResults(self, {})
