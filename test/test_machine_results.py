"""Tests for the lazy MachineResults wrapper and streaming pagination."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import pyarrow as pa
import pytest

from mde_client.endpoints.machines import (
    MachineResults,
    MachinesEndpoint,
    MachinesQuery,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _fake_response(body: dict[str, Any]) -> httpx.Response:
    """Build a 200 httpx.Response with the given JSON body."""
    return httpx.Response(
        200,
        json=body,
        request=httpx.Request("GET", "https://fake.api/"),
    )


def _make_endpoint(pages: list[list[dict[str, Any]]]) -> MachinesEndpoint:
    """Build a MachinesEndpoint whose ``_arequest`` yields *pages* in order.

    Each element of *pages* becomes one paginated response.  The last page
    has no ``@odata.nextLink``; earlier pages include one that points to a
    synthetic ``/next`` URL.
    """
    call_index = 0

    async def _fake_arequest(method: str, path: str, **kwargs: Any) -> httpx.Response:
        nonlocal call_index
        idx = call_index
        call_index += 1
        body: dict[str, Any] = {"value": pages[idx]}
        if idx < len(pages) - 1:
            body["@odata.nextLink"] = "/next"
        return _fake_response(body)

    http_client = MagicMock(spec=httpx.Client)
    http_client.base_url = "https://fake.api"
    auth = MagicMock()
    auth.token = "fake-token"
    endpoint = MachinesEndpoint(http_client, auth)
    # type: ignore[assignment]  # ty: ignore[invalid-assignment]
    endpoint._arequest = _fake_arequest
    return endpoint


def _counting_endpoint(
    pages: list[list[dict[str, Any]]],
) -> tuple[MachinesEndpoint, list[int]]:
    """Like ``_make_endpoint`` but also returns a mutable counter list.

    ``counter[0]`` is incremented on each ``_arequest`` call so tests can
    assert exact request counts.  Unlike ``_make_endpoint``, **every page
    is treated as a standalone last page** (no ``@odata.nextLink``) so each
    ``_paginate_into`` invocation consumes exactly one entry.
    """
    counter = [0]
    call_index = 0

    async def _fake_arequest(method: str, path: str, **kwargs: Any) -> httpx.Response:
        nonlocal call_index
        counter[0] += 1
        idx = call_index
        call_index += 1
        body: dict[str, Any] = {"value": pages[idx]}
        # No @odata.nextLink — each fetch is a single-page response.
        return _fake_response(body)

    http_client = MagicMock(spec=httpx.Client)
    http_client.base_url = "https://fake.api"
    auth = MagicMock()
    auth.token = "fake-token"
    endpoint = MachinesEndpoint(http_client, auth)
    # type: ignore[assignment]  # ty: ignore[invalid-assignment]
    endpoint._arequest = _fake_arequest
    return endpoint, counter


# A minimal schema that matches the fake records used in tests.
_TEST_SCHEMA = pa.schema(
    [
        ("id", pa.string()),
        ("name", pa.string()),
    ]
)


def _patch_ensure_fetched(results: MachineResults, schema: pa.Schema) -> None:
    """Replace ``_ensure_fetched`` with one that uses *schema*."""
    from http_to_arrow import ArrowRecordContainer

    def _patched() -> None:
        if results._container is not None:
            return
        container = ArrowRecordContainer(schema=schema)
        results._endpoint._paginate_into(
            MachinesEndpoint._PATH,
            results._params,
            container,
        )
        results._container = container

    # type: ignore[assignment]  # ty: ignore[invalid-assignment]
    results._ensure_fetched = _patched


def _make_results(
    pages: list[list[dict[str, Any]]],
    query: MachinesQuery | None = None,
    schema: pa.Schema = _TEST_SCHEMA,
) -> MachineResults:
    """Build a MachineResults backed by fake paged responses."""
    endpoint = _make_endpoint(pages)
    params = query.to_odata_filters if query else {}
    results = MachineResults(endpoint, params)
    _patch_ensure_fetched(results, schema)
    return results


# ------------------------------------------------------------------
# 1. Construction is lazy — zero HTTP requests
# ------------------------------------------------------------------


class TestLazyConstruction:
    def test_no_request_on_construction(self) -> None:
        """Creating a MachineResults must not trigger any HTTP call."""
        endpoint, counter = _counting_endpoint([[]])

        _ = MachineResults(endpoint, {})
        assert counter[0] == 0

    def test_get_all_returns_machine_results(self) -> None:
        endpoint = _make_endpoint([[]])
        result = endpoint.get_all()
        assert isinstance(result, MachineResults)


# ------------------------------------------------------------------
# 2. Streaming pagination — no full list[dict]
# ------------------------------------------------------------------


class TestStreamingPagination:
    def test_multi_page_streaming(self) -> None:
        """Pages should be streamed into the container without building a full list."""
        page1 = [{"id": "1", "name": "a"}, {"id": "2", "name": "b"}]
        page2 = [{"id": "3", "name": "c"}]
        results = _make_results([page1, page2])

        records = results.to_json()
        assert len(records) == 3
        assert records[0]["id"] == "1"
        assert records[2]["id"] == "3"

    def test_single_page(self) -> None:
        results = _make_results([[{"id": "x", "name": "y"}]])
        records = results.to_json()
        assert len(records) == 1

    def test_empty_response(self) -> None:
        results = _make_results([[]])
        records = results.to_json()
        assert records == []


# ------------------------------------------------------------------
# 3. Cached container — no second network call
# ------------------------------------------------------------------


class TestCaching:
    def test_second_terminal_call_reuses_cache(self) -> None:
        """Calling two different terminal methods must not issue a second fetch."""
        page = [{"id": "1", "name": "cached"}]
        endpoint, counter = _counting_endpoint([page])
        results = MachineResults(endpoint, {})
        _patch_ensure_fetched(results, _TEST_SCHEMA)

        # First terminal call fetches
        _ = results.to_json()
        first_count = counter[0]

        # Second terminal call (different format) must not fetch again
        _ = results.to_arrow()
        assert counter[0] == first_count

    def test_to_json_and_to_arrow_return_same_data(self) -> None:
        results = _make_results([[{"id": "1", "name": "same"}]])
        json_data = results.to_json()
        arrow_data = results.to_arrow().to_pylist()
        assert json_data == arrow_data


# ------------------------------------------------------------------
# 4. refresh() clears cache and re-fetches
# ------------------------------------------------------------------


class TestRefresh:
    def test_refresh_returns_self(self) -> None:
        results = _make_results([[{"id": "1", "name": "a"}]])
        assert results.refresh() is results

    def test_refresh_clears_cache(self) -> None:
        page = [{"id": "1", "name": "a"}]
        endpoint, counter = _counting_endpoint([page, page])
        results = MachineResults(endpoint, {})
        _patch_ensure_fetched(results, _TEST_SCHEMA)

        _ = results.to_json()
        first_count = counter[0]

        # refresh + terminal call must fetch again
        _ = results.refresh().to_json()
        assert counter[0] == first_count + 1

    def test_refresh_is_chainable_with_different_formats(self) -> None:
        """refresh().to_arrow() and refresh().to_polars() must both work."""
        results = _make_results([[{"id": "1", "name": "a"}]])
        table = results.refresh().to_arrow()
        assert isinstance(table, pa.Table)


# ------------------------------------------------------------------
# 5. to_json() works without pyarrow/polars extras
# ------------------------------------------------------------------


class TestToJsonBaseInstall:
    def test_to_json_returns_list_of_dicts(self) -> None:
        results = _make_results([[{"id": "1", "name": "hello"}]])
        data = results.to_json()
        assert isinstance(data, list)
        assert isinstance(data[0], dict)
        assert data[0]["name"] == "hello"


# ------------------------------------------------------------------
# 6. Import guards on to_arrow / to_polars
# ------------------------------------------------------------------


class TestImportGuards:
    def test_to_arrow_import_guard(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """to_arrow() must raise ImportError with install instructions when
        pyarrow is not available."""
        import builtins

        real_import = builtins.__import__

        def _fake_import(name: str, *args: Any, **kwargs: Any):
            if name == "pyarrow":
                raise ImportError("fake missing pyarrow")
            return real_import(name, *args, **kwargs)

        results = _make_results([[{"id": "1", "name": "a"}]])
        monkeypatch.setattr(builtins, "__import__", _fake_import)
        with pytest.raises(ImportError, match="arrow"):
            results.to_arrow()

    def test_to_polars_import_guard(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """to_polars() must raise ImportError with install instructions when
        polars is not available."""
        import builtins

        real_import = builtins.__import__

        def _fake_import(name: str, *args: Any, **kwargs: Any):
            if name == "polars":
                raise ImportError("fake missing polars")
            return real_import(name, *args, **kwargs)

        results = _make_results([[{"id": "1", "name": "a"}]])
        monkeypatch.setattr(builtins, "__import__", _fake_import)
        with pytest.raises(ImportError, match="polars"):
            results.to_polars()


# ------------------------------------------------------------------
# 7. Terminal methods on the real _ensure_fetched (NotImplementedError)
# ------------------------------------------------------------------


class TestNotImplementedSchema:
    def test_ensure_fetched_raises_not_implemented(self) -> None:
        """Until MACHINES_SCHEMA is defined, _ensure_fetched must raise."""
        endpoint = _make_endpoint([[]])
        results = MachineResults(endpoint, {})
        # Do NOT patch — exercise the real _ensure_fetched
        with pytest.raises(NotImplementedError, match="MACHINES_SCHEMA"):
            results.to_json()
