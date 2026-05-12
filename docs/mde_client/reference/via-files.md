# `ViaFiles`

`ViaFiles` is the async downloader used for Defender file-based export workflows.

## Public exports

- `ViaFiles`
- `ViaFilesConfig`
- `EmptyExportBlobError`

## What `ViaFiles` does

Given a set of export URLs, `ViaFiles`:

- downloads blobs concurrently
- detects gzip or plain text responses
- parses newline-delimited JSON incrementally
- batches records into an `ArrowRecordContainer`
- retries transient failures

Most package users do not need to call `ViaFiles` directly because export-backed endpoint wrappers already use it internally.

## `ViaFilesConfig`

`ViaFilesConfig` exposes these tuning fields:

- `download_workers`
- `client_timeout`
- `retry_attempts`
- `retry_delay_seconds`
- `download_chunk_size`
- `parse_batch_size`

These settings control concurrency, timeout behavior, retry policy, and streaming batch sizes.

## Error behavior

`EmptyExportBlobError` is raised internally when a blob returns `200 OK` but contains no records. After retries, confirmed-empty blobs are skipped instead of aborting the whole download.

Repeated hard failures raise a runtime error.

## See also

- [Use export-backed endpoints](../how-to/use-export-backed-endpoints.md)
- [How export-backed endpoints work](../explanation/export-backed-endpoints.md)
