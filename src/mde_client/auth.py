import msal


class MSALAuth:
    """Handles OAuth token acquisition and caching via MSAL.

    Accepts an optional token_cache so callers can inject a
    SerializableTokenCache for persistence — or get in-memory by default.
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
        self._app = msal.ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
            token_cache=token_cache or msal.TokenCache(),
        )

    @property
    def token(self) -> str:
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
    """Raised when MSAL fails to acquire a token."""
