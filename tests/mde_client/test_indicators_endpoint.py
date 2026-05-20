"""Tests for IndicatorsEndpoint request construction and query/payload models."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from mde_client.endpoints.indicators import (
    ImportIndicatorResults,
    IndicatorsEndpoint,
    IndicatorsQuery,
    IndicatorsResults,
    IndicatorsSubmitPayload,
)
from mde_client.models.action_payloads import BatchUpdateIndicatorPayload


def _payload(value: str = "1.2.3.4") -> IndicatorsSubmitPayload:
    return IndicatorsSubmitPayload(
        indicatorValue=value,
        indicatorType="IpAddress",
        action="Alert",
        application=None,
        title="t",
        description="d",
        expirationTime=None,
        severity="Medium",
        recommendedActions=None,
        rbacGroupNames=None,
        educateUrl=None,
        generateAlert=False,
    )


class _Recording(IndicatorsEndpoint):
    def __init__(self, status: int = 204, body: Any = None) -> None:
        http_client = MagicMock(spec=httpx.Client)
        http_client.base_url = "https://fake.api"
        auth = MagicMock()
        auth.token = "fake-token"
        super().__init__(http_client, auth)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self._status = status
        self._body = body

    async def _arequest(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self.calls.append((method, path, kwargs))
        return httpx.Response(
            self._status,
            json=self._body if self._body is not None else None,
            request=httpx.Request(method, f"https://fake.api{path}"),
        )


class TestGetAll:
    def test_returns_results(self, make_endpoint) -> None:
        result = make_endpoint(IndicatorsEndpoint).get_all()
        assert isinstance(result, IndicatorsResults)
        assert result._path == "/api/indicators"
        assert result._single is False

    def test_query_filter(self, make_endpoint) -> None:
        result = make_endpoint(IndicatorsEndpoint).get_all(
            IndicatorsQuery(indicatorType="IpAddress")
        )
        assert "indicatorType eq 'IpAddress'" in result._params["$filter"]


class TestGet:
    def test_path_and_single(self, make_endpoint) -> None:
        result = make_endpoint(IndicatorsEndpoint).get("ind-1")
        assert result._path == "/api/indicators/ind-1"
        assert result._single is True


class TestSubmit:
    def test_post_with_json_body(self, make_endpoint) -> None:
        payload = _payload()
        result = make_endpoint(IndicatorsEndpoint).submit(payload)
        assert result._method == "POST"
        assert result._single is True
        assert result._request_kwargs == {"json": payload.model_dump(exclude_none=True)}


class TestBatchImport:
    def test_single_chunk(self, make_endpoint) -> None:
        payloads = [_payload(f"1.1.1.{i}") for i in range(3)]
        result = make_endpoint(IndicatorsEndpoint).batch_import(payloads)
        assert isinstance(result, ImportIndicatorResults)
        assert result._method == "POST"
        assert result._path == "/api/indicators/import"
        body = result._request_kwargs["json"]
        assert body == {
            "indicators": [p.model_dump(exclude_none=True) for p in payloads]
        }

    def test_chunks_when_over_limit(self, make_endpoint) -> None:
        endpoint = make_endpoint(IndicatorsEndpoint)
        # _BATCH_SIZE_LIMIT is 500 — pick 501 to force exactly 2 chunks.
        payloads = [_payload(f"10.0.0.{i % 254 + 1}") for i in range(501)]
        result = endpoint.batch_import(payloads)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(r, ImportIndicatorResults) for r in result)


class TestBatchUpdate:
    def test_posts_to_batch_update(self) -> None:
        endpoint = _Recording(status=200, body={})
        payload = BatchUpdateIndicatorPayload(Indicators=["a", "b"])
        endpoint.batch_update(payload)
        assert endpoint.calls[0][0] == "POST"
        assert endpoint.calls[0][1] == "/api/indicators/batchUpdate"
        assert endpoint.calls[0][2]["json"] == payload.model_dump(exclude_none=True)


class TestDelete:
    def test_204_returns_true(self) -> None:
        endpoint = _Recording(status=204)
        assert endpoint.delete("ind-1") is True
        assert endpoint.calls[0][0] == "DELETE"
        assert endpoint.calls[0][1] == "/api/indicators/ind-1"

    def test_404_returns_false(self) -> None:
        endpoint = _Recording(status=404, body={"error": "not found"})
        assert endpoint.delete("missing") is False

    def test_500_raises_runtime_error(self) -> None:
        endpoint = _Recording(status=500, body={"error": "boom"})
        with pytest.raises(RuntimeError):
            endpoint.delete("ind-1")


class TestBatchDelete:
    def test_204_returns_true(self) -> None:
        endpoint = _Recording(status=204)
        assert endpoint.batch_delete(["a", "b"]) is True
        assert endpoint.calls[0][0] == "POST"
        assert endpoint.calls[0][1] == "/api/indicators/batchDelete"
        assert endpoint.calls[0][2]["json"] == {"ids": ["a", "b"]}

    def test_400_raises_value_error(self) -> None:
        endpoint = _Recording(status=400, body={"error": "bad"})
        with pytest.raises(ValueError):
            endpoint.batch_delete(["a"])

    def test_404_raises_value_error(self) -> None:
        endpoint = _Recording(status=404, body={"error": "missing"})
        with pytest.raises(ValueError):
            endpoint.batch_delete(["a"])

    def test_chunks_over_limit(self) -> None:
        endpoint = _Recording(status=204)
        ids = [f"id-{i}" for i in range(501)]
        assert endpoint.batch_delete(ids) is True
        assert len(endpoint.calls) == 2
