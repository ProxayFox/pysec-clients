# Tune performance

This guide covers the knobs `mde-client` exposes for throughput, latency, and memory pressure. The defaults are tuned for moderate tenants; large tenants and batch pipelines often benefit from explicit tuning.

## Pick the right materialization

Each terminal method on a results wrapper has different cost characteristics:

| Method        | Best for                                | Trade-off                                            |
| ------------- | --------------------------------------- | ---------------------------------------------------- |
| `to_arrow()`  | Joining/transforming inside the package | Lowest overhead — wrappers cache Arrow internally    |
| `to_polars()` | DataFrame analysis                      | Zero-copy from Arrow; ideal once you need a DataFrame |
| `to_dicts()`  | Python-native pipelines, small payloads | Materialises every row as `dict`; highest memory cost |
| `to_json()`   | Logging, serialisation                  | Encodes the dict view; do not use as a transit format |

If you call multiple terminal methods on the same wrapper, the underlying Arrow data is fetched once and reused. Call `refresh()` explicitly when you want a re-fetch.

## Control pagination

Collection endpoints auto-paginate until exhausted. Two knobs change that:

```python
from mde_client.endpoints.machines import MachinesQuery

# Cap results: a single page of at most 200 records.
q = MachinesQuery(top=200)
rows = client.machines.get_all(q).to_polars()

# Increase per-page size for fewer round-trips on big lists.
q = MachinesQuery(page_size=1000)
rows = client.machines.get_all(q).to_polars()
```

- Setting `top` (or `skip`) disables auto-pagination and issues a single request.
- `page_size` increases the per-page batch without disabling pagination.
- Larger `page_size` reduces request count but increases per-response memory and latency.

## Tune the HTTP client

Inject an `httpx.Client` with explicit timeouts, retries, and connection limits:

```python
import httpx
from mde_client import MDEClient

http = httpx.Client(
    base_url="https://api.securitycenter.microsoft.com",
    timeout=httpx.Timeout(30.0, connect=5.0),
    limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    # transport=httpx.HTTPTransport(retries=3),  # transport-level connect retries
)

with MDEClient(tenant_id, client_id, client_secret, http_client=http) as client:
    ...
```

The client takes ownership when you do not inject one. If you do inject, you also own the lifecycle; close it when you are done.

## Tune `ViaFiles` for export-backed endpoints

[`ViaFilesConfig`](../reference/via-files.md) exposes the knobs that matter for file-export workflows:

| Field                  | What it controls                                          |
| ---------------------- | --------------------------------------------------------- |
| `download_workers`     | Concurrency for blob downloads                            |
| `client_timeout`       | Per-blob HTTP timeout                                     |
| `retry_attempts`       | How many times a blob is retried on failure               |
| `retry_delay_seconds`  | Delay between retries                                     |
| `download_chunk_size`  | Streaming read granularity (bytes)                        |
| `parse_batch_size`     | Records per Arrow batch during NDJSON parsing             |

Defaults are conservative. For large tenants:

- Raise `download_workers` (8–16) on a fast network with spare CPU.
- Raise `parse_batch_size` to reduce Arrow overhead per batch.
- Raise `client_timeout` when blobs are large or the network has high tail latency.

## Reuse the client across calls

`MDEClient` owns one connection pool and one MSAL token cache. Reuse a single instance per process:

```python
# Good
with MDEClient(...) as client:
    machines = client.machines.get_all().to_polars()
    alerts = client.alerts.get_all().to_polars()


# Bad — closes the pool, drops the token cache, repeats MSAL flow.
def get_machines():
    with MDEClient(...) as c:
        ...


def get_alerts():
    with MDEClient(...) as c:
        ...
```

If you do need a long-running process (worker, server, scheduler), inject a persistent `msal.SerializableTokenCache` so cached tokens survive process restarts. See [Inject a custom HTTP client or token cache](inject-http-client-and-token-cache.md).

## Refresh deliberately

A results wrapper caches the fetched Arrow data the first time you materialize it. Subsequent terminal calls reuse the cache:

```python
results = client.machines.get_all()
df1 = results.to_polars()  # network fetch
df2 = results.to_polars()  # cached, no fetch
results.refresh()
df3 = results.to_polars()  # network fetch again
```

In long-running pipelines, hold the wrapper and call `refresh()` on a schedule rather than instantiating new endpoint queries.

## See also

- [Handle errors and retries](handle-errors-and-retries.md)
- [Use export-backed endpoints](use-export-backed-endpoints.md)
- [ViaFiles reference](../reference/via-files.md)
- [Lazy results and caching](../explanation/lazy-results.md)
