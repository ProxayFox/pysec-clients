# Use Export-Backed Endpoints

Use this guide when the Defender endpoint you need returns export URLs instead of embedding the final dataset directly in the initial response.

## Call the endpoint-specific method

The package already wraps several export-backed workflows for you:

```python
browser_extensions = client.browser_extension.get_all_files().to_dicts()
certificates = client.certificate_inventory.get_all_files().to_dicts()
device_av = client.device_av_health.get_all_files().to_dicts()
baselines = client.baseline_configurations.get_all_files().to_dicts()
```

The result wrapper handles the download step internally. You still use the same terminal methods as any other endpoint.

The export downloader handles both plain NDJSON blobs and gzipped NDJSON blobs, so you do not need to special-case those formats in normal endpoint usage.

## Prefer the endpoint wrapper over raw export URLs

Most callers do not need to use `ViaFiles` directly. The endpoint wrapper already knows:

- how to detect the export URLs in the response
- how to stream and parse newline-delimited JSON
- how to coerce records into the endpoint schema

## Use the JSON-backed form when available

Some surfaces offer both a regular JSON endpoint and a via-files form:

```python
json_rows = client.browser_extension.get_all().to_dicts()
file_rows = client.browser_extension.get_all_files().to_dicts()
```

Choose the form that matches the size and workflow you need.

## Use `ViaFiles` directly when you already have export URLs

Most callers should stay with the endpoint wrappers, but direct `ViaFiles` usage is available when you already have export URLs and want to stream them into your own Arrow container:

```python
import asyncio

from http_to_arrow import ArrowRecordContainer

from mde_client import ViaFiles, ViaFilesConfig

urls = [
    "https://blob.example.com/a.json",
    "https://blob.example.com/b.json",
]

container = ArrowRecordContainer(schema=None)
downloader = ViaFiles(ViaFilesConfig(download_workers=2, client_timeout=30))

container = asyncio.run(downloader.download_export_files(urls, container))
table = container.to_table()
```

This path is useful when you want to tune worker count, timeout, retry settings, or parse batch size directly.

## Apply a record transform during download

If each NDJSON record wraps the payload you actually want, pass `record_transform` to normalize it during download:

```python
import asyncio

from http_to_arrow import ArrowRecordContainer

from mde_client import ViaFiles

def unwrap(record: dict[str, object]) -> dict[str, object]:
    inner = dict(record.get("wrapper", {}))
    for key, value in record.items():
        if key != "wrapper":
            inner[key] = value
    return inner

container = ArrowRecordContainer(schema=None)
container = asyncio.run(
    ViaFiles().download_export_files(urls, container, record_transform=unwrap)
)
```

This is the same mechanism the package uses internally for export-backed endpoints whose blob records need reshaping.

## Know the failure model

Export downloads retry transient failures. Confirmed-empty blobs are skipped after retry logging. A repeated hard failure raises a runtime error.

Practical behaviors to expect:

- multiple export URLs are merged into the same container
- an empty URL list returns immediately without error
- SAS query strings are redacted from logs
- confirmed-empty blobs are skipped rather than treated as fatal failures

## Next references

- [ViaFiles reference](../reference/via-files.md)
- [How export-backed endpoints work](../explanation/export-backed-endpoints.md)
