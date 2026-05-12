# Authenticate with Client Credentials

Use this guide when you already know you want app-only authentication and need the package-level steps.

## What you need

- tenant ID
- client ID
- client secret
- Defender application permissions granted to the app registration

## Create the client

```python
from mde_client import MDEClient

client = MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
)
```

`MDEClient` uses MSAL under the hood and requests the Defender default scope.

## Reuse the client safely

Prefer the context-manager form so the underlying `httpx.Client` is closed promptly:

```python
from mde_client import MDEClient

with MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
) as client:
    machines = client.machines.get_all().to_dicts()
```

If you do not use `with`, call `client.close()` yourself.

## Persist tokens with a cache

If you want MSAL token caching outside the default in-memory behavior, inject a cache object:

```python
import msal

from mde_client import MDEClient

cache = msal.SerializableTokenCache()

client = MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    token_cache=cache,
)
```

## Handle authentication failures

Authentication failures raise `AuthenticationError`:

```python
from mde_client import AuthenticationError, MDEClient

try:
    with MDEClient(
        tenant_id="YOUR_TENANT_ID",
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
    ) as client:
        client.machines.get_all().to_dicts()
except AuthenticationError as exc:
    print(exc)
```

## Next references

- [Authentication reference](../reference/authentication.md)
- [MDEClient reference](../reference/mde-client.md)
