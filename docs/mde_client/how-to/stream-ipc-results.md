# Stream Results as Arrow IPC

Use this guide when a result set is too large to materialize in memory — for
example exporting millions of rows from a memory-limited runtime such as a 2 GiB
Azure Function.

The cached terminals (`to_dicts()`, `to_json()`, `to_arrow()`, `to_polars()`)
build the full dataset in memory before returning. `to_ipc_stream()` instead
streams the result as [Arrow IPC stream](https://arrow.apache.org/docs/python/ipc.html)
byte chunks: each page is fetched, serialized into a `RecordBatch`, emitted, and
released, so peak memory stays close to a single batch.

## Stream from a results wrapper

`to_ipc_stream()` is an async generator. Iterate it and forward each chunk to
your output:

```python
results = client.machines.get_all()

async for chunk in results.to_ipc_stream(compression="zstd"):
    ...  # forward each chunk downstream
```

An explicit `pyarrow.Schema` is required because the IPC stream header is written
before any rows are fetched. Most wrappers already define `SCHEMA`, so you do not
need to pass one. Provide `schema=` when a wrapper has no schema:

```python
import pyarrow as pa

schema = pa.schema([("id", pa.string()), ("computerDnsName", pa.string())])

async for chunk in results.to_ipc_stream(schema=schema):
    ...
```

## Forward to a streaming HTTP response

The Arrow IPC stream content type is `application/vnd.apache.arrow.stream`. In an
Azure Function (or any ASGI app) you can stream the chunks straight to the
client:

```python
import azure.functions as func


async def main(req: func.HttpRequest) -> func.HttpResponse:
    results = client.machines.get_all()

    async def body():
        async for chunk in results.to_ipc_stream(compression="zstd"):
            yield chunk

    return func.HttpResponse(
        body(),
        mimetype="application/vnd.apache.arrow.stream",
    )
```

## Consume the stream on the client

Concatenated chunks form a valid Arrow IPC stream, readable with PyArrow:

```python
import pyarrow as pa

reader = pa.ipc.open_stream(pa.BufferReader(response_bytes))
table = reader.read_all()
```

For truly large payloads, read batches incrementally instead of `read_all()`:

```python
reader = pa.ipc.open_stream(source)
for batch in reader:
    ...  # process one RecordBatch at a time
```

## Tuning

`to_ipc_stream()` accepts a few keyword arguments:

- `batch_size` — target row count per emitted `RecordBatch` (default `128_000`).
- `queue_maxsize` — bounded backpressure between page fetching and batch
  serialization (default `4`). Lower it for very large pages; raise it for many
  small pages.
- `compression` — an Arrow IPC codec such as `"zstd"` supported by your PyArrow
  build. Compression shrinks the serialized output without changing schema
  compatibility.

## Behavior to account for

- **Not cached.** Unlike the other terminals, `to_ipc_stream()` issues fresh
  requests on every call and never populates the wrapper's internal container.
  `refresh()` is unnecessary.
- **Schema required.** Inferred-schema mode is not supported for streaming.
- **Works across fetch modes.** Collection pagination, concurrent `$top`/`$skip`
  pagination, single-object responses, and export-backed (`files=True`)
  endpoints all stream through the same method.
- **Errors mid-stream.** If a request fails partway, the partial IPC stream is
  flushed and closed cleanly and the original exception is re-raised after the
  trailing bytes are emitted.

## See also

- [Work with result formats](work-with-result-formats.md)
- [Results wrappers reference](../reference/results.md)
- [Result materialization model](../explanation/result-materialization.md)
