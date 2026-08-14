# Build multi-endpoint workflows

Real workloads stitch several Defender endpoints together — for example: list machines, then enrich each one with alerts and software inventory. This page shows the idioms that fit naturally on top of `mde-client`'s lazy results and Arrow-first materialization.

## A worked example: machine alert summary

The goal: for every active Windows machine, produce a `Polars` DataFrame with one row per machine and per-machine alert counts joined on.

```python
import polars as pl
from mde_client import MDEClient
from mde_client.endpoints.machines import MachinesQuery


def alert_summary(client: MDEClient) -> pl.DataFrame:
    # 1. Pull active Windows machines as Polars (one network round-trip set).
    machines = (
        client.machines.get_all(
            MachinesQuery(healthStatus="Active", osPlatform="Windows10")
        )
        .to_polars()
        .select(["id", "computerDnsName", "lastSeen"])
    )

    # 2. For each machine, fetch related alerts and count.
    counts: list[dict] = []
    for machine_id in machines["id"]:
        alerts = client.machines.alerts(machine_id).to_polars()
        counts.append({"id": machine_id, "alert_count": alerts.height})

    counts_df = pl.DataFrame(counts)

    # 3. Join the two frames on machine id.
    return machines.join(counts_df, on="id", how="left")
```

Things to notice:

- Each endpoint method returns a lazy wrapper; the network call happens when you call `.to_polars()`.
- Reusing one `MDEClient` keeps the HTTP connection pool and MSAL token cache warm across calls.
- Defender query fields (`healthStatus`, `osPlatform`) preserve upstream names — see [Why query models keep Defender field names](../explanation/query-models.md).

## Run per-machine fan-out concurrently

The pattern above is fine for hundreds of machines. For thousands, parallelise the inner loop with a thread pool. Defender rate-limits aggressively, so keep the pool small and combine it with the retry policy from [Handle errors and retries](handle-errors-and-retries.md):

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


def _count(machine_id: str) -> dict:
    return {
        "id": machine_id,
        "alert_count": client.machines.alerts(machine_id).to_polars().height,
    }


counts: list[dict] = []
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = [pool.submit(_count, mid) for mid in machines["id"]]
    for fut in as_completed(futures):
        counts.append(fut.result())
```

If you see `429` responses, drop `max_workers`, add a `Retry-After` aware retry, or batch fewer machines per cycle.

## Compose Arrow tables directly

When the only thing you need is the joined dataset, work in Arrow end-to-end and skip the DataFrame round-trips for intermediate steps:

```python
import pyarrow as pa
import pyarrow.compute as pc

machines = client.machines.get_all().to_arrow()
ids = machines.column("id").to_pylist()

alert_tables = [client.machines.alerts(i).to_arrow() for i in ids]
all_alerts = pa.concat_tables(alert_tables, promote_options="default")
```

Arrow is the canonical format inside `mde-client`; `to_polars()` and `to_dicts()` both flow through Arrow.

## Stitching export-backed endpoints

Export-backed endpoints (browser extensions, AV health, certificate inventory, firmware-by-machine, etc.) return one big batched result. Materialise once, then `.join()` against your machine inventory:

```python
extensions = client.browser_extension.get_all_files().to_polars()
machines = client.machines.get_all().to_polars()

joined = machines.join(extensions, left_on="id", right_on="machineId", how="inner")
```

See [Use export-backed endpoints](use-export-backed-endpoints.md) for the export contract.

## Plug into a real pipeline

Common shapes that work well on top of `mde-client`:

- **Scheduled ETL**: a single `MDEClient` per run; export-backed endpoints for bulk data, JSON-backed endpoints for per-entity follow-ups.
- **Notebook investigation**: load to Polars, slice/dice, then drop into your existing analysis stack.
- **Alerting service**: keep one `MDEClient` warm, call `refresh()` on cached results on a timer.
- **Data lake hydration**: write `to_arrow()` output straight to Parquet via `pyarrow.parquet.write_table`.

## See also

- [List and filter machines](list-and-filter-machines.md)
- [Get related data for one machine](get-machine-related-data.md)
- [Use export-backed endpoints](use-export-backed-endpoints.md)
- [Tune performance](tune-performance.md)
- [Result materialization model](../explanation/result-materialization.md)
