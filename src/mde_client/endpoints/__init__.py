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
    from .alerts import AlertsEndpoint, AlertsResults
    from .authenticatedScan import (
        AuthenticatedDefinitionsEndpoint,
        DeviceAuthenticatedAgentsEndpoint,
    )
    from .base import BaseEndpoint, BaseResults, BaseQuery, BasePayload
    from .browserExtension import BrowserExtensionEndpoint
    from .certificateInventory import CertificateInventoryEndpoint
    from .deviceAvHealth import DeviceAVHealthEndpoint
    from .domain import DomainEndpoint, DomainResults
    from .files import FileEndpoint, FileResults
    from .indicators import IndicatorsEndpoint, IndicatorsResults
    from .investigations import InvestigationsEndpoint
    from .ips import IPEndpoint, IPResults
    from .library import LibraryFilesEndpoint, LibraryFilesResults
    from .machineActions import MachineActionsEndpoint, MachineActionsResults
    from .machines import (
        MachinesEndpoint,
        MachineResults,
        MachineReferencesResults,
        AssetBaselineAssessmentResults,
    )
    from .misc import ProductDTOResults
    from .recommendations import RecommendationsEndpoint, RecommendationResults
    from .remediations import RemediationEndpoint, RemediationResults
    from .score import ScoreEndpoint, ScoreResults
    from .securityBaseline import (
        BaselineConfigurationEndpoint,
        BaselineConfigurationResults,
    )
    from .software import SoftwareEndpoint, SoftwareResults, DistributionDTOResults
    from .users import UserEndpoint, UserResults
    from .vulnerabilities import (
        VulnerabilityEndpoint,
        VulnerabilityResults,
        VulnerabilityDTOResults,
    )

_NAME_TO_MODULE = {
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
    "DomainEndpoint": "domain",
    "DomainResults": "domain",
    "FileEndpoint": "files",
    "FileResults": "files",
    "IndicatorsEndpoint": "indicators",
    "IndicatorsResults": "indicators",
    "InvestigationsEndpoint": "investigations",
    "IPEndpoint": "ips",
    "IPResults": "ips",
    "LibraryFilesEndpoint": "library",
    "LibraryFilesResults": "library",
    "MachineActionsEndpoint": "machineActions",
    "MachineActionsResults": "machineActions",
    "MachinesEndpoint": "machines",
    "MachineResults": "machines",
    "MachineReferencesResults": "machines",
    "AssetBaselineAssessmentResults": "machines",
    "ProductDTOResults": "misc",
    "RecommendationsEndpoint": "recommendations",
    "RecommendationResults": "recommendations",
    "RemediationEndpoint": "remediations",
    "RemediationResults": "remediations",
    "ScoreEndpoint": "score",
    "ScoreResults": "score",
    "BaselineConfigurationEndpoint": "securityBaseline",
    "BaselineConfigurationResults": "securityBaseline",
    "SoftwareEndpoint": "software",
    "SoftwareResults": "software",
    "DistributionDTOResults": "software",
    "UserEndpoint": "user",
    "UserResults": "user",
    "VulnerabilityEndpoint": "vulnerabilities",
    "VulnerabilityResults": "vulnerabilities",
    "VulnerabilityDTOResults": "vulnerabilities",
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
    # Domain
    "DomainEndpoint",
    "DomainResults",
    # Files
    "FileEndpoint",
    "FileResults",
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
    # Machines
    "MachinesEndpoint",
    "MachineResults",
    "MachineReferencesResults",
    "AssetBaselineAssessmentResults",
    # Misc
    "ProductDTOResults",
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
    # Software
    "SoftwareEndpoint",
    "SoftwareResults",
    "DistributionDTOResults",
    # User
    "UserEndpoint",
    "UserResults",
    # Vulnerabilities
    "VulnerabilityEndpoint",
    "VulnerabilityResults",
    "VulnerabilityDTOResults",
]
