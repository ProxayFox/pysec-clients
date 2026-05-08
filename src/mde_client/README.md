# mde-client

Python client for the [Microsoft Defender for Endpoint](https://learn.microsoft.com/en-us/defender-endpoint/) API.

The current package surface focuses on the machines endpoint and returns lazy result handles that can be materialized as JSON, PyArrow tables, or Polars DataFrames.

## Install

```bash
uv add mde-client
```

Optional extras for terminal conversions:

```bash
uv add mde-client[arrow]
uv add mde-client[arrow,polars]
```

Use the base install if you only need JSON output. Add extras when you want `to_arrow()` or `to_polars()`.

## Prerequisites

You need an Azure AD app registration that can use the OAuth 2.0 client-credentials flow against Microsoft Defender for Endpoint.

- Tenant ID
- Client ID
- Client secret
- Defender application permissions for your tenant's app registration

## Quick Start

```python
from mde_client import AuthenticationError, MDEClient
from mde_client.endpoints.machines import MachinesQuery

try:
    with MDEClient(
        tenant_id="YOUR_TENANT_ID",
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
    ) as client:
        results = client.machines.get_all(
            MachinesQuery(healthStatus="Active", page_size=500)
        )

        machines = results.to_json()
        print(f"Fetched {len(machines)} machines")

        machine = client.machines.get("machine-guid").to_json()[0]
        print(machine["computerDnsName"])

        logon_users = client.machines.logonusers("machine-guid").to_json()
        print(logon_users[:3])
except AuthenticationError as exc:
    print(f"Authentication failed: {exc}")
```

## Authentication

`MDEClient` authenticates with [MSAL](https://github.com/AzureAD/microsoft-authentication-library-for-python) using the client-credentials flow and the Defender default scope.

An optional token cache can be injected for persistent storage:

```python
import msal

cache = msal.SerializableTokenCache()

client = MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    token_cache=cache,
)
```

`MDEClient` also accepts an injected `httpx.Client` for testing, custom transports, timeouts, or proxy configuration.

## Package Shape

```text
mde_client/
  __init__.py       # public API: MDEClient, AuthenticationError
  client.py         # top-level client and context-manager lifecycle
  auth.py           # MSAL token acquisition and caching
  endpoints/
    base.py         # shared query/result behavior
    machines.py     # machines endpoint, query model, lazy result types
  schemas/
    machines.py     # PyArrow schemas for machine and logon-user results
```

## Execution Model

Collection reads and single-machine reads currently use the same lazy result wrapper.

```python
results = client.machines.get_all(MachinesQuery(healthStatus="Active"))

# No HTTP request is made until a terminal method runs.
rows = results.to_json()
table = results.to_arrow()
frame = results.to_polars()

# Re-fetch the underlying API response.
fresh_rows = results.refresh().to_json()
```

Current behavior to account for:

- `get_all()` returns a `MachineResults` handle and auto-paginates unless `top` or `skip` is supplied.
- `get()` also returns a `MachineResults` handle, but it is configured for a single machine lookup.
- Terminal methods reuse the cached response until `refresh()` is called.
- `to_json()` returns `list[dict]`.
- `to_arrow()` returns a `pyarrow.Table`.
- `to_polars()` returns a Polars DataFrame.

## Supported Endpoints

### `client.machines`

| Method | Returns | Notes |
| ------ | ------- | ----- |
| `get_all(query=None)` | `MachineResults` | Lists machines and follows `@odata.nextLink` pagination unless `top` or `skip` is set |
| `get(id)` | `MachineResults` | Fetches one machine by ID and materializes as a single-row result |
| `logonusers(id)` | `LogonUserResults` | Fetches machine logon users |

### Not Yet Implemented

These methods are present on `client.machines` but currently raise `NotImplementedError`:

- `alerts(id)`
- `software(id)`
- `vulnerabilities(id)`
- `recommendations(id)`
- `tags(id)`
- `getmissingkbs(id)`

## Query Parameters

`MachinesQuery` combines common pagination controls with endpoint-specific filters.

### Pagination Controls

| Field | Type | Notes |
| ----- | ---- | ----- |
| `page_size` | `int` | Sent as `pageSize`; must be between 1 and 10000 |
| `top` | `int \| None` | Sent as `$top`; disables automatic pagination |
| `skip` | `int \| None` | Sent as `$skip`; disables automatic pagination |

### Machine Filters

These fields map directly to the Defender machines API filter field names, so they intentionally use camelCase.

| Field | Type |
| ----- | ---- |
| `computerDnsName` | `str \| None` |
| `id` | `str \| list[str] \| None` |
| `version` | `str \| None` |
| `deviceValue` | `Literal["None", "Informational", "Low", "Medium", "High"] \| None` |
| `aadDeviceId` | `str \| list[str] \| None` |
| `machineTags` | `str \| list[str] \| None` |
| `lastSeen` | `datetime \| None` |
| `exposureLevel` | `Literal["None", "Informational", "Low", "Medium", "High"] \| None` |
| `onboardingStatus` | `Literal["Onboarded", "CanBeOnboarded", "Unsupported", "InsufficientInfo"] \| None` |
| `lastIpAddress` | `str \| None` |
| `healthStatus` | `Literal["Active", "Inactive", "ImpairedCommunication", "NoSensorData", "NoSensorDataImpairedCommunication", "Unknown"] \| None` |
| `osPlatform` | `str \| None` |
| `riskScore` | `Literal["None", "Informational", "Low", "Medium", "High"] \| None` |
| `rbacGroupId` | `str \| None` |

## Output Schemas

Machine and logon-user collections are shaped into Arrow-backed containers using the schemas in [schemas/machines.py](schemas/machines.py). Unknown fields are dropped and compatible values are coerced into the declared schema during materialization.

## Errors And Troubleshooting

- `AuthenticationError` is raised when MSAL cannot acquire a token.
- API request failures bubble up through `httpx.Response.raise_for_status()`, which raises `httpx.HTTPStatusError`.
- `to_arrow()` raises `ImportError` with install guidance if Arrow support is unavailable.
- `to_polars()` raises `ImportError` with install guidance if Polars support is unavailable.
- Placeholder machine sub-resource methods currently raise `NotImplementedError` by design.

## Testability

The client is built for dependency injection. You can provide your own `httpx.Client` and `msal.TokenCache` when testing:

```python
import httpx
import msal

client = MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    http_client=httpx.Client(transport=mock_transport),
    token_cache=msal.TokenCache(),
)
```

## License

[AGPL-3.0](../../LICENSE)
