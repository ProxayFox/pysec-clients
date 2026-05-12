# `MDEClient`

`MDEClient` is the top-level entry point for the package.

## Constructor

```python
MDEClient(
    tenant_id: str,
    client_id: str,
    client_secret: str,
    *,
    base_url: str = "https://api.securitycenter.microsoft.com",
    token_cache: msal.TokenCache | None = None,
    http_client: httpx.Client | None = None,
)
```

## Parameters

- `tenant_id`: Azure AD tenant ID.
- `client_id`: app registration client ID.
- `client_secret`: app registration client secret.
- `base_url`: optional override for the Defender API base URL.
- `token_cache`: optional MSAL token cache.
- `http_client`: optional pre-configured `httpx.Client`.

## Lifecycle

`MDEClient` is a context manager:

```python
with MDEClient(...) as client:
    rows = client.machines.get_all().to_dicts()
```

If you do not use the context-manager form, call `close()` when you are done.

## Top-level endpoint properties

- `advanced_queries`
- `alerts`
- `authenticated_definitions`
- `authenticated_agents`
- `browser_extension`
- `certificate_inventory`
- `device_av_health`
- `domain`
- `files`
- `indicators`
- `investigations`
- `ips`
- `library`
- `machine_actions`
- `machines`
- `recommendations`
- `remediations`
- `score`
- `baseline_configurations`
- `software`
- `user`
- `vulnerabilities`

See [Endpoint index](endpoints/index.md) for endpoint-specific pages.

## Public top-level imports

The package exports these names from `mde_client`:

- `MDEClient`
- `AuthenticationError`
- `ViaFiles`
- `ViaFilesConfig`
- `EmptyExportBlobError`
