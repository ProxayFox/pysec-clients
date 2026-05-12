from __future__ import annotations

import logging

from .base import BaseEndpoint, BaseQuery, BaseResults
from ..schemas import ASSET_CERTIFICATE_ASSESSMENT_SCHEMA

log = logging.getLogger(__name__)


class CertificateInventoryQuery(BaseQuery):
    """Query parameters for the /api/certificatesinventory endpoint."""

    pass


class CertificateInventoryResults(BaseResults):
    """Results from the /api/certificatesinventory endpoint."""

    SCHEMA = ASSET_CERTIFICATE_ASSESSMENT_SCHEMA


class CertificateInventoryEndpoint(BaseEndpoint):
    """Client for the certificate inventory endpoint."""

    def get_all(self) -> CertificateInventoryResults:
        """Get the certificate inventory for a machine.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-certificate-inventory-assessment
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-certificate-inventory-assessment#1-export-certificate-assessment-json-response
        """
        from .machines import MachinesEndpoint

        return MachinesEndpoint(
            self._http, self._auth
        )._certificateAssessmentByMachine()

    def get_all_files(self) -> CertificateInventoryResults:
        """Get the certificate inventory for a machine as a file.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-certificate-inventory-assessment
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-certificate-inventory-assessment#2-export-certificate-assessment-via-files
        """
        from .machines import MachinesEndpoint

        return MachinesEndpoint(self._http, self._auth)._certificateAssessmentExport()
