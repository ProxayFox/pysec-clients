"""Endpoint package for the Microsoft Defender for Endpoint client.

This package provides lazy endpoint classes and result wrappers for each
Defender API surface area:

- `alerts` — alert retrieval and related resource lookups.
- `machines` — machine inventory, logon users, software, vulnerabilities,
  recommendations, and lookup helpers.
- `authenticatedScan` — authenticated scan agents, definitions, and history.
- `browserExtension` — browser extension inventory by machine.
- `base` — shared `BaseQuery`, `BasePayload`, `BaseResults`, and
  `BaseEndpoint` primitives consumed by every endpoint module.

All public endpoint classes are importlib-lazy-loaded so that importing
the package does not pull in every schema dependency up front.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .advancedqueries import AdvancedHuntingQueriesEndpoint
    from .alerts import AlertsEndpoint, AlertsResults
    from .authenticatedScan import (
        AuthenticatedDefinitionsEndpoint,
        DeviceAuthenticatedAgentsEndpoint,
    )
    from .base import BaseEndpoint, BasePayload, BaseQuery, BaseResults
    from .browserExtension import BrowserExtensionEndpoint
    from .certificateInventory import CertificateInventoryEndpoint
    from .deviceAvHealth import DeviceAVHealthEndpoint
    from .deviceGroups import DeviceGroupsEndpoint
    from .domain import DomainEndpoint, DomainResults
    from .files import FileEndpoint, FileResults
    from .firmware import (
        AssetHardwareFirmwareResults,
        FirmwareEndpoint,
        FirmwareResults,
    )
    from .incidents import IncidentsEndpoint
    from .indicators import IndicatorsEndpoint, IndicatorsResults
    from .investigations import InvestigationsEndpoint
    from .ips import IPEndpoint, IPResults
    from .library import LibraryFilesEndpoint, LibraryFilesResults
    from .machineActions import (
        ActionAvailabilityStatusResults,
        MachineActionsEndpoint,
        MachineActionsResults,
    )
    from .machines import (
        AssetBaselineAssessmentResults,
        MachineReferencesResults,
        MachineResults,
        MachinesEndpoint,
    )
    from .misc import ProductDTOResults, PublicProductDTOResults
    from .recommendations import RecommendationResults, RecommendationsEndpoint
    from .remediations import RemediationEndpoint, RemediationResults
    from .score import ScoreEndpoint, ScoreResults
    from .securityBaseline import (
        AssetConfigurationResults,
        BaselineConfigurationEndpoint,
        BaselineConfigurationResults,
    )
    from .settings import DataExportSettingsEndpoint, DataExportSettingsResults
    from .software import (
        AssetNonCPESoftwareResults,
        AssetSoftwareResults,
        DistributionDTOResults,
        SoftwareEndpoint,
        SoftwareResults,
    )
    from .users import UserEndpoint, UserResults
    from .vulnerabilities import (
        AssetVulnerabilityResults,
        DeltaAssetVulnerabilityResults,
        VulnerabilityDTOResults,
        VulnerabilityEndpoint,
        VulnerabilityResults,
    )

_NAME_TO_MODULE = {
    "AdvancedHuntingQueriesEndpoint": "advancedqueries",
    "AlertsEndpoint": "alerts",
    "AlertsResults": "alerts",
    "AuthenticatedDefinitionsEndpoint": "authenticatedScan",
    "DeviceAuthenticatedAgentsEndpoint": "authenticatedScan",
    "BaseEndpoint": "base",
    "BaseResults": "base",
    "BaseQuery": "base",
    "BasePayload": "base",
    "BrowserExtensionEndpoint": "browserExtension",
    "CertificateInventoryEndpoint": "certificateInventory",
    "DeviceAVHealthEndpoint": "deviceAvHealth",
    "DeviceGroupsEndpoint": "deviceGroups",
    "DomainEndpoint": "domain",
    "DomainResults": "domain",
    "FileEndpoint": "files",
    "FileResults": "files",
    "FirmwareEndpoint": "firmware",
    "FirmwareResults": "firmware",
    "AssetHardwareFirmwareResults": "firmware",
    "IncidentsEndpoint": "incidents",
    "IndicatorsEndpoint": "indicators",
    "IndicatorsResults": "indicators",
    "InvestigationsEndpoint": "investigations",
    "IPEndpoint": "ips",
    "IPResults": "ips",
    "LibraryFilesEndpoint": "library",
    "LibraryFilesResults": "library",
    "MachineActionsEndpoint": "machineActions",
    "MachineActionsResults": "machineActions",
    "ActionAvailabilityStatusResults": "machineActions",
    "MachinesEndpoint": "machines",
    "MachineResults": "machines",
    "MachineReferencesResults": "machines",
    "AssetBaselineAssessmentResults": "machines",
    "ProductDTOResults": "misc",
    "PublicProductDTOResults": "misc",
    "RecommendationsEndpoint": "recommendations",
    "RecommendationResults": "recommendations",
    "RemediationEndpoint": "remediations",
    "RemediationResults": "remediations",
    "ScoreEndpoint": "score",
    "ScoreResults": "score",
    "BaselineConfigurationEndpoint": "securityBaseline",
    "BaselineConfigurationResults": "securityBaseline",
    "AssetConfigurationResults": "securityBaseline",
    "DataExportSettingsEndpoint": "settings",
    "DataExportSettingsResults": "settings",
    "SoftwareEndpoint": "software",
    "SoftwareResults": "software",
    "DistributionDTOResults": "software",
    "AssetSoftwareResults": "software",
    "AssetNonCPESoftwareResults": "software",
    "UserEndpoint": "users",
    "UserResults": "users",
    "VulnerabilityEndpoint": "vulnerabilities",
    "VulnerabilityResults": "vulnerabilities",
    "VulnerabilityDTOResults": "vulnerabilities",
    "AssetVulnerabilityResults": "vulnerabilities",
    "DeltaAssetVulnerabilityResults": "vulnerabilities",
}


def __getattr__(name: str) -> object:
    """Lazily import schema constants on first access (PEP 562).

    The resolved value is written back into the module's globals so
    subsequent accesses skip this function entirely.
    """
    module_name = _NAME_TO_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(f".{module_name}", __name__)
    value = getattr(module, name)
    globals()[name] = value  # cache: subsequent access bypasses __getattr__
    return value


__all__ = [
    # Advanced Hunting Queries
    "AdvancedHuntingQueriesEndpoint",
    # Alerts
    "AlertsEndpoint",
    "AlertsResults",
    # Authenticated Scan
    "AuthenticatedDefinitionsEndpoint",
    "DeviceAuthenticatedAgentsEndpoint",
    # Base Endpoint
    "BaseEndpoint",
    "BaseResults",
    "BaseQuery",
    "BasePayload",
    # Browser Extension
    "BrowserExtensionEndpoint",
    # Certificate Inventory
    "CertificateInventoryEndpoint",
    # Device AV Health
    "DeviceAVHealthEndpoint",
    # Device Groups
    "DeviceGroupsEndpoint",
    # Domain
    "DomainEndpoint",
    "DomainResults",
    # Files
    "FileEndpoint",
    "FileResults",
    # Firmware
    "FirmwareEndpoint",
    "FirmwareResults",
    "AssetHardwareFirmwareResults",
    # Incidents
    "IncidentsEndpoint",
    # Indicators
    "IndicatorsEndpoint",
    "IndicatorsResults",
    # Investigations
    "InvestigationsEndpoint",
    # IPs
    "IPEndpoint",
    "IPResults",
    # Library Files
    "LibraryFilesEndpoint",
    "LibraryFilesResults",
    # Machine Actions
    "MachineActionsEndpoint",
    "MachineActionsResults",
    "ActionAvailabilityStatusResults",
    # Machines
    "MachinesEndpoint",
    "MachineResults",
    "MachineReferencesResults",
    "AssetBaselineAssessmentResults",
    # Misc
    "ProductDTOResults",
    "PublicProductDTOResults",
    # Recommendations
    "RecommendationsEndpoint",
    "RecommendationResults",
    # Remediations
    "RemediationEndpoint",
    "RemediationResults",
    # Score
    "ScoreEndpoint",
    "ScoreResults",
    # Security Baseline
    "BaselineConfigurationEndpoint",
    "BaselineConfigurationResults",
    "AssetConfigurationResults",
    # Settings
    "DataExportSettingsEndpoint",
    "DataExportSettingsResults",
    # Software
    "SoftwareEndpoint",
    "SoftwareResults",
    "DistributionDTOResults",
    "AssetSoftwareResults",
    "AssetNonCPESoftwareResults",
    # User
    "UserEndpoint",
    "UserResults",
    # Vulnerabilities
    "VulnerabilityEndpoint",
    "VulnerabilityResults",
    "VulnerabilityDTOResults",
    "AssetVulnerabilityResults",
    "DeltaAssetVulnerabilityResults",
]
