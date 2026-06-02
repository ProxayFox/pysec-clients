"""Tests for shared BaseEndpoint, BaseQuery, and BaseResults primitives."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from http_to_arrow import ArrowRecordContainer

from mde_client.endpoints.base import BaseEndpoint, BaseQuery, BaseResults


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _resp(
    status: int = 200,
    *,
    body: dict | list | None = None,
    text: str | None = None,
    url: str = "https://fake.api/path",
) -> httpx.Response:
    if body is not None:
        return httpx.Response(status, json=body, request=httpx.Request("GET", url))
    return httpx.Response(status, text=text or "", request=httpx.Request("GET", url))


class _RecordingEndpoint(BaseEndpoint):
    _PATH = "/api/test"

    def __init__(self, responses: list[httpx.Response]) -> None:
        http = MagicMock(spec=httpx.Client)
        http.base_url = "https://fake.api"
        auth = MagicMock()
        auth.token = "fake-token"
        super().__init__(http, auth)
        self._responses = responses
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def _arequest(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self.calls.append((method, path, kwargs))
        return self._responses.pop(0)


# ---------------------------------------------------------------------------
# Helper methods
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_id_list_wraps_string(self) -> None:
        assert BaseEndpoint._id_list("abc") == ["abc"]

    def test_id_list_passes_list_through(self) -> None:
        assert BaseEndpoint._id_list(["a", "b"]) == ["a", "b"]

    def test_chunks_splits_evenly(self) -> None:
        assert list(BaseEndpoint._chunks([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]

    def test_chunks_empty(self) -> None:
        assert list(BaseEndpoint._chunks([], 3)) == []


# ---------------------------------------------------------------------------
# _arequest token + header injection
# ---------------------------------------------------------------------------


class TestArequestHeaders:
    def test_injects_bearer_header(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict[str, Any] = {}

        class _FakeAsyncClient:
            def __init__(self, *, base_url, timeout) -> None:
                captured["base_url"] = base_url
                captured["timeout"] = timeout

            async def __aenter__(self):
                return self

            async def __aexit__(self, *exc) -> None:
                pass

            async def request(self, method, path, **kwargs):
                captured["method"] = method
                captured["path"] = path
                captured["headers"] = kwargs.get("headers")
                return _resp(200, body={"value": []})

        monkeypatch.setattr(httpx, "AsyncClient", _FakeAsyncClient)

        http = MagicMock(spec=httpx.Client)
        http.base_url = "https://fake.api"
        http.timeout = httpx.Timeout(5.0)
        auth = MagicMock()
        auth.token = "the-token"

        endpoint = BaseEndpoint(http, auth)
        endpoint._request("GET", "/api/x")

        assert captured["method"] == "GET"
        assert captured["path"] == "/api/x"
        assert captured["headers"] == {"Authorization": "Bearer the-token"}
        assert captured["base_url"] == http.base_url


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class TestPagination:
    def test_paginate_follows_next_link(self) -> None:
        endpoint = _RecordingEndpoint(
            [
                _resp(
                    200, body={"value": [{"id": 1}], "@odata.nextLink": "/api/test?p=2"}
                ),
                _resp(200, body={"value": [{"id": 2}]}),
            ]
        )
        records = endpoint._paginate("/api/test", {})
        assert [r["id"] for r in records] == [1, 2]
        # Second call used the nextLink as the path.
        assert endpoint.calls[1][1] == "/api/test?p=2"

    def test_paginate_rejects_top(self) -> None:
        endpoint = _RecordingEndpoint([])
        with pytest.raises(ValueError, match="\\$top"):
            endpoint._paginate("/api/test", {"$top": "5"})

    def test_paginate_rejects_skip(self) -> None:
        endpoint = _RecordingEndpoint([])
        with pytest.raises(ValueError, match="\\$top"):
            endpoint._paginate("/api/test", {"$skip": "5"})

    def test_paginate_into_streams_pages(self) -> None:
        endpoint = _RecordingEndpoint(
            [
                _resp(200, body={"value": [{"id": "a"}], "@odata.nextLink": "/next"}),
                _resp(200, body={"value": [{"id": "b"}]}),
            ]
        )
        container = ArrowRecordContainer(schema=None)
        endpoint._paginate_into("/api/test", {}, container)
        assert container.to_polars.to_dicts() == [{"id": "a"}, {"id": "b"}]


class TestPaginateIntoErrors:
    def test_403_raises_permission_error(self) -> None:
        body = {
            "error": {
                "code": "Forbidden",
                "message": "Need WindowsDefenderATP.Read.All",
            }
        }
        endpoint = _RecordingEndpoint([_resp(403, body=body)])
        container = ArrowRecordContainer(schema=None)
        with pytest.raises(PermissionError, match="WindowsDefenderATP.Read.All"):
            endpoint._paginate_into("/api/test", {}, container)

    def test_non_403_raises_http_status_error_with_body(self) -> None:
        endpoint = _RecordingEndpoint(
            [_resp(500, text="boom", url="https://fake.api/api/test")]
        )
        container = ArrowRecordContainer(schema=None)
        with pytest.raises(httpx.HTTPStatusError, match="boom") as exc:
            endpoint._paginate_into("/api/test", {}, container)
        assert "500" in str(exc.value)


# ---------------------------------------------------------------------------
# BaseResults
# ---------------------------------------------------------------------------


class TestBaseResultsRecordsFromBody:
    def test_list_passthrough(self) -> None:
        assert BaseResults._records_from_body([{"a": 1}]) == [{"a": 1}]

    def test_value_list(self) -> None:
        assert BaseResults._records_from_body({"value": [{"a": 1}]}) == [{"a": 1}]

    def test_value_dict_wrapped(self) -> None:
        assert BaseResults._records_from_body({"value": {"a": 1}}) == [{"a": 1}]

    def test_top_level_dict(self) -> None:
        assert BaseResults._records_from_body({"a": 1}) == [{"a": 1}]

    def test_unknown_shape(self) -> None:
        assert BaseResults._records_from_body(None) == []


class TestBaseResultsLifecycle:
    def test_refresh_clears_container(self) -> None:
        endpoint = _RecordingEndpoint(
            [
                _resp(200, body={"value": [{"id": 1}]}),
                _resp(200, body={"value": [{"id": 2}]}),
            ]
        )
        results = BaseResults(endpoint, {})
        results.SCHEMA = None
        first = results.to_dicts()
        assert first == [{"id": 1}]
        # Second call without refresh should not refetch.
        assert results.to_dicts() == [{"id": 1}]
        results.refresh()
        assert results.to_dicts() == [{"id": 2}]

    def test_to_json_str(self) -> None:
        endpoint = _RecordingEndpoint([_resp(200, body={"value": [{"id": 1}]})])
        results = BaseResults(endpoint, {})
        results.SCHEMA = None
        out = results.to_json()
        assert isinstance(out, bytes)
        assert b'"id":1' in out

    def test_to_json_indented(self) -> None:
        endpoint = _RecordingEndpoint([_resp(200, body={"value": [{"id": 1}]})])
        results = BaseResults(endpoint, {})
        results.SCHEMA = None
        out = results.to_json(indent=True)
        assert isinstance(out, str)
        assert "\n" in out

    def test_single_uses_request_path(self) -> None:
        endpoint = _RecordingEndpoint([_resp(200, body={"id": "abc"})])
        results = BaseResults(endpoint, {}, path="/api/test/abc", single=True)
        results.SCHEMA = None
        assert results.to_dicts() == [{"id": "abc"}]
        assert endpoint.calls[0][1] == "/api/test/abc"

    def test_top_param_skips_pagination(self) -> None:
        endpoint = _RecordingEndpoint(
            [_resp(200, body={"value": [{"id": 1}], "@odata.nextLink": "/next"})]
        )
        results = BaseResults(endpoint, {"$top": "1"})
        results.SCHEMA = None
        assert results.to_dicts() == [{"id": 1}]
        # Only one call made — pagination skipped.
        assert len(endpoint.calls) == 1

    def test_normalize_export_record_default_is_none(self) -> None:
        assert BaseResults._normalize_export_record() is None


# ---------------------------------------------------------------------------
# BaseQuery
# ---------------------------------------------------------------------------


class _DemoQuery(BaseQuery):
    name: str | list[str] | None = None
    label: str | None = None


class TestBaseQueryFilters:
    def test_page_size_defaults_to_10000(self) -> None:
        params = _DemoQuery().to_odata_filters
        assert params["pageSize"] == "10000"

    def test_string_filter(self) -> None:
        params = _DemoQuery(page_size=None, name="alpha").to_odata_filters
        assert params["$filter"] == "name eq 'alpha'"

    def test_string_escapes_quote(self) -> None:
        params = _DemoQuery(page_size=None, name="a'b").to_odata_filters
        assert params["$filter"] == "name eq 'a''b'"

    def test_list_filter_in_clause(self) -> None:
        params = _DemoQuery(page_size=None, name=["a", "b"]).to_odata_filters
        assert params["$filter"] == "name in ('a', 'b')"

    def test_multiple_filters_joined_with_and(self) -> None:
        params = _DemoQuery(page_size=None, name="alpha", label="beta").to_odata_filters
        assert "name eq 'alpha'" in params["$filter"]
        assert "label eq 'beta'" in params["$filter"]
        assert " and " in params["$filter"]

    def test_top_and_skip_serialised(self) -> None:
        params = _DemoQuery(page_size=None, top=5, skip=10).to_odata_filters
        assert params["$top"] == "5"
        assert params["$skip"] == "10"

    def test_top_omits_default_page_size(self) -> None:
        params = _DemoQuery(top=5).to_odata_filters
        assert params["$top"] == "5"
        assert "pageSize" not in params

    def test_page_size_cannot_be_combined_with_top(self) -> None:
        with pytest.raises(ValueError, match="page_size.*\\$top.*\\$skip"):
            _DemoQuery(page_size=100, top=5).to_odata_filters

    def test_page_size_cannot_be_combined_with_skip(self) -> None:
        with pytest.raises(ValueError, match="page_size.*\\$top.*\\$skip"):
            _DemoQuery(page_size=100, skip=10).to_odata_filters

    def test_since_time_int_becomes_iso(self) -> None:
        params = _DemoQuery(page_size=None, sinceTime=1).to_odata_filters
        assert "sinceTime" in params
        # Should be ISO 8601 with TZ suffix.
        assert "T" in params["sinceTime"]

    def test_since_time_string_passthrough(self) -> None:
        params = _DemoQuery(
            page_size=None, sinceTime="2025-01-01T00:00:00Z"
        ).to_odata_filters
        assert params["sinceTime"] == "2025-01-01T00:00:00Z"
