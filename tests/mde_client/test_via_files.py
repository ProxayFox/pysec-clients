"""Tests for the ViaFiles async streaming export downloader."""

from __future__ import annotations

import asyncio
import gzip
from typing import Any
from unittest.mock import patch

import aiohttp
import orjson
import pyarrow as pa
import pytest
from http_to_arrow import ArrowRecordContainer

from mde_client.viaFiles import (
    EmptyExportBlobError,
    ViaFiles,
    ViaFilesConfig,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_TEST_SCHEMA = pa.schema([("id", pa.string()), ("name", pa.string())])


def _make_container() -> ArrowRecordContainer:
    return ArrowRecordContainer(
        schema=_TEST_SCHEMA,
        unknown_field_policy="drop",
        coercion_policy="coerce",
    )


def _ndjson_bytes(records: list[dict[str, Any]]) -> bytes:
    """Encode records as newline-delimited JSON (plain text)."""
    return b"\n".join(orjson.dumps(r) for r in records) + b"\n"


def _gzip_bytes(data: bytes) -> bytes:
    """Gzip-compress raw bytes."""
    return gzip.compress(data)


class _FakeStreamReader:
    """Simulates ``aiohttp.StreamReader.iter_chunked()``."""

    def __init__(self, data: bytes, chunk_size: int = 1024) -> None:
        self._data = data
        self._chunk_size = chunk_size

    def iter_chunked(self, n: int) -> Any:
        async def _iter() -> Any:
            offset = 0
            while offset < len(self._data):
                chunk = self._data[offset : offset + n]
                offset += n
                yield chunk

        return _iter()


class _FakeResponse:
    """Minimal aiohttp.ClientResponse stand-in for streaming tests."""

    def __init__(
        self, data: bytes, *, chunk_size: int = 1024, status: int = 200
    ) -> None:
        self.content = _FakeStreamReader(data, chunk_size)
        self.status = status
        self.content_length = len(data)

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise Exception(f"HTTP {self.status}")


# ------------------------------------------------------------------
# 1. ViaFilesConfig
# ------------------------------------------------------------------


class TestViaFilesConfig:
    def test_defaults(self) -> None:
        config = ViaFilesConfig()
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 10
        assert config.client_timeout == 300
        assert config.parse_batch_size == 5000

    def test_custom_values(self) -> None:
        config = ViaFilesConfig(download_workers=8, retry_attempts=5)
        assert config.download_workers == 8
        assert config.retry_attempts == 5


# ------------------------------------------------------------------
# 2. _redact_url
# ------------------------------------------------------------------


class TestRedactUrl:
    def test_strips_query_string(self) -> None:
        url = (
            "https://blob.core.windows.net/export/file.gz?sp=r&st=2024-01-01&sig=secret"
        )
        redacted = ViaFiles._redact_url(url)
        assert "secret" not in redacted
        assert "sig=" not in redacted
        assert redacted == "https://blob.core.windows.net/export/file.gz"

    def test_preserves_path(self) -> None:
        url = "https://example.com/a/b/c?key=val"
        assert ViaFiles._redact_url(url) == "https://example.com/a/b/c"

    def test_handles_no_query(self) -> None:
        url = "https://example.com/path"
        assert ViaFiles._redact_url(url) == "https://example.com/path"

    def test_fallback_on_garbage(self) -> None:
        # Should not raise even on malformed input
        result = ViaFiles._redact_url("")
        assert isinstance(result, str)


# ------------------------------------------------------------------
# 3. _stream_export_records — plain text
# ------------------------------------------------------------------


class TestStreamExportRecordsPlain:
    @pytest.fixture
    def via(self) -> ViaFiles:
        return ViaFiles(ViaFilesConfig(parse_batch_size=2, download_chunk_size=64))

    @pytest.mark.asyncio
    async def test_parses_plain_ndjson(self, via: ViaFiles) -> None:
        records = [{"id": "1", "name": "a"}, {"id": "2", "name": "b"}]
        data = _ndjson_bytes(records)
        response = _FakeResponse(data)
        queue: asyncio.Queue[list[dict[str, Any]] | None] = asyncio.Queue()

        count = await via._stream_export_records(
            response, "http://fake/file.json", queue
        )

        assert count == 2
        batch = await queue.get()
        assert batch == records

    @pytest.mark.asyncio
    async def test_handles_empty_lines(self, via: ViaFiles) -> None:
        data = b'{"id":"1","name":"x"}\n\n\n{"id":"2","name":"y"}\n'
        response = _FakeResponse(data)
        queue: asyncio.Queue[list[dict[str, Any]] | None] = asyncio.Queue()

        count = await via._stream_export_records(response, "http://fake/f", queue)
        assert count == 2

    @pytest.mark.asyncio
    async def test_empty_response_returns_zero(self, via: ViaFiles) -> None:
        response = _FakeResponse(b"")
        queue: asyncio.Queue[list[dict[str, Any]] | None] = asyncio.Queue()

        count = await via._stream_export_records(response, "http://fake/f", queue)
        assert count == 0
        assert queue.empty()


# ------------------------------------------------------------------
# 4. _stream_export_records — gzip
# ------------------------------------------------------------------


class TestStreamExportRecordsGzip:
    @pytest.fixture
    def via(self) -> ViaFiles:
        return ViaFiles(ViaFilesConfig(parse_batch_size=10, download_chunk_size=256))

    @pytest.mark.asyncio
    async def test_decompresses_gzip(self, via: ViaFiles) -> None:
        records = [{"id": str(i), "name": f"rec-{i}"} for i in range(5)]
        data = _gzip_bytes(_ndjson_bytes(records))
        response = _FakeResponse(data)
        queue: asyncio.Queue[list[dict[str, Any]] | None] = asyncio.Queue()

        count = await via._stream_export_records(response, "http://fake/f.gz", queue)

        assert count == 5
        batch = await queue.get()
        assert batch is not None
        assert len(batch) == 5
        assert batch[0]["id"] == "0"

    @pytest.mark.asyncio
    async def test_gzip_batching(self) -> None:
        """Records are emitted in batches of parse_batch_size."""
        via = ViaFiles(ViaFilesConfig(parse_batch_size=3, download_chunk_size=8192))
        records = [{"id": str(i), "name": f"n{i}"} for i in range(7)]
        data = _gzip_bytes(_ndjson_bytes(records))
        response = _FakeResponse(data)
        queue: asyncio.Queue[list[dict[str, Any]] | None] = asyncio.Queue()

        count = await via._stream_export_records(response, "http://fake/f.gz", queue)

        assert count == 7
        # First batch: 3, second batch: 3, third batch: 1
        b1 = await queue.get()
        assert b1 is not None
        assert len(b1) == 3
        b2 = await queue.get()
        assert b2 is not None
        assert len(b2) == 3
        b3 = await queue.get()
        assert b3 is not None
        assert len(b3) == 1


# ------------------------------------------------------------------
# 5. _append_export_records
# ------------------------------------------------------------------


class TestAppendExportRecords:
    @pytest.mark.asyncio
    async def test_extends_container_from_queue(self) -> None:
        via = ViaFiles()
        container = _make_container()
        queue: asyncio.Queue[list[dict[str, Any]] | None] = asyncio.Queue()

        await queue.put([{"id": "1", "name": "a"}])
        await queue.put([{"id": "2", "name": "b"}])
        await queue.put(None)  # sentinel

        await via._append_export_records(queue, container)

        table = container.to_table()
        assert table.num_rows == 2

    @pytest.mark.asyncio
    async def test_stops_on_none_sentinel(self) -> None:
        via = ViaFiles()
        container = _make_container()
        queue: asyncio.Queue[list[dict[str, Any]] | None] = asyncio.Queue()

        await queue.put(None)
        await via._append_export_records(queue, container)
        assert container.to_table().num_rows == 0


# ------------------------------------------------------------------
# 6. download_export_files — integration-style with aiohttp mocking
# ------------------------------------------------------------------


class _FakeAsyncCtx:
    """Async context manager that returns a _FakeResponse on __aenter__."""

    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    async def __aenter__(self) -> _FakeResponse:
        return self._response

    async def __aexit__(self, *args: Any) -> None:
        pass


class _FakeClientSession:
    """Minimal stand-in for aiohttp.ClientSession as an async context manager."""

    def __init__(self, get_side_effect: Any = None) -> None:
        self._get_side_effect = get_side_effect
        self._default_response: _FakeResponse | None = None

    async def __aenter__(self) -> "_FakeClientSession":
        return self

    async def __aexit__(self, *args: Any) -> None:
        pass

    def get(self, url: str, **kwargs: Any) -> _FakeAsyncCtx | _RaisingAsyncCtx:
        if self._get_side_effect is not None:
            return self._get_side_effect(url, **kwargs)
        assert self._default_response is not None
        return _FakeAsyncCtx(self._default_response)


class _RaisingAsyncCtx:
    """Async context manager that raises on __aenter__."""

    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def __aenter__(self) -> None:
        raise self._exc

    async def __aexit__(self, *args: Any) -> None:
        pass


class TestDownloadExportFiles:
    @pytest.mark.asyncio
    async def test_downloads_single_plain_blob(self) -> None:
        records = [{"id": "1", "name": "hello"}, {"id": "2", "name": "world"}]
        blob_data = _ndjson_bytes(records)

        via = ViaFiles(ViaFilesConfig(download_workers=2, client_timeout=10))
        container = _make_container()

        fake_session = _FakeClientSession()
        fake_session._default_response = _FakeResponse(blob_data)

        with patch(
            "mde_client.viaFiles.aiohttp.ClientSession", return_value=fake_session
        ):
            result = await via.download_export_files(
                ["https://blob.example.com/file1.json?sig=x"],
                container,
            )

        assert result is container
        table = container.to_table()
        assert table.num_rows == 2
        assert table.column("id").to_pylist() == ["1", "2"]

    @pytest.mark.asyncio
    async def test_downloads_gzipped_blob(self) -> None:
        records = [{"id": "g1", "name": "gzipped"}]
        blob_data = _gzip_bytes(_ndjson_bytes(records))

        via = ViaFiles(ViaFilesConfig(download_workers=1, client_timeout=10))
        container = _make_container()

        fake_session = _FakeClientSession()
        fake_session._default_response = _FakeResponse(blob_data)

        with patch(
            "mde_client.viaFiles.aiohttp.ClientSession", return_value=fake_session
        ):
            result = await via.download_export_files(
                ["https://blob.example.com/file.gz?sig=y"],
                container,
            )

        assert result.to_table().num_rows == 1
        assert result.to_table().column("name").to_pylist() == ["gzipped"]

    @pytest.mark.asyncio
    async def test_multiple_urls(self) -> None:
        records_a = [{"id": "a1", "name": "fileA"}]
        records_b = [{"id": "b1", "name": "fileB"}, {"id": "b2", "name": "fileB2"}]
        blob_a = _ndjson_bytes(records_a)
        blob_b = _ndjson_bytes(records_b)

        via = ViaFiles(ViaFilesConfig(download_workers=2, client_timeout=10))
        container = _make_container()

        call_count = 0

        def get_side_effect(url: str, **kwargs: Any) -> _FakeAsyncCtx:
            nonlocal call_count
            call_count += 1
            data = blob_a if call_count == 1 else blob_b
            return _FakeAsyncCtx(_FakeResponse(data))

        fake_session = _FakeClientSession(get_side_effect=get_side_effect)

        with patch(
            "mde_client.viaFiles.aiohttp.ClientSession", return_value=fake_session
        ):
            await via.download_export_files(
                ["https://blob.example.com/a.json", "https://blob.example.com/b.json"],
                container,
            )

        assert container.to_table().num_rows == 3

    @pytest.mark.asyncio
    async def test_empty_urls_list(self) -> None:
        via = ViaFiles()
        container = _make_container()
        result = await via.download_export_files([], container)
        assert result is container
        assert result.to_table().num_rows == 0


# ------------------------------------------------------------------
# 7. Retry behaviour
# ------------------------------------------------------------------


class TestRetryBehaviour:
    @pytest.mark.asyncio
    async def test_retries_on_client_error(self) -> None:
        """Should retry on aiohttp.ClientError and succeed on second attempt."""
        records = [{"id": "1", "name": "retry-ok"}]
        blob_data = _ndjson_bytes(records)

        via = ViaFiles(
            ViaFilesConfig(
                download_workers=1,
                client_timeout=10,
                retry_attempts=3,
                retry_delay_seconds=0,
            )
        )
        container = _make_container()

        attempt_count = 0

        def get_side_effect(
            url: str, **kwargs: Any
        ) -> _FakeAsyncCtx | _RaisingAsyncCtx:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                return _RaisingAsyncCtx(aiohttp.ClientError("boom"))
            return _FakeAsyncCtx(_FakeResponse(blob_data))

        fake_session = _FakeClientSession(get_side_effect=get_side_effect)

        with patch(
            "mde_client.viaFiles.aiohttp.ClientSession", return_value=fake_session
        ):
            await via.download_export_files(["https://blob.example.com/f"], container)

        assert attempt_count == 2
        assert container.to_table().num_rows == 1

    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self) -> None:
        """Should raise RuntimeError after exhausting retries."""
        via = ViaFiles(
            ViaFilesConfig(
                download_workers=1,
                client_timeout=5,
                retry_attempts=2,
                retry_delay_seconds=0,
            )
        )
        container = _make_container()

        def get_side_effect(url: str, **kwargs: Any) -> _RaisingAsyncCtx:
            return _RaisingAsyncCtx(aiohttp.ClientError("fail"))

        fake_session = _FakeClientSession(get_side_effect=get_side_effect)

        with patch(
            "mde_client.viaFiles.aiohttp.ClientSession", return_value=fake_session
        ):
            with pytest.raises(RuntimeError, match="Failed to download"):
                await via.download_export_files(
                    ["https://blob.example.com/bad"], container
                )

    @pytest.mark.asyncio
    async def test_skips_empty_blob_after_retries(self) -> None:
        """Empty blobs (zero records) are skipped, not raised as fatal errors."""
        via = ViaFiles(
            ViaFilesConfig(
                download_workers=1,
                client_timeout=10,
                retry_attempts=2,
                retry_delay_seconds=0,
            )
        )
        container = _make_container()

        def get_side_effect(url: str, **kwargs: Any) -> _FakeAsyncCtx:
            return _FakeAsyncCtx(_FakeResponse(b""))

        fake_session = _FakeClientSession(get_side_effect=get_side_effect)

        with patch(
            "mde_client.viaFiles.aiohttp.ClientSession", return_value=fake_session
        ):
            # Should NOT raise — empty blobs are gracefully skipped
            await via.download_export_files(
                ["https://blob.example.com/empty"], container
            )

        assert container.to_table().num_rows == 0


