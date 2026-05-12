# Inject a Custom HTTP Client or Token Cache

Use this guide when you need custom HTTP behavior, a mock transport for tests, or persistent MSAL token caching.

## Inject an `httpx.Client`

```python
import httpx

from mde_client import MDEClient

http_client = httpx.Client(timeout=httpx.Timeout(60.0))

client = MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    http_client=http_client,
)
```

This is useful for custom transports, proxy configuration, or explicit timeouts.

## Inject a token cache

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

## Combine both for tests

```python
import httpx
import msal

from mde_client import MDEClient

client = MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    http_client=httpx.Client(transport=mock_transport),
    token_cache=msal.TokenCache(),
)
```

## Close injected clients

If you inject your own `httpx.Client`, keep ownership in mind. Using `with MDEClient(...) as client:` still closes the underlying client when the context exits.

## Next references

- [MDEClient reference](../reference/mde-client.md)
- [Why the client supports dependency injection](../explanation/dependency-injection.md)
