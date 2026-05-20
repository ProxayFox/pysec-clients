"""Shared fixtures for new ``tests/mde_client/`` unit tests.

These fixtures are opt-in: existing test modules build their own
``_make_endpoint()`` and ``_fake_response()`` helpers and continue to do so.
New tests added during the coverage push use the helpers below.

The patterns mirror those established by
``test_machines_endpoint.py``, ``test_alerts_endpoint.py``, and
``test_machine_results.py``:

- ``fake_http_client`` / ``fake_auth`` — minimal ``MagicMock`` stand-ins.
- ``make_endpoint`` — factory that wires either fixture into any
  ``BaseEndpoint`` subclass.
- ``fake_response`` — builds a real ``httpx.Response`` so that
  ``raise_for_status`` / ``.json()`` behave authentically.
- ``recording_endpoint`` — factory returning a subclass whose
  ``_arequest`` records ``(method, path, kwargs)`` and pops from a queue
  of fake responses. Mirrors the ``_FakeAlertsEndpoint`` pattern.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

from mde_client.endpoints.base import BaseEndpoint

FAKE_BASE_URL = "https://fake.api"
FAKE_TOKEN = "fake-token"


@pytest.fixture
def fake_http_client() -> MagicMock:
    """Return a ``MagicMock(spec=httpx.Client)`` with a stable ``base_url``."""
    client = MagicMock(spec=httpx.Client)
    client.base_url = FAKE_BASE_URL
    return client


@pytest.fixture
def fake_auth() -> MagicMock:
    """Return a ``MagicMock`` whose ``token`` attribute is a fixed string."""
    auth = MagicMock()
    auth.token = FAKE_TOKEN
    return auth


@pytest.fixture
def make_endpoint(
    fake_http_client: MagicMock, fake_auth: MagicMock
) -> Callable[..., BaseEndpoint]:
    """Return a factory that builds any ``BaseEndpoint`` subclass with shared mocks."""

    def _factory[T: BaseEndpoint](endpoint_cls: type[T]) -> T:
        return endpoint_cls(fake_http_client, fake_auth)

    return _factory


def _build_fake_response(
    method: str,
    path: str,
    json_body: Any = None,
    *,
    status: int = 200,
    headers: Mapping[str, str] | None = None,
) -> httpx.Response:
    """Build an ``httpx.Response`` bound to a synthetic request."""
    url = path if path.startswith("http") else f"{FAKE_BASE_URL}{path}"
    request = httpx.Request(method, url)
    return httpx.Response(
        status,
        json=json_body if json_body is not None else {},
        headers=dict(headers) if headers else None,
        request=request,
    )


@pytest.fixture
def fake_response() -> Callable[..., httpx.Response]:
    """Return a builder for ``httpx.Response`` objects with sensible defaults."""
    return _build_fake_response


def _make_recording_endpoint(
    endpoint_cls: type[BaseEndpoint],
    responses: list[Any] | None = None,
    *,
    default_body: Any = None,
) -> BaseEndpoint:
    """Instantiate *endpoint_cls* with mocks and a recording ``_arequest``.

    ``responses`` is a FIFO queue of pre-built ``httpx.Response`` objects, or
    JSON-serialisable dicts that will be wrapped into 200 responses.  When the
    queue is empty (or omitted) every call returns a 200 response carrying
    ``default_body`` (or ``{}``).

    Each call is appended to the endpoint's ``calls`` list as
    ``(method, path, kwargs)`` — matching the pattern in
    ``test_alerts_endpoint.py``.
    """

    http_client = MagicMock(spec=httpx.Client)
    http_client.base_url = FAKE_BASE_URL
    auth = MagicMock()
    auth.token = FAKE_TOKEN
    queue = list(responses or [])

    base_cls: Any = endpoint_cls

    class _Recording(base_cls):
        def __init__(self) -> None:
            super().__init__(http_client, auth)
            self.calls: list[tuple[str, str, dict[str, Any]]] = []

        async def _arequest(
            self, method: str, path: str, **kwargs: Any
        ) -> httpx.Response:
            self.calls.append((method, path, kwargs))
            if queue:
                next_item = queue.pop(0)
                if isinstance(next_item, httpx.Response):
                    return next_item
                return _build_fake_response(method, path, next_item)
            return _build_fake_response(method, path, default_body)

    return _Recording()


@pytest.fixture
def recording_endpoint() -> Callable[..., BaseEndpoint]:
    """Return a factory for endpoint instances whose calls are recorded.

    Usage::

        ep = recording_endpoint(AlertsEndpoint, [{"id": "a"}])
        ep.someAction(...)
        assert ep.calls[0][1] == "/api/alerts/..."
    """
    return _make_recording_endpoint
