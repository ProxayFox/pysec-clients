# Lazy Results and Caching

The package is built around lazy result wrappers because Defender responses vary in size and cost.

Instead of fetching immediately, an endpoint method returns a lightweight wrapper that remembers:

- which path to call
- which query parameters to send
- whether the endpoint is single-item, paginated, or file-backed

The HTTP request only happens when you choose an output form such as `to_dicts()` or `to_polars()`.

## Why this helps

This design gives the caller one stable interface regardless of endpoint family.

It also lets the package postpone work until the caller knows how they want to consume the data.

## Why there is a cache

Once materialized, the wrapper keeps the parsed data in memory. That avoids repeated network calls when you need multiple representations of the same result:

```python
results = client.machines.get_all()
rows = results.to_dicts()
frame = results.to_polars()
```

Without caching, each terminal method would repeat the request.

## Why `refresh()` exists

Caching is useful, but some workflows need a fresh read. `refresh()` drops the cached container so the next terminal method triggers a new API call.

## Tradeoff

The design favors a consistent and ergonomic consumer API over strict eagerness. In return, the caller needs to understand that constructing a results object is not the same as executing the request.
