from __future__ import annotations

import logging

from datetime import datetime
from typing import Literal, Any, TYPE_CHECKING

from .base import BaseQuery, BaseEndpoint

if TYPE_CHECKING:
    import pyarrow as pa

log = logging.getLogger(__name__)

LEVELTYPE = Literal["None", "Informational", "Low", "Medium", "High"]
ONBOARDINGTYPE = Literal[
    "Onboarded", "CanBeOnboarded", "Unsupported", "InsufficientInfo"
]
HEALTHTYPE = Literal[
    "Active",
    "Inactive",
    "ImpairedCommunication",
    "NoSensorData",
    "NoSensorDataImpairedCommunication",
    "Unknown",
]


class MachinesQuery(BaseQuery):
    """Query parameters for the /api/machines endpoint.

    All fields are optional — omitted fields are simply not sent.
    Pydantic enforces the constraints (ge/le) at construction time,
    so invalid values are caught before hitting the wire.

    Example:
        query = MachinesQuery(healthStatus="Active", pageSize=500)
    """

    computerDnsName: str | None = None
    id: str | list[str] | None = None
    version: str | None = None
    deviceValue: LEVELTYPE | None = None
    aadDeviceId: str | list[str] | None = None
    machineTags: str | list[str] | None = None
    lastSeen: datetime | None = None
    exposureLevel: LEVELTYPE | None = None
    onboardingStatus: ONBOARDINGTYPE | None = None
    lastIpAddress: str | None = None
    healthStatus: HEALTHTYPE | None = None
    osPlatform: str | None = None
    riskScore: LEVELTYPE | None = None
    rbacGroupId: str | None = None


class MachineResults:
    """Lazy collection handle — holds the query intent, fires on terminal call.

    Constructed by ``MachinesEndpoint.get_all()``; no HTTP request is issued
    until a terminal method (``to_json``, ``to_arrow``, ``to_polars``) is
    called.  The internal cache is an ``ArrowRecordContainer`` that receives
    pages streamed directly from the paginator — a full ``list[dict]`` is
    never built in memory.

    Terminal methods:
        - ``to_json()``   — ``list[dict[str, Any]]`` (always available)
        - ``to_arrow()``  — ``pa.Table``  (requires the ``arrow`` extra)
        - ``to_polars()`` — ``pl.DataFrame`` (requires the ``polars`` extra)

    Call ``refresh()`` to discard cached data and re-fetch on the next
    terminal call.  ``refresh()`` returns ``self`` so the caller must
    choose a format explicitly::

        results.refresh().to_arrow()
    """

    def __init__(
        self,
        endpoint: MachinesEndpoint,
        params: dict[str, str],
    ) -> None:
        self._endpoint = endpoint
        self._params = params
        self._container: Any = None  # ArrowRecordContainer once fetched

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure_fetched(self) -> None:
        """Populate the container on first access; subsequent calls are a no-op."""
        if self._container is not None:
            return

        # TODO: define MACHINES_SCHEMA (pa.Schema) for the /api/machines
        # response so ArrowRecordContainer can enforce column types and
        # handle coercion.  Until then, raise so callers get a clear signal.
        raise NotImplementedError(
            "MACHINES_SCHEMA is not yet defined. A PyArrow schema describing "
            "the /api/machines response fields is required before "
            "ArrowRecordContainer can be initialised."
        )

    # ------------------------------------------------------------------
    # Terminal methods
    # ------------------------------------------------------------------

    def to_json(self) -> list[dict[str, Any]]:
        """Materialise results as plain Python dicts (no extra deps needed)."""
        self._ensure_fetched()
        return self._container.to_table().to_pylist()

    def to_arrow(self) -> pa.Table:
        """Materialise results as a PyArrow ``Table``.

        Requires the ``arrow`` extra::

            uv add mde-client[arrow]
        """
        try:
            import pyarrow as _pa  # noqa: F401
        except ImportError:
            raise ImportError(
                "Arrow support requires the 'arrow' extra. "
                "Install with: uv add mde-client[arrow]"
            ) from None

        self._ensure_fetched()
        return self._container.to_table()

    def to_polars(self):  # -> pl.DataFrame
        """Materialise results as a Polars ``DataFrame``.

        Requires the ``polars`` extra::

            uv add mde-client[polars]
        """
        try:
            import polars as _pl  # noqa: F401
        except ImportError:
            raise ImportError(
                "Polars support requires the 'polars' extra. "
                "Install with: uv add mde-client[polars]"
            ) from None

        self._ensure_fetched()
        return self._container.to_polars_frame()

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def refresh(self) -> MachineResults:
        """Discard cached data so the next terminal call re-fetches.

        Returns ``self`` so the caller chooses the output format explicitly::

            results.refresh().to_arrow()
        """
        self._container = None
        return self


class MachinesEndpoint(BaseEndpoint):
    """Client for the /api/machines endpoint.

    This is not intended to be used directly. Instead, use MDEClient.machines.

    Returns a lazy ``MachineResults`` handle — no HTTP request is issued
        until a terminal method is called::

            results = client.machines.get_all(query)
            records = results.to_json()      # list[dict]
            table   = results.to_arrow()     # pa.Table  (requires [arrow])
            df      = results.to_polars()    # DataFrame (requires [polars])

        Call ``results.refresh()`` to discard cached data and re-fetch.
    """

    _PATH = "/api/machines"

    def get_all(self, query: MachinesQuery | None = None) -> MachineResults:
        """Get all machines, with optional filtering.
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-machines
        """
        params = query.to_odata_filters if query else {}
        return MachineResults(self, params)

    def get(self, id: str | None = None):
        """Get machine by ID
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-by-id
        """
        pass

    def logonusers(self, id: str):
        """Get machine logon users for a machine
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-log-on-users
        """
        # path = f"{self._PATH}/{id}/logonusers"

        pass

    def alerts(self, id: str):
        """Get machine related alerts
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-machine-related-alerts
        """
        # path = f"{self._PATH}/{id}/alerts"

        pass

    def software(self, id: str):
        """Get installed software
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-installed-software
        """
        # path = f"{self._PATH}/{id}/software"

        pass

    def vulnerabilities(self, id: str):
        """Get discovered vulnerabilities for a machine.
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-discovered-vulnerabilities
        """
        # path = f"{self._PATH}/{id}/vulnerabilities"

        pass

    def recommendations(self, id: str):
        """Get security recommendations for a machine.
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-security-recommendations
        """
        # path = f"{self._PATH}/{id}/recommendations"

        pass

    def tags(self, id: str):
        """Find devices by tag API
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/find-machines-by-tag
        """
        # path = f"{self._PATH}/{id}/tags"

        pass

    def getmissingkbs(self, id: str):
        """Get missing KBs by device ID
        Docs: https://learn.microsoft.com/en-us/defender-endpoint/api/get-missing-kbs-machine
        """
        # path = f"{self._PATH}/{id}/getmissingkbs"

        pass


class MachineNotFoundError(Exception):
    def __init__(self, machine_id: str) -> None:
        super().__init__(f"Machine '{machine_id}' not found.")
        self.machine_id = machine_id
