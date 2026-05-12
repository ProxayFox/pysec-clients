# List and Filter Machines

Use this guide when you need to query the machines inventory and control filtering or pagination.

## List all machines

```python
from mde_client import MDEClient

with MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
) as client:
    machines = client.machines.get_all().to_dicts()
```

Without `$top` or `$skip`, the client paginates automatically until it has collected the full result set.

`MachinesQuery()` also includes a default `pageSize` value when you construct one without overrides, so the client can page through the collection in larger chunks.

## Filter by Defender fields

Use `MachinesQuery` and keep Defender field names as they appear in the API:

```python
from mde_client import MDEClient
from mde_client.endpoints.machines import MachinesQuery

query = MachinesQuery(
    healthStatus="Active",
    exposureLevel="High",
    page_size=500,
)

with MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
) as client:
    machines = client.machines.get_all(query).to_dicts()
```

Common fields include `healthStatus`, `machineTags`, `osPlatform`, `riskScore`, and `rbacGroupId`.

You can also combine filters or pass lists for `in (...)` queries:

```python
from mde_client.endpoints.machines import MachinesQuery

query = MachinesQuery(
    healthStatus="Active",
    osPlatform="Windows10",
    id=["machine-1", "machine-2"],
)

rows = client.machines.get_all(query).to_dicts()
```

The query builder joins multiple fields with `and` and translates string lists into Defender-compatible `in (...)` filters.

## Limit the result set

Set `top` when you only want one page of results:

```python
from mde_client.endpoints.machines import MachinesQuery

query = MachinesQuery(top=100)
```

When `top` or `skip` is set, the client does not auto-paginate.

This is useful for discovery workflows where you want one bounded page and then plan to inspect the result in a dataframe:

```python
from mde_client.endpoints.machines import MachinesQuery

query = MachinesQuery(top=512)
frame = client.machines.get_all(query).to_polars()
```

## Continue from an offset

Use `skip` to request a later slice of the collection:

```python
from mde_client.endpoints.machines import MachinesQuery

query = MachinesQuery(skip=1000, top=100)
```

This is useful when you want deterministic page-sized batches rather than automatic full collection retrieval.

## Find by IP or tag

`MachinesEndpoint` also exposes helper lookups for specific machine discovery workflows:

```python
from datetime import datetime, timedelta, timezone

timestamp = datetime.now(timezone.utc) - timedelta(days=29)
record = client.machines.findbyip("10.0.0.25", timestamp).to_dicts()
tagged = client.machines.tag("production", useStartsWithFilter=True).to_dicts()
```

Use `useStartsWithFilter=True` when your tag input is a prefix rather than an exact tag.

If you already have a page of machine records in Polars, a practical pattern is to extract candidate IP addresses first and then call `findbyip()` on one of them:

```python
import polars as pl

from datetime import datetime, timedelta, timezone
from mde_client.endpoints.machines import MachinesQuery

frame = client.machines.get_all(MachinesQuery(top=512)).to_polars()
ip_list = (
    frame.select(pl.col("ipAddresses"))
    .explode("ipAddresses")
    .select(pl.col("ipAddresses").struct.field("ipAddress").alias("ipAddress"))
    .drop_nulls()
    .get_column("ipAddress")
    .cast(pl.String)
    .unique()
    .to_list()
)

if ip_list:
    timestamp = datetime.now(timezone.utc) - timedelta(days=29)
    matches = client.machines.findbyip(ip_list[0], timestamp).to_dicts()
```

## Next references

- [machines endpoint reference](../reference/endpoints/machines.md)
- [Query models reference](../reference/queries.md)
