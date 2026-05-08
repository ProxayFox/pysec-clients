# mde-client

Python client for the [Microsoft Defender for Endpoint](https://learn.microsoft.com/en-us/defender-endpoint/) API.

## Install

```bash
uv add mde-client
```

## Usage

```python
from mde_client import MDEClient
from mde_client.endpoints.machines import MachinesQuery

with MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
) as client:
    # Fetch all active machines as a PyArrow Table
    table = client.machines.get_all(
        MachinesQuery(health_status="Active")
    )
    print(table.to_pandas())

    # Fetch a single machine by ID
    machine = client.machines.get("machine-guid")
    print(machine.computer_dns_name)
```

## Authentication

`MDEClient` authenticates via the OAuth 2.0 client-credentials flow using [MSAL](https://github.com/AzureAD/microsoft-authentication-library-for-python). You need an Azure AD app registration with the **WindowsDefenderATP** API permissions.

An optional `token_cache` (`msal.SerializableTokenCache`) can be injected for persistent token storage:

```python
import msal

cache = msal.SerializableTokenCache()
client = MDEClient(..., token_cache=cache)
```

## Architecture

```text
mde_client/
  __init__.py       # public API: MDEClient, AuthenticationError
  client.py         # MDEClient — session lifecycle, lazy endpoint properties
  auth.py           # MSALAuth — token acquisition and caching
  endpoints/
    machines.py     # MachinesEndpoint, MachinesQuery, MachineRecord
```

**Pattern:** each endpoint module contains a query model, one or more response models, and an endpoint class. `MDEClient` exposes each endpoint as a `@property`.

| Return type | When |
| ----------- | ---- |
| `pa.Table` (PyArrow) | Collection endpoints (`get_all`, `logon_users`) |
| Pydantic model | Single-item endpoints (`get`) |

## Available endpoints

### `client.machines`

| Method | Returns | Description |
| ------ | ------- | ----------- |
| `get_all(query?)` | `pa.Table` | List machines with optional OData filters |
| `get(machine_id)` | `MachineRecord` | Fetch a single machine by GUID |
| `logon_users(machine_id)` | `pa.Table` | Logon users for a machine |

### `MachinesQuery` filters

All fields are optional. Pydantic validates constraints at construction time.

| Field | Type | OData mapping |
| ----- | ---- | ------------- |
| `health_status` | `HealthType` | `healthStatus eq '…'` |
| `os_platform` | `str` | `osPlatform eq '…'` |
| `risk_score` | `LevelType` | `riskScore eq '…'` |
| `exposure_level` | `LevelType` | `exposureLevel eq '…'` |
| `onboarding_status` | `OnboardingType` | `onboardingStatus eq '…'` |
| `machine_id` | `str \| list[str]` | `id eq '…'` (OR-joined) |
| `machine_tags` | `str \| list[str]` | `machineTags/any(…)` |
| `last_seen_since` | `datetime` | `lastSeen ge …` |
| `page_size` | `int` (1–10 000) | Controls pagination batch size |
| `top` / `skip` | `int` | `$top` / `$skip` |

## Testability

Both `httpx.Client` and `msal.TokenCache` are constructor-injected, so tests can substitute fakes without mocking:

```python
client = MDEClient(
    ...,
    http_client=httpx.Client(transport=mock_transport),
    token_cache=msal.TokenCache(),
)
```

## License

[AGPL-3.0](../../LICENSE)
