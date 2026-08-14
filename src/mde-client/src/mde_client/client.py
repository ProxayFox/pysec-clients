from typing import TYPE_CHECKING, Self

import httpx
import msal

from .auth import MSALAuth

if TYPE_CHECKING:
    from .endpoints import (
        AdvancedHuntingQueriesEndpoint,
        AlertsEndpoint,
        AuthenticatedDefinitionsEndpoint,
        BaseEndpoint,
        BaselineConfigurationEndpoint,
        BrowserExtensionEndpoint,
        CertificateInventoryEndpoint,
        DataExportSettingsEndpoint,
        DeviceAuthenticatedAgentsEndpoint,
        DeviceAVHealthEndpoint,
        DeviceGroupsEndpoint,
        DomainEndpoint,
        FileEndpoint,
        FirmwareEndpoint,
        IncidentsEndpoint,
        IndicatorsEndpoint,
        InvestigationsEndpoint,
        IPEndpoint,
        LibraryFilesEndpoint,
        MachineActionsEndpoint,
        MachinesEndpoint,
        RecommendationsEndpoint,
        RemediationEndpoint,
        ScoreEndpoint,
        SoftwareEndpoint,
        UserEndpoint,
        VulnerabilityEndpoint,
    )


class MDEClient:
    """Top-level client for the Microsoft Defender for Endpoint API.

    Manages the HTTP session and auth lifecycle. Endpoint-specific
    functionality is accessed via properties (e.g. client.machines).

    Args:
        tenant_id:     Azure AD tenant ID.
        client_id:     App registration client ID.
        client_secret: App registration client secret.
        base_url:      Override the default MDE API base URL.
        token_cache:   Inject an msal.SerializableTokenCache for persistent
                       caching. Defaults to in-memory (msal.TokenCache).
        http_client:   Inject a pre-configured httpx.Client, e.g. for testing
                       or to set custom timeouts/proxies.

    Example:
        client = MDEClient(
            tenant_id="...",
            client_id="...",
            client_secret="...",
        )
        table = client.machines.get_all(MachinesQuery(health_status="Active"))
    """

    _DEFAULT_BASE_URL = "https://api.securitycenter.microsoft.com"

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        token_cache: msal.TokenCache | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._auth = MSALAuth(
            tenant_id,
            client_id,
            client_secret,
            token_cache=token_cache,
        )
        self._http = http_client or httpx.Client(
            base_url=base_url,
            timeout=httpx.Timeout(30.0),
        )

    # ------------------------------------------------------------------
    # Endpoints
    # ------------------------------------------------------------------

    @property
    def misc(self) -> BaseEndpoint:
        """Generic base endpoint for one-off API paths without a dedicated module."""
        from .endpoints import BaseEndpoint

        return BaseEndpoint(self._http, self._auth)

    @property
    def advanced_queries(self) -> AdvancedHuntingQueriesEndpoint:
        """Endpoint for `/api/advancedqueries/run` (Advanced Hunting KQL queries)."""
        from .endpoints import AdvancedHuntingQueriesEndpoint

        return AdvancedHuntingQueriesEndpoint(self._http, self._auth)

    @property
    def alerts(self) -> AlertsEndpoint:
        """Endpoint for `/api/alerts` and related alert lookups."""
        from .endpoints import AlertsEndpoint

        return AlertsEndpoint(self._http, self._auth)

    @property
    def authenticated_definitions(self) -> AuthenticatedDefinitionsEndpoint:
        """Endpoint for authenticated-scan definitions."""
        from .endpoints import AuthenticatedDefinitionsEndpoint

        return AuthenticatedDefinitionsEndpoint(self._http, self._auth)

    @property
    def authenticated_agents(self) -> DeviceAuthenticatedAgentsEndpoint:
        """Endpoint for authenticated-scan device agents."""
        from .endpoints import DeviceAuthenticatedAgentsEndpoint

        return DeviceAuthenticatedAgentsEndpoint(self._http, self._auth)

    @property
    def browser_extension(self) -> BrowserExtensionEndpoint:
        """Endpoint for browser extension inventory and per-machine extensions."""
        from .endpoints import BrowserExtensionEndpoint

        return BrowserExtensionEndpoint(self._http, self._auth)

    @property
    def certificate_inventory(self) -> CertificateInventoryEndpoint:
        """Endpoint for certificate inventory export data."""
        from .endpoints import CertificateInventoryEndpoint

        return CertificateInventoryEndpoint(self._http, self._auth)

    @property
    def device_av_health(self) -> DeviceAVHealthEndpoint:
        """Endpoint for device antivirus health export data."""
        from .endpoints import DeviceAVHealthEndpoint

        return DeviceAVHealthEndpoint(self._http, self._auth)

    @property
    def device_groups(self) -> DeviceGroupsEndpoint:
        """Endpoint for device-group inventory."""
        from .endpoints import DeviceGroupsEndpoint

        return DeviceGroupsEndpoint(self._http, self._auth)

    @property
    def domain(self) -> DomainEndpoint:
        """Endpoint for alert-related domain lookups and stats."""
        from .endpoints import DomainEndpoint

        return DomainEndpoint(self._http, self._auth)

    @property
    def firmware(self) -> FirmwareEndpoint:
        """Endpoint for firmware inventory and per-asset firmware lookups."""
        from .endpoints import FirmwareEndpoint

        return FirmwareEndpoint(self._http, self._auth)

    @property
    def files(self) -> FileEndpoint:
        """Endpoint for file (hash) lookups and related machines/alerts/stats."""
        from .endpoints import FileEndpoint

        return FileEndpoint(self._http, self._auth)

    @property
    def incidents(self) -> IncidentsEndpoint:
        """Endpoint for `/api/incidents` (list and single-incident lookup)."""
        from .endpoints import IncidentsEndpoint

        return IncidentsEndpoint(self._http, self._auth)

    @property
    def indicators(self) -> IndicatorsEndpoint:
        """Endpoint for custom threat indicators (TI)."""
        from .endpoints import IndicatorsEndpoint

        return IndicatorsEndpoint(self._http, self._auth)

    @property
    def investigations(self) -> InvestigationsEndpoint:
        """Endpoint for automated investigation records."""
        from .endpoints import InvestigationsEndpoint

        return InvestigationsEndpoint(self._http, self._auth)

    @property
    def ips(self) -> IPEndpoint:
        """Endpoint for IP-address lookups and related alerts/stats."""
        from .endpoints import IPEndpoint

        return IPEndpoint(self._http, self._auth)

    @property
    def library(self) -> LibraryFilesEndpoint:
        """Endpoint for live-response library files (list, upload, delete)."""
        from .endpoints import LibraryFilesEndpoint

        return LibraryFilesEndpoint(self._http, self._auth)

    @property
    def machine_actions(self) -> MachineActionsEndpoint:
        """Endpoint for machine actions (isolate, scan, collect package, etc.)."""
        from .endpoints import MachineActionsEndpoint

        return MachineActionsEndpoint(self._http, self._auth)

    @property
    def machines(self) -> MachinesEndpoint:
        """Endpoint for machine inventory, lookups, tagging, and related data."""
        from .endpoints import MachinesEndpoint

        return MachinesEndpoint(self._http, self._auth)

    @property
    def recommendations(self) -> RecommendationsEndpoint:
        """Endpoint for TVM security recommendations."""
        from .endpoints import RecommendationsEndpoint

        return RecommendationsEndpoint(self._http, self._auth)

    @property
    def remediations(self) -> RemediationEndpoint:
        """Endpoint for TVM remediation activities."""
        from .endpoints import RemediationEndpoint

        return RemediationEndpoint(self._http, self._auth)

    @property
    def score(self) -> ScoreEndpoint:
        """Endpoint for exposure and secure-score reporting."""
        from .endpoints import ScoreEndpoint

        return ScoreEndpoint(self._http, self._auth)

    @property
    def baseline_configurations(self) -> BaselineConfigurationEndpoint:
        """Endpoint for security baseline configuration assessments."""
        from .endpoints import BaselineConfigurationEndpoint

        return BaselineConfigurationEndpoint(self._http, self._auth)

    @property
    def settings(self) -> DataExportSettingsEndpoint:
        """Endpoint for data-export (raw streaming) settings."""
        from .endpoints import DataExportSettingsEndpoint

        return DataExportSettingsEndpoint(self._http, self._auth)

    @property
    def software(self) -> SoftwareEndpoint:
        """Endpoint for software inventory and per-asset software lookups."""
        from .endpoints import SoftwareEndpoint

        return SoftwareEndpoint(self._http, self._auth)

    @property
    def user(self) -> UserEndpoint:
        """Endpoint for user-account lookups and related alerts/machines."""
        from .endpoints import UserEndpoint

        return UserEndpoint(self._http, self._auth)

    @property
    def vulnerabilities(self) -> VulnerabilityEndpoint:
        """Endpoint for vulnerability inventory and per-asset vulnerability lookups."""
        from .endpoints import VulnerabilityEndpoint

        return VulnerabilityEndpoint(self._http, self._auth)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args) -> None:
        self.close()
