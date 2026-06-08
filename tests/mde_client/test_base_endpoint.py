"""Tests for shared BaseEndpoint, BaseQuery, and BaseResults primitives."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone, tzinfo
from email.utils import format_datetime
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from http_to_arrow import ArrowRecordContainer

import mde_client.endpoints.base as base_module
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


class _SkipEndpoint(BaseEndpoint):
    _PATH = "/api/test"
    _RATE_LIMIT_BACKOFF_BASE_SECONDS = 0.0

    def __init__(
        self,
        batches: dict[int, list[dict[str, Any]]],
        *,
        responses: dict[int, list[httpx.Response]] | None = None,
    ) -> None:
        http = MagicMock(spec=httpx.Client)
        http.base_url = "https://fake.api"
        auth = MagicMock()
        auth.token = "fake-token"
        super().__init__(http, auth)
        self._batches = batches
        self._responses = responses or {}
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.sleep_calls: list[float] = []

    async def _arequest(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self.calls.append((method, path, kwargs))
        params = kwargs.get("params", {})
        offset = int(params.get("$skip", "0"))
        responses = self._responses.get(offset)
        if responses:
            return responses.pop(0)
        return _resp(200, body={"value": self._batches.get(offset, [])})

    async def _asleep(self, delay: float) -> None:
        self.sleep_calls.append(delay)
        await asyncio.sleep(0)


class _SkipResults(BaseResults):
    SCHEMA = None
    USE_CONCURRENT_SKIP_PAGINATION = True
    SKIP_PAGE_SIZE = 2
    SKIP_MAX_CONCURRENT = 3


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
        assert container.to_polars().to_dicts() == [{"id": "a"}, {"id": "b"}]

    def test_concurrent_skip_pagination_fetches_ordered_windows(self) -> None:
        endpoint = _SkipEndpoint(
            {
                0: [{"id": 0}, {"id": 1}],
                2: [{"id": 2}, {"id": 3}],
                4: [],
            }
        )
        container = ArrowRecordContainer(schema=None)
        endpoint._paginate_skip_into(
            "/api/test",
            {"pageSize": "10000", "$filter": "name eq 'a'"},
            container,
            page_size=2,
            max_concurrent=3,
        )

        assert container.to_polars().to_dicts() == [
            {"id": 0},
            {"id": 1},
            {"id": 2},
            {"id": 3},
        ]
        call_params = [call[2]["params"] for call in endpoint.calls]
        assert [params["$skip"] for params in call_params] == ["0", "2", "4"]
        assert all(params["$top"] == "2" for params in call_params)
        assert all("pageSize" not in params for params in call_params)
        assert all(params["$filter"] == "name eq 'a'" for params in call_params)

    def test_concurrent_skip_pagination_stops_after_short_page(self) -> None:
        endpoint = _SkipEndpoint(
            {
                0: [{"id": 0}, {"id": 1}],
                2: [{"id": 2}],
                4: [{"id": 4}, {"id": 5}],
            }
        )
        container = ArrowRecordContainer(schema=None)
        endpoint._paginate_skip_into(
            "/api/test", {}, container, page_size=2, max_concurrent=3
        )

        assert container.to_polars().to_dicts() == [
            {"id": 0},
            {"id": 1},
            {"id": 2},
        ]

    def test_concurrent_skip_pagination_rejects_manual_skip(self) -> None:
        endpoint = _SkipEndpoint({})
        container = ArrowRecordContainer(schema=None)
        with pytest.raises(ValueError, match="concurrent skip pagination"):
            endpoint._paginate_skip_into("/api/test", {"$skip": "10"}, container)

    def test_concurrent_skip_results_route_through_base_results(self) -> None:
        endpoint = _SkipEndpoint({0: [{"id": 0}, {"id": 1}], 2: []})
        results = _SkipResults(endpoint, {"pageSize": "10000"})

        assert results.to_dicts() == [{"id": 0}, {"id": 1}]
        assert all("pageSize" not in call[2]["params"] for call in endpoint.calls)

    def test_concurrent_skip_pagination_respects_endpoint_rate_cap(self) -> None:
        class _LimitedSkipEndpoint(_SkipEndpoint):
            _RATE_LIMIT_CALLS_PER_MINUTE = 2

        endpoint = _LimitedSkipEndpoint({0: [{"id": 0}], 1: []})
        container = ArrowRecordContainer(schema=None)
        endpoint._paginate_skip_into(
            "/api/test", {}, container, page_size=1, max_concurrent=10
        )

        assert [call[2]["params"]["$skip"] for call in endpoint.calls] == ["0", "1"]

    def test_rate_limit_retry_after_is_used_for_429(self) -> None:
        endpoint = _SkipEndpoint(
            {1: []},
            responses={
                0: [
                    httpx.Response(
                        429,
                        json={"error": "rate"},
                        headers={"Retry-After": "2"},
                        request=httpx.Request("GET", "https://fake.api/path"),
                    ),
                    _resp(200, body={"value": [{"id": 0}]}),
                ]
            },
        )
        container = ArrowRecordContainer(schema=None)
        endpoint._paginate_skip_into(
            "/api/test", {}, container, page_size=1, max_concurrent=1
        )

        assert endpoint.sleep_calls == [2.0]
        assert container.to_polars().to_dicts() == [{"id": 0}]

    def test_rate_limit_retry_after_http_date_is_used_for_429(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fixed_now = datetime(2026, 6, 3, 12, 0, 0, tzinfo=timezone.utc)
        retry_at = fixed_now + timedelta(seconds=90)

        class _FixedDatetime(datetime):
            @classmethod
            def now(cls, tz: tzinfo | None = None) -> datetime:
                if tz is None:
                    return fixed_now.replace(tzinfo=None)
                return fixed_now.astimezone(tz)

        monkeypatch.setattr(base_module, "datetime", _FixedDatetime)
        endpoint = _SkipEndpoint(
            {1: []},
            responses={
                0: [
                    httpx.Response(
                        429,
                        json={"error": "rate"},
                        headers={"Retry-After": format_datetime(retry_at, usegmt=True)},
                        request=httpx.Request("GET", "https://fake.api/path"),
                    ),
                    _resp(200, body={"value": [{"id": 0}]}),
                ]
            },
        )
        container = ArrowRecordContainer(schema=None)
        endpoint._paginate_skip_into(
            "/api/test", {}, container, page_size=1, max_concurrent=1
        )

        assert endpoint.sleep_calls == [90.0]
        assert container.to_polars().to_dicts() == [{"id": 0}]

    def test_rate_limit_without_retry_after_uses_backoff(self) -> None:
        class _BackoffSkipEndpoint(_SkipEndpoint):
            _RATE_LIMIT_BACKOFF_BASE_SECONDS = 1.5

            def _rate_limit_jitter(self) -> float:
                return 0.25

        endpoint = _BackoffSkipEndpoint(
            {1: []},
            responses={
                0: [
                    httpx.Response(
                        429,
                        json={"error": "rate"},
                        request=httpx.Request("GET", "https://fake.api/path"),
                    ),
                    _resp(200, body={"value": [{"id": 0}]}),
                ]
            },
        )
        container = ArrowRecordContainer(schema=None)
        endpoint._paginate_skip_into(
            "/api/test", {}, container, page_size=1, max_concurrent=1
        )

        assert endpoint.sleep_calls == [1.75]
        assert container.to_polars().to_dicts() == [{"id": 0}]

    def test_rate_limit_retry_exhaustion_raises_final_429(self) -> None:
        class _ShortRetrySkipEndpoint(_SkipEndpoint):
            _RATE_LIMIT_MAX_RETRIES = 2

        endpoint = _ShortRetrySkipEndpoint(
            {},
            responses={
                0: [
                    httpx.Response(
                        429,
                        json={"error": "rate"},
                        request=httpx.Request("GET", "https://fake.api/path"),
                    ),
                    httpx.Response(
                        429,
                        json={"error": "rate"},
                        request=httpx.Request("GET", "https://fake.api/path"),
                    ),
                    httpx.Response(
                        429,
                        json={"error": "rate"},
                        request=httpx.Request("GET", "https://fake.api/path"),
                    ),
                ]
            },
        )
        container = ArrowRecordContainer(schema=None)

        with pytest.raises(httpx.HTTPStatusError, match="429"):
            endpoint._paginate_skip_into(
                "/api/test", {}, container, page_size=1, max_concurrent=1
            )

        assert len(endpoint.calls) == 3
        assert endpoint.sleep_calls == [0.0, 0.0]

    def test_backoff_delay_uses_exponential_attempt_and_jitter(self) -> None:
        class _BackoffSkipEndpoint(_SkipEndpoint):
            _RATE_LIMIT_BACKOFF_BASE_SECONDS = 1.5

            def _rate_limit_jitter(self) -> float:
                return 0.25

        endpoint = _BackoffSkipEndpoint({})

        assert endpoint._backoff_delay(0) == 1.75
        assert endpoint._backoff_delay(2) == 6.25


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
