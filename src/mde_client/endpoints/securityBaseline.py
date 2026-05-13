from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseEndpoint, BaseResults
from ..schemas import BASELINE_CONFIGURATION_SCHEMA, ASSET_CONFIGURATION_SCHEMA

if TYPE_CHECKING:
    from .machines import AssetBaselineAssessmentResults


class BaselineConfigurationResults(BaseResults):
    """Results from the /api/baselineConfigurations endpoint."""

    SCHEMA = BASELINE_CONFIGURATION_SCHEMA


class AssetConfigurationResults(BaseResults):
    """Results from the /api/assetConfigurations endpoint."""

    SCHEMA = ASSET_CONFIGURATION_SCHEMA


class BaselineConfigurationEndpoint(BaseEndpoint):
    """Endpoint for /api/baselineConfigurations."""

    def get_all(self) -> AssetBaselineAssessmentResults:
        """Get the security baseline compliance assessment for a machine.

        Returns all security baselines assessments for all devices, on a per-device basis.\n
        It returns a table with a separate entry for every unique combination of DeviceId, ProfileId, ConfigurationId.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-security-baseline-assessment
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-security-baseline-assessment#1-export-security-baselines-assessment-json-response
        """
        from .machines import MachinesEndpoint

        return MachinesEndpoint(
            self._http, self._auth
        )._baselineComplianceAssessmentByMachine()

    def get_all_files(self) -> AssetBaselineAssessmentResults:
        """Get the security baseline compliance assessment for a machine as a file.

        Returns all security baselines assessments for all devices, on a per-device basis.\n
        It returns a table with a separate entry for every unique combination of DeviceId, ProfileId, ConfigurationId.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-security-baseline-assessment
            - https://learn.microsoft.com/en-us/defender-endpoint/api/export-security-baseline-assessment#2-export-security-baselines-assessment-via-files
        """
        from .machines import MachinesEndpoint

        return MachinesEndpoint(
            self._http, self._auth
        )._baselineComplianceAssessmentExport()

    def profiles(self) -> BaselineConfigurationResults:
        """Retrieves a list of all security baselines assessment profiles created by the organization.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-security-baselines-assessment-profiles
        """
        path = "/api/baselineProfiles"
        return BaselineConfigurationResults(self, {}, path=path)

    def active(self) -> BaselineConfigurationResults:
        """Retrieves a list of the configurations being assessed in active baseline profiles.

        **Docs:** https://learn.microsoft.com/en-us/defender-endpoint/api/get-security-baselines-assessment-configurations
        """
        path = "/api/baselineConfigurations"
        return BaselineConfigurationResults(self, {}, path=path)

    def assessmentByMachine(self) -> AssetConfigurationResults:
        """Get the secure configuration assessment for a machine.

        This response contains the Secure Configuration Assessment on your exposed devices,
        and returns an entry for every unique combination of DeviceId, ConfigurationId.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-secure-config
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-secure-config#1-export-secure-configuration-assessment-json-response
        """
        from .machines import MachinesEndpoint

        return MachinesEndpoint(
            self._http, self._auth
        )._secureConfigurationsAssessmentByMachine()

    def assessmentByMachineFiles(self) -> AssetConfigurationResults:
        """Get the secure configuration assessment for a machine as a file.

        This response contains the Secure Configuration Assessment on your exposed devices,
        and returns an entry for every unique combination of DeviceId, ConfigurationId.

        **Docs:**
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-secure-config
            - https://learn.microsoft.com/en-us/defender-endpoint/api/get-assessment-secure-config#2-export-secure-configuration-assessment-via-files
        """
        from .machines import MachinesEndpoint

        return MachinesEndpoint(
            self._http, self._auth
        )._secureConfigurationsAssessmentExport()
