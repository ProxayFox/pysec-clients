# Run an Advanced Hunting Query

Use this guide when you want to execute a Defender advanced hunting query through the package.

## Run the query

```python
from mde_client import MDEClient

query = """
DeviceInfo
| take 10
"""

with MDEClient(
    tenant_id="YOUR_TENANT_ID",
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
) as client:
    rows = client.advanced_queries.run(query).to_dicts()
```

The `run()` method returns its own results wrapper with the same terminal methods used by other endpoints.

## Convert to a dataframe

```python
frame = client.advanced_queries.run(query).to_polars()
```

This is useful when you plan to reshape or aggregate the output locally.

## Refresh the query

If you want to rerun the same query after the results have already been materialized:

```python
results = client.advanced_queries.run(query)
first = results.to_dicts()
fresh = results.refresh().to_dicts()
```

## Notes

- The advanced hunting result schema is not fixed in the same way as the endpoint schemas backed by generated Arrow contracts.
- The wrapper still exposes the same `to_dicts()`, `to_json()`, `to_arrow()`, `to_polars()`, and `refresh()` interface.

## Next references

- [advanced_queries endpoint reference](../reference/endpoints/advanced-queries.md)
- [Results wrappers reference](../reference/results.md)
