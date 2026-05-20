"""Async streaming downloader for Defender file-based export endpoints.

When an MDE export endpoint returns a list of SAS-signed blob URLs
(``exportFiles``), this module downloads them concurrently, decompresses
gzip on the fly, parses newline-delimited JSON, and streams the parsed
records into an ``ArrowRecordContainer`` in batches.

The public entry point is :pymethod:`ViaFiles.download_export_files`.
"""

from __future__ import annotations

import asyncio
import codecs
import logging
import os
import zlib
from collections.abc import AsyncIterator, Callable
from typing import Any, Protocol, runtime_checkable
from urllib.parse import urlsplit, urlunsplit

import aiohttp
import orjson
from http_to_arrow import ArrowRecordContainer
from pydantic import BaseModel

log = logging.getLogger(__name__)

#: Callable that transforms a single parsed export record.
type RecordTransform = Callable[[dict[str, Any]], dict[str, Any]]


@runtime_checkable
class StreamableResponse(Protocol):
    """Minimal interface consumed by :meth:`ViaFiles._stream_export_records`."""

    @property
    def content(self) -> _StreamableContent: ...


class _StreamableContent(Protocol):
    """Minimal interface for the ``content`` property of a ``StreamableResponse``."""

    def iter_chunked(self, n: int) -> AsyncIterator[bytes]: ...


class EmptyExportBlobError(RuntimeError):
    """Raised when an export blob returns 200 OK but contains no records."""


class ViaFilesConfig(BaseModel):
    """Tuning knobs for :class:`ViaFiles` export downloads."""

    download_workers: int = max(1, int((os.cpu_count() or 1) * 0.75))
    client_timeout: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: int = 10
    download_chunk_size: int = int(1024 * 1024 * 2.5)  # 2.5 MiB
    parse_batch_size: int = 5000


