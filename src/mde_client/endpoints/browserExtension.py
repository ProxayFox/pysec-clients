"""Microsoft Defender for Endpoint browser-extension inventory endpoint.

This module defines:
- `BrowserExtensionsPermissionsInfoQuery`: OData query model for filtering
  browser extension permission records.
- `BrowserExtensionResults` and `BrowserExtensionsResults`: lazy result
  wrappers mapped to the browser-extension Arrow schemas.
- `BrowserExtensionEndpoint`: a thin shim that forwards requests to the
  browser-extension paths on the Machines API and returns correctly-typed
  result wrappers. Core HTTP and pagination logic is inherited from
  `MachinesEndpoint` / `BaseEndpoint`.

Endpoint methods return lazy `BaseResults` subclasses and defer HTTP requests
until a terminal materialization method is called.

**Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/export-browser-extensions-assessment
"""

from __future__ import annotations

from datetime import datetime

from .base import BaseQuery, BaseEndpoint, BaseResults
from .machines import MachinesEndpoint
from ..schemas import ASSET_BROWSER_EXTENSION_SCHEMA, BROWSER_EXTENSIONS_SCHEMA


class BrowserExtensionsPermissionsInfoQuery(BaseQuery):
    """Query for the /api/machines/permissionsinfo endpoint."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    cvssV3: str | None = None
    publishedOn: datetime | None = None
    severity: str | None = None
    updatedOn: datetime | None = None


class BrowserExtensionResults(BaseResults):
    """Results from the /api/machines/BrowserExtensionsInventoryByMachine endpoint."""

    SCHEMA = ASSET_BROWSER_EXTENSION_SCHEMA


class BrowserExtensionsPermissionsInfoResults(BaseResults):
    """Results from the /api/machines/permissionsinfo endpoint."""

    SCHEMA = BROWSER_EXTENSIONS_SCHEMA


class BrowserExtensionEndpoint(BaseEndpoint):
    """Endpoint for /api/machines/BrowserExtensionsInventoryByMachine"""

    _PATH = "/api/browserextensions"

    def get_all(self) -> BrowserExtensionResults:
        """Get All Browser Extensions for a machine.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-browser-extensions
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-browser-extensions#1-export-browser-extensions-assessment-json-response
        """
        return MachinesEndpoint(
            self._http, self._auth
        )._browserExtensionsInventoryByMachine()

    def get_all_files(self) -> BrowserExtensionResults:
        """Get All Browser Extensions for a machine.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-browser-extensions
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-browser-extensions#2-export-browser-extension-assessment-via-files

        TODO: Need to Implement file download and parsing logic to handle this endpoint
        """
        return MachinesEndpoint(
            self._http, self._auth
        )._browserextensionsinventoryExport()

    def permissionsinfo(
        self, query: BrowserExtensionsPermissionsInfoQuery | None = None
    ) -> BrowserExtensionsPermissionsInfoResults:
        """Get permissions info for browser extensions.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-browser-extensions-permission-info
        """
        params = query.to_odata_filters if query else {}
        path = f"{self._PATH}/permissionsinfo"
        return BrowserExtensionsPermissionsInfoResults(self, params, path=path)
