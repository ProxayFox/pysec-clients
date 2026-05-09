import msal
import httpx

from .auth import MSALAuth
from .endpoints.base import BaseEndpoint
from .endpoints.machines import MachinesEndpoint


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
        return BaseEndpoint(self._http, self._auth)

    @property
    def machines(self) -> MachinesEndpoint:
        return MachinesEndpoint(self._http, self._auth)

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
