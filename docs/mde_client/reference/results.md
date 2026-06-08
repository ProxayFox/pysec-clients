# Results Wrappers

Most endpoint methods return a lazy results wrapper instead of an eager list.

## Shared interface

The main wrapper type is `BaseResults`. It exposes:

- `to_dicts()`
- `to_json(indent: bool = False)`
- `to_arrow()`
- `to_polars()`
- `to_ipc_stream(schema=None, *, batch_size=128_000, queue_maxsize=4, compression=None)`
- `refresh()`

The advanced hunting endpoint uses a dedicated wrapper, but it follows the same materialization interface.

## Fetch behavior

The wrapper does not fetch on construction. The first terminal method triggers the HTTP request and caches the result in memory.

## Pagination behavior

- collection endpoints paginate automatically by default
- if a query sets `$top` or `$skip`, the wrapper performs only that request
- single-item methods use `single=True` and normalize the response to a one-record list when materialized as dictionaries

## File-backed behavior

Some wrappers use `files=True`. In that case the initial response is expected to contain export URLs, and the wrapper downloads the export blobs through `ViaFiles` before returning the final materialized result.

## Materialization choices

- `to_dicts()` is the simplest Python-native format
- `to_json()` is useful for logging or serialization
- `to_arrow()` returns a `pyarrow.Table`
- `to_polars()` returns a Polars DataFrame
- `refresh()` clears the cache so the next terminal method fetches again

## Streaming for memory-limited runtimes

`to_ipc_stream()` is an async terminal that streams results as Arrow IPC stream byte chunks instead of building a cached table. Each page is fetched, serialized into a `RecordBatch`, emitted, and released, so peak memory stays close to a single batch — suitable for exporting millions of rows from a 2 GiB Azure Function.

Unlike the other terminal methods, it is **not cached**: it issues fresh requests on every call and never populates the internal container. An explicit `pyarrow.Schema` is required (from `schema=` or the wrapper's `SCHEMA`) because the IPC stream header is written before any rows are fetched.

```python
async for chunk in results.to_ipc_stream(compression="zstd"):
    ...  # forward each chunk to a streaming HTTP response
```

See [Stream results as Arrow IPC](../how-to/stream-ipc-results.md).

## See also

- [Work with result formats](../how-to/work-with-result-formats.md)
- [Lazy results and caching](../explanation/lazy-results.md)

## API

::: mde_client.endpoints.base.BaseResults
    options:
      heading_level: 3
      show_bases: false
