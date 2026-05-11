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
    from .alerts import AlertsEndpoint
    from .browserExtension import BrowserExtensionEndpoint
    from .machines import MachinesEndpoint
    from .authenticatedScan import (
        AuthenticatedDefinitionsEndpoint,
        DeviceAuthenticatedAgentsEndpoint,
    )

_NAME_TO_MODULE = {
    "AlertsEndpoint": "alerts",
    "BrowserExtensionEndpoint": "browserExtension",
    "MachinesEndpoint": "machines",
    "AuthenticatedDefinitionsEndpoint": "authenticatedScan",
    "DeviceAuthenticatedAgentsEndpoint": "authenticatedScan",
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
    # Browser Extension
    "BrowserExtensionEndpoint",
    # Machines
    "MachinesEndpoint",
    # Authenticated Scan
    "AuthenticatedDefinitionsEndpoint",
    "DeviceAuthenticatedAgentsEndpoint",
]
