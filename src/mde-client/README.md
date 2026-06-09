# mde-client

Python client for the [Microsoft Defender for Endpoint](https://learn.microsoft.com/en-us/defender-endpoint/) API.

`mde-client` is organized around a single top-level `MDEClient` with lazy endpoint wrappers. Endpoint calls return result handles that fetch on first materialization, cache the payload, and can be rendered as Python dictionaries, JSON, PyArrow tables, or Polars DataFrames.

## Highlights

- Client-credentials authentication through MSAL.
- Lazy endpoint results with shared materialization methods.
- Coverage across machine inventory, alerts, investigations, authenticated scans, advanced hunting, assessments, remediation, and machine actions.
- Built-in support for Defender file-export endpoints through `ViaFiles`.
- Constructor injection for `httpx.Client` and `msal.TokenCache` to keep tests and custom transports straightforward.

## Documentation

Use this README for the package overview and quick start.

- For the structured docs set, start at [../../docs/mde_client/index.md](../../docs/mde_client/index.md).
- For a first-success walkthrough, use [../../docs/mde_client/tutorials/get-started.md](../../docs/mde_client/tutorials/get-started.md).
- For API lookup, use [../../docs/mde_client/reference/index.md](../../docs/mde_client/reference/index.md).

## Install

```bash
uv add mde-client
```

The package also defines optional extras when you want to declare dataframe support explicitly in your environment:

```bash
uv add "mde-client[arrow]"
uv add "mde-client[arrow,polars]"
```

If you are developing inside this monorepo, use the root workflow instead:

```bash
uv sync --all-packages --all-groups
```

## Authentication Prerequisites

You need an Azure AD app registration that can use the OAuth 2.0 client-credentials flow against Microsoft Defender for Endpoint.

- Tenant ID
- Client ID
- Client secret
- Defender application permissions granted to the app registration

`MDEClient` uses [MSAL](https://github.com/AzureAD/microsoft-authentication-library-for-python) and the Defender default scope under the hood.

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
        machines = client.machines.get_all(
            MachinesQuery(healthStatus="Active", page_size=500)
        ).to_dicts()

        print(f"Fetched {len(machines)} machines")

        machine = client.machines.get("machine-guid").to_dicts()[0]
        print(machine["computerDnsName"])

        logon_users = client.machines.logonusers("machine-guid").to_dicts()
        print(logon_users[:3])
except AuthenticationError as exc:
    print(f"Authentication failed: {exc}")
```

## Public Imports

The top-level package exports:

- `MDEClient`
- `AuthenticationError`
- `ViaFiles`
- `ViaFilesConfig`
- `EmptyExportBlobError`

## Result Model

Most endpoint methods return a lazy results wrapper rather than an eager list or model.

```python
results = client.machines.get_all(MachinesQuery(healthStatus="Active"))

# No request is made until a terminal method runs.
rows = results.to_dicts()
payload = results.to_json()
table = results.to_arrow()
frame = results.to_polars()

# Drop the cached payload and fetch again on the next terminal call.
fresh_rows = results.refresh().to_dicts()
```

Behavior to account for:

- Collection and single-item lookups use the same wrapper style.
- Pagination is automatic for list endpoints unless you set `$top` or `$skip` through a query model.
- Materialization methods reuse cached data until `refresh()` is called.
- `to_dicts()` is the simplest Python-native representation for downstream code.
- Write helpers return either lazy result wrappers or `bool`, depending on whether the underlying API returns an entity payload or an empty success response.

### Streaming Arrow IPC for memory-limited runtimes

For very large result sets (some Defender endpoints return millions of rows), the cached terminal methods can exceed tight memory budgets. `to_ipc_stream()` is an async terminal that streams results as Arrow IPC stream byte chunks, keeping peak memory close to a single record batch — for example when exporting from a 2 GiB Azure Function.

```python
import pyarrow as pa

results = client.machines.get_all()

async for chunk in results.to_ipc_stream(compression="zstd"):
    ...  # forward each chunk to a streaming HTTP response
```

Unlike the other terminals it is not cached and issues fresh requests on every call. It requires an explicit `pyarrow.Schema` (from `schema=` or the wrapper's `SCHEMA`) because the IPC stream header is written before any rows are fetched. It works for collection pagination, concurrent `$top`/`$skip` pagination, single-object responses, and export-backed (`files=True`) endpoints.

## Endpoint Surface

`MDEClient` exposes endpoint properties for the current Defender surface. The most commonly used groups are:

| Property | What it covers |
| -------- | -------------- |
| `machines` | Machine inventory, machine lookups, related users and alerts, installed software, vulnerabilities, recommendations, machine-scoped actions, and several assessment exports |
| `alerts` | Alert listing, alert relationships, create-by-reference flows, and batch updates |
| `authenticated_definitions` / `authenticated_agents` | Authenticated scan definitions, scanner agents, and scan history workflows |
| `advanced_queries` | Advanced hunting query execution |
| `software`, `vulnerabilities`, `recommendations`, `remediations`, `score`, `baseline_configurations` | Exposure, remediation, score, and baseline-related datasets |
| `browser_extension`, `certificate_inventory`, `device_av_health` | Assessment inventory and export-backed datasets |
| `files`, `domain`, `ips`, `user`, `investigations`, `indicators`, `library`, `machine_actions` | Related entity lookups, response actions, indicator management, and live response library operations |

The full property list is defined on `MDEClient`, but the important pattern is consistent: endpoint methods return a results wrapper or a small success value, and the wrapper APIs stay uniform across endpoint families.

## Query Models

Query models inherit from a shared base that supports:

- `page_size` mapped to `pageSize`
- `top` mapped to `$top`
- `skip` mapped to `$skip`
- OData-style `$filter` construction from non-null model fields

Defender-specific query fields intentionally preserve upstream API names such as `healthStatus`, `machineTags`, and `lastSeen` instead of normalizing everything to snake_case.

## File Exports And `ViaFiles`

Some Defender endpoints return `exportFiles` SAS URLs instead of embedding the final dataset in the initial API response. For those endpoints, the result wrappers use `ViaFiles` internally to:

- download blobs concurrently
- stream gzip or plain NDJSON responses
- parse records incrementally
- append them into an `ArrowRecordContainer`

Most callers do not need to use `ViaFiles` directly because export-backed endpoint wrappers already handle it. Use `ViaFiles` yourself when you already have export URLs and want to stream them into your own Arrow container with custom tuning through `ViaFilesConfig`.

`EmptyExportBlobError` is the internal signal used when a blob returns `200 OK` but contains no records. The public downloader retries and then skips confirmed-empty blobs.

## Customization And Testing

`MDEClient` accepts both a custom `httpx.Client` and an optional MSAL token cache:

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

This makes it straightforward to test request construction, inject custom transports, or persist tokens outside the default in-memory cache.

## Errors And Operational Notes

- `AuthenticationError` is raised when MSAL cannot acquire a token.
- HTTP failures bubble up through `httpx` status handling.
- Export-file downloads retry transient failures and raise a runtime error if a blob cannot be fetched successfully; confirmed-empty blobs are skipped after retry logging.
- The client is a context manager; use `with MDEClient(...) as client:` when possible so the underlying HTTP session is closed promptly.

## License

[Apache-2.0](../../LICENSE)

## Releasing

`mde-client` is published to PyPI from this monorepo via a tag-driven GitHub
Actions workflow that authenticates with [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC, no API tokens).

To cut a release:

1. Bump `version` in [`pyproject.toml`](pyproject.toml).
2. Add a matching `[<version>] - <date>` section to [`CHANGELOG.md`](CHANGELOG.md)
   and move items out of `[Unreleased]`.
3. Run `just quality` locally (includes `uv build` + `twine check`).
4. Merge the version bump and changelog to `main`. The
   [tag-on-version-bump workflow](../../.github/workflows/tag-on-version-bump.yml)
   detects the changed `version` and automatically creates and pushes the
   annotated tag `mde-client-v<version>` (e.g. `mde-client-v0.2.0`). It is
   idempotent and skips tags that already exist.
5. The [release workflow](../../.github/workflows/release.yml) triggers on that
   tag, verifies it matches the pyproject version, builds the sdist and wheel,
   and publishes to PyPI.
6. The [Docs workflow](../../.github/workflows/docs.yml) publishes a versioned
   documentation snapshot with `mike` for the same tag. Stable tags move the
   `latest` alias and the site root; prerelease tags (`rc`/`a`/`b`) publish a
   browsable version without changing `latest`.

Future vendor packages in this monorepo follow the same scheme:
`<distribution-name>-v<version>`.