class ViaFiles:
    """Async streaming downloader for Defender file-based exports.

    Accepts an optional :class:`ViaFilesConfig` to control concurrency,
    timeouts, retry behaviour, and batch sizes.  When none is supplied the
    defaults from ``ViaFilesConfig`` are used.
    """

    def __init__(self, config: ViaFilesConfig | None = None) -> None:
        self._config = config or ViaFilesConfig()

    @staticmethod
    def _redact_url(url: str) -> str:
        """Return *url* with the query string stripped to avoid logging SAS tokens."""
        try:
            parts = urlsplit(url)
            return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        except Exception:
            return "[redacted-url]"

    async def _stream_export_records(
        self,
        response: StreamableResponse,
        f_url: str,
        record_queue: asyncio.Queue[list[dict[str, Any]] | None],
        record_transform: RecordTransform | None = None,
    ) -> int:
        """Stream, decompress, and parse a single export blob into queued batches."""

        compression_mode: str | None = None
        decompressor: zlib._Decompress | None = None
        decoder = codecs.getincrementaldecoder("utf-8-sig")()
        buffered_line = ""
        records_batch: list[dict[str, Any]] = []
        total_records = 0

        async def emit_batch() -> None:
            nonlocal records_batch
            if not records_batch:
                return
            await record_queue.put(records_batch)
            records_batch = []

        async def parse_text_chunk(text_chunk: str, *, final: bool = False) -> None:
            nonlocal buffered_line, records_batch, total_records

            combined = buffered_line + text_chunk
            if not combined and not final:
                return

            if final:
                lines = combined.splitlines()
                buffered_line = ""
            else:
                lines: list[str] = []
                buffered_line = ""
                for line in combined.splitlines(keepends=True):
                    if line.endswith(("\n", "\r")):
                        lines.append(line)
                    else:
                        buffered_line = line

            for line in lines:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                record = orjson.loads(stripped_line)
                if record_transform is not None:
                    record = record_transform(record)
                records_batch.append(record)
                total_records += 1

                if len(records_batch) >= self._config.parse_batch_size:
                    await emit_batch()

        async for chunk in response.content.iter_chunked(
            self._config.download_chunk_size
        ):
            if not chunk:
                continue

            # Auto-detect gzip on the first chunk.
            if compression_mode is None:
                if chunk.startswith(b"\x1f\x8b"):
                    compression_mode = "gzip"
                    decompressor = zlib.decompressobj(zlib.MAX_WBITS | 16)
                else:
                    compression_mode = "plain"
                    log.warning(
                        "Failed to detect gzip for %s, trying plain text.",
                        self._redact_url(f_url),
                    )

            if compression_mode == "gzip" and decompressor is not None:
                decoded_text = decoder.decode(decompressor.decompress(chunk))
            else:
                decoded_text = decoder.decode(chunk)

            await parse_text_chunk(decoded_text)

        # Flush any trailing data.
        if compression_mode == "gzip" and decompressor is not None:
            trailing_text = decoder.decode(decompressor.flush(), final=True)
        else:
            trailing_text = decoder.decode(b"", final=True)

        await parse_text_chunk(trailing_text, final=True)
        await emit_batch()

        log.info("%d records found in %s.", total_records, self._redact_url(f_url))
        return total_records

    async def _append_export_records(
        self,
        record_queue: asyncio.Queue[list[dict[str, Any]] | None],
        container: ArrowRecordContainer,
    ) -> None:
        """Drain *record_queue* and extend *container* until a sentinel ``None`` arrives."""
        while True:
            records = await record_queue.get()
            try:
                if records is None:
                    return
                await asyncio.to_thread(container.extend, records)
            finally:
                record_queue.task_done()

    async def _download_export_file(
        self,
        session: aiohttp.ClientSession,
        f_url: str,
        semaphore: asyncio.Semaphore,
        record_queue: asyncio.Queue[list[dict[str, Any]] | None],
        record_transform: RecordTransform | None = None,
    ) -> None:
        """Download and parse a single export blob with retry logic."""
        last_error: Exception | None = None

        for attempt in range(1, self._config.retry_attempts + 1):
            try:
                async with semaphore, session.get(f_url) as response:
                    response.raise_for_status()
                    record_count = await self._stream_export_records(
                        response,
                        f_url,
                        record_queue,
                        record_transform,
                    )
                    if record_count == 0:
                        raise EmptyExportBlobError(
                            "Export blob returned 200 OK but contained no records "
                            f"(content_length={response.content_length})"
                        )
                break  # success
            except (
                aiohttp.ClientError,
                asyncio.TimeoutError,
                EmptyExportBlobError,
            ) as exc:
                last_error = exc
                status_suffix = (
                    f" (status {exc.status})"  # type: ignore[union-attr]
                    if hasattr(exc, "status")
                    else ""
                )
                log.warning(
                    "Attempt %d/%d failed for %s: %s%s",
                    attempt,
                    self._config.retry_attempts,
                    self._redact_url(f_url),
                    type(exc).__name__,
                    status_suffix,
                )
                if attempt < self._config.retry_attempts:
                    await asyncio.sleep(self._config.retry_delay_seconds * attempt)
        else:
            if isinstance(last_error, EmptyExportBlobError):
                log.info(
                    "Skipping empty export blob after %d attempts: %s",
                    self._config.retry_attempts,
                    self._redact_url(f_url),
                )
                return
            raise RuntimeError(
                f"Failed to download {self._redact_url(f_url)} "
                f"after {self._config.retry_attempts} attempts"
            ) from last_error

    async def download_export_files(
        self,
        urls: list[str],
        container: ArrowRecordContainer,
        *,
        record_transform: RecordTransform | None = None,
    ) -> ArrowRecordContainer:
        """Download export blobs concurrently and stream records into *container*.

        Args:
            urls: SAS-signed blob URLs returned by an MDE ``exportFiles`` response.
            container: Pre-configured :class:`ArrowRecordContainer` that records
                are streamed into.
            record_transform: Optional callable applied to each parsed JSON
                record before it is batched.  Use this to flatten nested
                export formats (e.g. ``DeviceGatheredInfo``).

        Returns:
            The same *container*, now populated with the parsed records.
        """
        semaphore = asyncio.Semaphore(max(1, self._config.download_workers))
        record_queue: asyncio.Queue[list[dict[str, Any]] | None] = asyncio.Queue(
            maxsize=max(1, self._config.download_workers * 2),
        )
        timeout = aiohttp.ClientTimeout(total=self._config.client_timeout)
        append_task = asyncio.create_task(
            self._append_export_records(record_queue, container),
        )

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                tasks = [
                    self._download_export_file(
                        session,
                        f_url,
                        semaphore,
                        record_queue,
                        record_transform,
                    )
                    for f_url in urls
                ]
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=False)
                await record_queue.join()
        finally:
            await record_queue.put(None)
            await append_task

        return container
