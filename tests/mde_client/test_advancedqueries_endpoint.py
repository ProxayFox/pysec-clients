"""Tests for AdvancedHuntingQueriesEndpoint and result wrapper."""

from __future__ import annotations

from typing import Any

import httpx

from mde_client.endpoints.advancedqueries import (
    AdvancedHuntingQueriesEndpoint,
    AdvancedHuntingQueriesResults,
)


class TestRun:
    def test_returns_results_wrapper(self, make_endpoint) -> None:
        result = make_endpoint(AdvancedHuntingQueriesEndpoint).run("Devices | take 1")
        assert isinstance(result, AdvancedHuntingQueriesResults)

    def test_path_is_advanced_queries_run(self, make_endpoint) -> None:
        result = make_endpoint(AdvancedHuntingQueriesEndpoint).run("Devices | take 1")
        assert result._path == "/api/advancedqueries/run"

    def test_query_stored_on_wrapper(self, make_endpoint) -> None:
        result = make_endpoint(AdvancedHuntingQueriesEndpoint).run("Devices | take 1")
        assert result._query == "Devices | take 1"

    def test_no_http_call_on_construction(
        self, make_endpoint, fake_http_client
    ) -> None:
        _ = make_endpoint(AdvancedHuntingQueriesEndpoint).run("Devices | take 1")
        fake_http_client.request.assert_not_called()


class _RecordingAdvancedHunting(AdvancedHuntingQueriesEndpoint):
    """Captures _request calls and serves a stubbed Results payload."""

    def __init__(self, results_body: list[dict[str, Any]]) -> None:
        from unittest.mock import MagicMock

        http_client = MagicMock(spec=httpx.Client)
        http_client.base_url = "https://fake.api"
        auth = MagicMock()
        auth.token = "fake-token"
        super().__init__(http_client, auth)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self._body = {"Results": results_body, "Schema": []}

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self.calls.append((method, path, kwargs))
        return httpx.Response(
            200,
            json=self._body,
            request=httpx.Request(method, f"https://fake.api{path}"),
        )


class TestFetchSemantics:
    def test_fetched_issues_post_with_json_body(self) -> None:
        endpoint = _RecordingAdvancedHunting([{"DeviceId": "abc"}])
        result = endpoint.run("Devices | take 1")

        _ = result.to_dicts()

        assert len(endpoint.calls) == 1
        method, path, kwargs = endpoint.calls[0]
        assert method == "POST"
        assert path == "/api/advancedqueries/run"
        assert kwargs["json"] == {"Query": "Devices | take 1"}

    def test_refresh_returns_self_and_clears_cache(self) -> None:
        endpoint = _RecordingAdvancedHunting([{"DeviceId": "abc"}])
        result = endpoint.run("Devices | take 1")

        result._container = object()  # type: ignore[assignment]  # ty: ignore[invalid-assignment]
        same = result.refresh()
        assert same is result
        assert result._container is None
