# Result materialization model

`mde-client` separates *fetching* records from *formatting* them. Every endpoint that returns a collection (or a single record) hands you a lazy results wrapper; the network call and the conversion to your final shape are two distinct events.

## Three layers, in order

```text
endpoint method   →   results wrapper   →   terminal method (.to_polars(), .to_arrow(), .to_dicts(), .to_json())
   (no I/O)            (cache + I/O)             (zero-copy view into the cache)
```

1. Calling `client.machines.get_all(query)` constructs a wrapper. It records the path, query, and pagination hints, but performs no I/O.
2. The first terminal call (`.to_polars()`, `.to_arrow()`, `.to_dicts()`, `.to_json()`) fetches every page, normalises rows, and caches the result internally as an `ArrowRecordContainer`.
3. The terminal method returns a view onto that cached Arrow container. Subsequent terminal calls reuse the cache; `.refresh()` clears it.

## Why Arrow is the canonical format

Defender responses are heterogenous: pages, file exports, NDJSON streams, multiple status envelopes. Internally the package normalises all of those into a single `ArrowRecordContainer` because:

- Arrow can stream record batches with a fixed schema rather than holding every row in Python memory at once.
- Both `pyarrow.Table` and `polars.DataFrame` are zero-copy views of Arrow data. Returning a `Table` or `DataFrame` from the cache costs effectively nothing.
- A typed schema catches upstream changes early; `mde_client.schemas` exposes the canonical schemas the package was built against.
- `to_dicts()` and `to_json()` are derived from the same Arrow buffer, so all four terminal methods see exactly the same data.

## Why the wrapper caches

The wrapper caches because users typically read the same response several different ways during a single operation: log it as JSON, write it to Parquet via Arrow, and inspect a row or two as dicts. Fetching once per terminal call would hit the Defender API harder without giving the user anything in return.

Caching is also why `refresh()` is explicit. The package never silently re-fetches; if you want fresh data you ask for it.

## Why terminal calls do not return the cache directly

`to_arrow()` returns a `pyarrow.Table`, not the raw container, so:

- Callers cannot accidentally mutate the wrapper's internal state.
- Different terminal methods can apply small, format-specific transforms (for example, `to_dicts()` flattens nested struct columns the way Python users expect).
- Future format additions (`to_pandas()`, `to_iceberg()`, etc.) do not require breaking the wrapper API.

## Implications for users

- **Choose your terminal once.** Mixing `.to_dicts()` and `.to_polars()` on the same wrapper is fine and cheap.
- **Cache lives in the wrapper, not the client.** If you want long-term reuse, keep the wrapper around; if you want to drop it, dereference it.
- **Schema mismatches surface at fetch time.** If Defender adds a column the package's schema does not know about, you find out when the first terminal method runs, not later in your transformation code.
- **Streaming reads are still on the table.** The current cache is fully materialised, but the underlying Arrow batching means future iterator-style terminals can be added without changing the user-facing contract.

## See also

- [Results wrappers (reference)](../reference/results.md)
- [Work with result formats](../how-to/work-with-result-formats.md)
- [Lazy results and caching](lazy-results.md)
