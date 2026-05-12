# How Export-Backed Endpoints Work

Some Defender APIs do not return the final dataset directly. Instead, the initial response contains `exportFiles` URLs that point to blob storage.

## What the client does with those URLs

For export-backed endpoint wrappers, the package:

- calls the initial endpoint
- extracts the export URLs
- downloads the blobs concurrently
- decompresses them when needed
- parses newline-delimited JSON records
- appends the records into the same Arrow-backed container used elsewhere in the client

## Why the user-facing API stays the same

The package hides the extra transport layer so callers can keep using the same materialization methods they already know:

```python
rows = client.device_av_health.get_all_files().to_dicts()
```

That makes export-backed endpoints feel like ordinary endpoint calls even though the underlying fetch path is more complex.

## Why this matters

Without this abstraction, every caller would need to reimplement blob download, gzip handling, newline parsing, and retry behavior.

The current design keeps that logic in one place and reuses it across endpoint families.