# ------------------------------------------------------------------
# 8. EmptyExportBlobError
# ------------------------------------------------------------------


class TestEmptyExportBlobError:
    def test_is_runtime_error(self) -> None:
        assert issubclass(EmptyExportBlobError, RuntimeError)

    def test_message(self) -> None:
        err = EmptyExportBlobError("test message")
        assert str(err) == "test message"


# ------------------------------------------------------------------
# 9. ViaFiles with custom config
# ------------------------------------------------------------------


class TestViaFilesInit:
    def test_default_config(self) -> None:
        via = ViaFiles()
        assert via._config.retry_attempts == 3

    def test_custom_config(self) -> None:
        config = ViaFilesConfig(retry_attempts=10, download_workers=32)
        via = ViaFiles(config)
        assert via._config.retry_attempts == 10
        assert via._config.download_workers == 32


# ------------------------------------------------------------------
# 10. record_transform callback
# ------------------------------------------------------------------


class TestRecordTransform:
    @pytest.mark.asyncio
    async def test_stream_applies_transform(self) -> None:
        """_stream_export_records should apply record_transform to each parsed record."""
        via = ViaFiles(ViaFilesConfig(parse_batch_size=10, download_chunk_size=8192))
        # Records with nested data, simulating DeviceGatheredInfo wrapping
        records = [
            {"rbacGroupId": 1, "DeviceGatheredInfo": {"id": "a", "name": "dev-a"}},
            {"rbacGroupId": 2, "DeviceGatheredInfo": {"id": "b", "name": "dev-b"}},
        ]
        data = _ndjson_bytes(records)
        response = _FakeResponse(data)
        queue: asyncio.Queue[list[dict[str, Any]] | None] = asyncio.Queue()

        def flatten(record: dict[str, Any]) -> dict[str, Any]:
            nested = record.pop("DeviceGatheredInfo", None)
            if isinstance(nested, dict):
                nested.update(record)
                return nested
            return record

        count = await via._stream_export_records(
            response,
            "http://fake/f",
            queue,
            record_transform=flatten,
        )

        assert count == 2
        batch = await queue.get()
        assert batch is not None
        batch1 = batch[0]
        batch2 = batch[1]
        assert batch1 == {"id": "a", "name": "dev-a", "rbacGroupId": 1}
        assert batch2 == {"id": "b", "name": "dev-b", "rbacGroupId": 2}

    @pytest.mark.asyncio
    async def test_download_with_transform(self) -> None:
        """download_export_files should thread record_transform through to parsing."""
        records = [
            {"wrapper": {"id": "1", "name": "inner"}, "extra": "top"},
        ]
        blob_data = _ndjson_bytes(records)

        via = ViaFiles(ViaFilesConfig(download_workers=1, client_timeout=10))
        container = _make_container()

        fake_session = _FakeClientSession()
        fake_session._default_response = _FakeResponse(blob_data)

        def unwrap(record: dict[str, Any]) -> dict[str, Any]:
            inner = record.pop("wrapper", {})
            inner.update(record)
            return inner

        with patch(
            "mde_client.viaFiles.aiohttp.ClientSession", return_value=fake_session
        ):
            await via.download_export_files(
                ["https://blob.example.com/f"],
                container,
                record_transform=unwrap,
            )

        table = container.to_table()
        assert table.num_rows == 1
        assert table.column("id").to_pylist() == ["1"]
        assert table.column("name").to_pylist() == ["inner"]

    @pytest.mark.asyncio
    async def test_none_transform_is_identity(self) -> None:
        """When record_transform is None, records pass through unchanged."""
        records = [{"id": "1", "name": "plain"}]
        blob_data = _ndjson_bytes(records)

        via = ViaFiles(ViaFilesConfig(download_workers=1, client_timeout=10))
        container = _make_container()

        fake_session = _FakeClientSession()
        fake_session._default_response = _FakeResponse(blob_data)

        with patch(
            "mde_client.viaFiles.aiohttp.ClientSession", return_value=fake_session
        ):
            await via.download_export_files(
                ["https://blob.example.com/f"],
                container,
                record_transform=None,
            )

        assert container.to_table().num_rows == 1
        assert container.to_table().column("id").to_pylist() == ["1"]
