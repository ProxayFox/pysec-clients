"""Tests for the lazy MachineResults wrapper and streaming pagination."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import polars as pl
import pyarrow as pa
from http_to_arrow import ArrowRecordContainer

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


class _FakeEndpoint(MachinesEndpoint):
    """MachinesEndpoint with a fake ``_arequest`` that serves pre-canned pages.

    *chain_pages*: when True (default) pages are linked via ``@odata.nextLink``
    so a single ``_paginate_into`` call consumes all of them.  When False each
    call returns a standalone single-page response — useful for counting exact
    fetches.
    """

    def __init__(
        self,
        pages: list[list[dict[str, Any]]],
        *,
        chain_pages: bool = True,
    ) -> None:
        http_client = MagicMock(spec=httpx.Client)
        http_client.base_url = "https://fake.api"
        auth = MagicMock()
        auth.token = "fake-token"
        super().__init__(http_client, auth)
        self._pages = pages
        self._chain_pages = chain_pages
        self._call_index = 0
        # A list so callers can hold a live reference to the count.
        self.counter: list[int] = [0]

    async def _arequest(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        idx = self._call_index
        self._call_index += 1
        self.counter[0] += 1
        body: dict[str, Any] = {"value": self._pages[idx]}
        if self._chain_pages and idx < len(self._pages) - 1:
            body["@odata.nextLink"] = "/next"
        return _fake_response(body)


class _FakeMachineResults(MachineResults):
    """MachineResults whose ``_ensure_fetched`` uses a caller-supplied schema."""

    def __init__(
        self,
        endpoint: MachinesEndpoint,
        params: dict[str, str],
        schema: pa.Schema,
    ) -> None:
        super().__init__(endpoint, params)
        self._schema = schema

    def _ensure_fetched(self) -> ArrowRecordContainer:
        if self._container is None:
            container = ArrowRecordContainer(schema=self._schema)
            self._endpoint._paginate_into(
                MachinesEndpoint._PATH,
                self._params,
                container,
            )
            self._container = container
        return self._container


# A minimal schema that matches the fake records used in tests.
_TEST_SCHEMA = pa.schema(
    [
        ("id", pa.string()),
        ("name", pa.string()),
    ]
)


def _make_results(
    pages: list[list[dict[str, Any]]],
    query: MachinesQuery | None = None,
    schema: pa.Schema = _TEST_SCHEMA,
) -> _FakeMachineResults:
    """Build a _FakeMachineResults backed by fake paged responses."""
    endpoint = _FakeEndpoint(pages)
    params = query.to_odata_filters if query else {}
    return _FakeMachineResults(endpoint, params, schema)


# ------------------------------------------------------------------
# 1. Construction is lazy — zero HTTP requests
# ------------------------------------------------------------------


class TestLazyConstruction:
    def test_no_request_on_construction(self) -> None:
        """Creating a MachineResults must not trigger any HTTP call."""
        endpoint = _FakeEndpoint([[]], chain_pages=False)

        _ = MachineResults(endpoint, {})
        assert endpoint.counter[0] == 0

    def test_get_all_returns_machine_results(self) -> None:
        endpoint = _FakeEndpoint([[]])
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

        records = results.to_dicts()
        assert len(records) == 3
        assert records[0]["id"] == "1"
        assert records[2]["id"] == "3"

    def test_single_page(self) -> None:
        results = _make_results([[{"id": "x", "name": "y"}]])
        records = results.to_dicts()
        assert len(records) == 1

    def test_empty_response(self) -> None:
        results = _make_results([[]])
        records = results.to_dicts()
        assert records == []


# ------------------------------------------------------------------
# 3. Cached container — no second network call
# ------------------------------------------------------------------


class TestCaching:
    def test_second_terminal_call_reuses_cache(self) -> None:
        """Calling two different terminal methods must not issue a second fetch."""
        page = [{"id": "1", "name": "cached"}]
        endpoint = _FakeEndpoint([page], chain_pages=False)
        results = _FakeMachineResults(endpoint, {}, _TEST_SCHEMA)

        # First terminal call fetches
        _ = results.to_dicts()
        first_count = endpoint.counter[0]

        # Second terminal call (different format) must not fetch again
        _ = results.to_arrow()
        assert endpoint.counter[0] == first_count

    def test_to_dicts_and_to_arrow_return_same_data(self) -> None:
        results = _make_results([[{"id": "1", "name": "same"}]])
        json_data = results.to_dicts()
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
        endpoint = _FakeEndpoint([page, page], chain_pages=False)
        results = _FakeMachineResults(endpoint, {}, _TEST_SCHEMA)

        _ = results.to_dicts()
        first_count = endpoint.counter[0]

        # refresh + terminal call must fetch again
        _ = results.refresh().to_dicts()
        assert endpoint.counter[0] == first_count + 1

    def test_refresh_is_chainable_with_different_formats(self) -> None:
        """refresh().to_arrow() and refresh().to_polars() must both work."""
        results = _make_results([[{"id": "1", "name": "a"}]])
        table = results.refresh().to_arrow()
        assert isinstance(table, pa.Table)


# ------------------------------------------------------------------
# 5. to_dicts() works without pyarrow/polars extras
# ------------------------------------------------------------------


class TestToJsonBaseInstall:
    def test_to_dicts_returns_list_of_dicts(self) -> None:
        results = _make_results([[{"id": "1", "name": "hello"}]])
        data = results.to_dicts()
        assert isinstance(data, list)
        assert isinstance(data[0], dict)
        assert data[0]["name"] == "hello"


# ------------------------------------------------------------------
# 6. Terminal materialization helpers
# ------------------------------------------------------------------


class TestTerminalFormats:
    def test_to_arrow_returns_table(self) -> None:
        """to_arrow() should materialize records into a pyarrow Table."""
        results = _make_results([[{"id": "1", "name": "a"}]])
        table = results.to_arrow()

        assert isinstance(table, pa.Table)
        assert table.to_pylist() == [{"id": "1", "name": "a"}]

    def test_to_polars_returns_dataframe(self) -> None:
        """to_polars() should materialize records into a polars DataFrame."""
        results = _make_results([[{"id": "1", "name": "a"}]])
        frame = results.to_polars()

        assert isinstance(frame, pl.DataFrame)
        assert frame.to_dicts() == [{"id": "1", "name": "a"}]
