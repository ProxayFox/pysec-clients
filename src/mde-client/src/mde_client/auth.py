"""Authentication primitives for the Microsoft Defender for Endpoint client.

This module owns the OAuth2 client-credentials flow used by `MDEClient` to
acquire bearer tokens for the Defender API. It wraps MSAL so endpoint code can
simply read `MSALAuth.token` on each request without worrying about cache
hits, expiry, or refresh.

Exports:
    MSALAuth: Confidential-client wrapper that acquires and caches tokens.
    AuthenticationError: Raised when MSAL fails to return an access token.
"""

import msal


class MSALAuth:
    """OAuth2 client-credentials token acquisition for the Defender API.

    Wraps `msal.ConfidentialClientApplication` and exposes a single `token`
    property that returns a current bearer token, transparently using the
    underlying MSAL cache to avoid unnecessary round-trips to Azure AD.

    Args:
        tenant_id: Azure AD tenant ID for the application registration.
        client_id: App registration client ID.
        client_secret: App registration client secret.
        token_cache: Optional `msal.TokenCache` (or `SerializableTokenCache`)
            for cross-process or persistent caching. Defaults to a new
            in-memory `msal.TokenCache()`.
    """

    _SCOPES = ["https://api.securitycenter.microsoft.com/.default"]

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
        *,
        token_cache: msal.TokenCache | None = None,
    ) -> None:
        """Configure the underlying MSAL confidential-client application."""
        self._app = msal.ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
            token_cache=token_cache or msal.TokenCache(),
        )

    @property
    def token(self) -> str:
        """Return a valid bearer token for the Defender API.

        MSAL serves the token from its cache when one is still valid, and
        fetches a fresh token from Azure AD otherwise. Callers should read
        this property on every request rather than caching the string
        themselves.

        Returns:
            A bearer access token suitable for the `Authorization` header.

        Raises:
            AuthenticationError: If MSAL fails to return a token (missing
                credentials, invalid authority, app permission issues, etc.).
        """
        result = self._app.acquire_token_for_client(scopes=self._SCOPES)

        if result is None:
            raise AuthenticationError(
                "MSAL returned None — check your credentials and authority URL."
            )

        if "access_token" not in result:
            error = result.get("error", "unknown_error")
            description = result.get("error_description", "No description provided.")
            raise AuthenticationError(f"{error}: {description}")

        return result["access_token"]


class AuthenticationError(Exception):
    """Raised when MSAL fails to acquire an access token for the Defender API."""
