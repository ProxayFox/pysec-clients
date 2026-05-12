import msal
import httpx
from typing import TYPE_CHECKING

from .auth import MSALAuth

if TYPE_CHECKING:
    from .endpoints import (
        AlertsEndpoint,
        AuthenticatedDefinitionsEndpoint,
        DeviceAuthenticatedAgentsEndpoint,
        BaseEndpoint,
        BrowserExtensionEndpoint,
        CertificateInventoryEndpoint,
        DeviceAVHealthEndpoint,
        DomainEndpoint,
        FileEndpoint,
        IndicatorsEndpoint,
        InvestigationsEndpoint,
        IPEndpoint,
        LibraryFilesEndpoint,
        MachineActionsEndpoint,
        MachinesEndpoint,
        RecommendationsEndpoint,
        RemediationEndpoint,
        ScoreEndpoint,
        BaselineConfigurationEndpoint,
        SoftwareEndpoint,
        UserEndpoint,
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
    def alerts(self) -> AlertsEndpoint:
        from .endpoints import AlertsEndpoint

        return AlertsEndpoint(self._http, self._auth)

    @property
    def authenticated_definitions(self) -> AuthenticatedDefinitionsEndpoint:
        from .endpoints import AuthenticatedDefinitionsEndpoint

        return AuthenticatedDefinitionsEndpoint(self._http, self._auth)

    @property
    def authenticated_agents(self) -> DeviceAuthenticatedAgentsEndpoint:
        from .endpoints import DeviceAuthenticatedAgentsEndpoint

        return DeviceAuthenticatedAgentsEndpoint(self._http, self._auth)

    @property
    def misc(self) -> BaseEndpoint:
        from .endpoints import BaseEndpoint

        return BaseEndpoint(self._http, self._auth)

    @property
    def browser_extension(self) -> BrowserExtensionEndpoint:
        from .endpoints import BrowserExtensionEndpoint

        return BrowserExtensionEndpoint(self._http, self._auth)

    @property
    def certificate_inventory(self) -> CertificateInventoryEndpoint:
        from .endpoints import CertificateInventoryEndpoint

        return CertificateInventoryEndpoint(self._http, self._auth)

    @property
    def device_av_health(self) -> DeviceAVHealthEndpoint:
        from .endpoints import DeviceAVHealthEndpoint

        return DeviceAVHealthEndpoint(self._http, self._auth)

    @property
    def domain(self) -> DomainEndpoint:
        from .endpoints import DomainEndpoint

        return DomainEndpoint(self._http, self._auth)

    @property
    def files(self) -> FileEndpoint:
        from .endpoints import FileEndpoint

        return FileEndpoint(self._http, self._auth)

    @property
    def indicators(self) -> IndicatorsEndpoint:
        from .endpoints import IndicatorsEndpoint

        return IndicatorsEndpoint(self._http, self._auth)

    @property
    def investigations(self) -> InvestigationsEndpoint:
        from .endpoints import InvestigationsEndpoint

        return InvestigationsEndpoint(self._http, self._auth)

    @property
    def ips(self) -> IPEndpoint:
        from .endpoints import IPEndpoint

        return IPEndpoint(self._http, self._auth)

    @property
    def library(self) -> LibraryFilesEndpoint:
        from .endpoints import LibraryFilesEndpoint

        return LibraryFilesEndpoint(self._http, self._auth)

    @property
    def machine_actions(self) -> MachineActionsEndpoint:
        from .endpoints import MachineActionsEndpoint

        return MachineActionsEndpoint(self._http, self._auth)

    @property
    def machines(self) -> MachinesEndpoint:
        from .endpoints import MachinesEndpoint

        return MachinesEndpoint(self._http, self._auth)

    @property
    def recommendations(self) -> RecommendationsEndpoint:
        from .endpoints import RecommendationsEndpoint

        return RecommendationsEndpoint(self._http, self._auth)

    @property
    def remediations(self) -> RemediationEndpoint:
        from .endpoints import RemediationEndpoint

        return RemediationEndpoint(self._http, self._auth)

    @property
    def score(self) -> ScoreEndpoint:
        from .endpoints import ScoreEndpoint

        return ScoreEndpoint(self._http, self._auth)

    @property
    def baseline_configurations(self) -> BaselineConfigurationEndpoint:
        from .endpoints import BaselineConfigurationEndpoint

        return BaselineConfigurationEndpoint(self._http, self._auth)

    @property
    def software(self) -> SoftwareEndpoint:
        from .endpoints import SoftwareEndpoint

        return SoftwareEndpoint(self._http, self._auth)

    @property
    def user(self) -> UserEndpoint:
        from .endpoints import UserEndpoint

        return UserEndpoint(self._http, self._auth)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "MDEClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()
