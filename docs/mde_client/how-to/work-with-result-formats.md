# Work with Result Formats

Use this guide when you need the same endpoint data in different in-memory representations.

## Start from a results wrapper

```python
results = client.machines.get_all()
```

At this stage the request has not run yet.

This lazy behavior is intentional. Constructing the wrapper is cheap, and the first terminal method decides when the request actually happens.

## Convert to Python dictionaries

```python
rows = results.to_dicts()
```

Use this when you want the simplest Python-native representation.

## Convert to JSON

```python
payload = results.to_json()
pretty = results.to_json(indent=True)
```

`to_json(indent=True)` returns a formatted JSON string.

## Convert to Arrow or Polars

```python
table = results.to_arrow()
frame = results.to_polars()
```

Use these when you need columnar or dataframe-style processing.

## Reuse the same fetched payload

Once the first terminal method runs, later terminal methods use the cached payload rather than triggering a second fetch:

```python
results = client.machines.get_all()

rows = results.to_dicts()   # first fetch
table = results.to_arrow()  # reuses cached data
frame = results.to_polars() # reuses cached data
```

This makes it practical to inspect the same result in multiple formats during one workflow.

## Refresh the cached data

Materialization caches the underlying payload. Call `refresh()` before the next terminal method when you want a new API call:

```python
fresh_rows = results.refresh().to_dicts()
```

`refresh()` is chainable, so these patterns also work:

```python
fresh_table = results.refresh().to_arrow()
fresh_frame = results.refresh().to_polars()
```

## Notes

- `to_dicts()` is usually the best first choice for application code and debugging.
- Arrow and Polars support depend on your environment and package extras.
- The same materialization pattern is used across most endpoints.
- An empty response still materializes cleanly as `[]`, an empty table, or an empty dataframe.

## Next references

- [Results wrappers reference](../reference/results.md)
- [Lazy results and caching](../explanation/lazy-results.md)
