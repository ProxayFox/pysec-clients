# Authentication

The package uses MSAL client-credentials authentication.

## What the client does

- builds an `msal.ConfidentialClientApplication`
- uses the authority `https://login.microsoftonline.com/{tenant_id}`
- requests the Defender default scope
- raises `AuthenticationError` when MSAL does not return an access token

## Inputs

Authentication is driven by these constructor values on `MDEClient`:

- `tenant_id`
- `client_id`
- `client_secret`
- optional `token_cache`

## Token cache behavior

If you do not pass a token cache, the client uses an in-memory `msal.TokenCache`. If you need persistence, inject your own cache implementation.

## Error model

`AuthenticationError` is raised when:

- MSAL returns `None`
- MSAL returns a result without `access_token`

HTTP-level API failures that happen after authentication are not wrapped as `AuthenticationError`; they bubble up through `httpx` status handling.

## See also

- [Authenticate with client credentials](../how-to/authenticate-with-client-credentials.md)
- [MDEClient](mde-client.md)
