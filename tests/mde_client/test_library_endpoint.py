"""Tests for library file upload payload and endpoint request construction."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx

from mde_client.endpoints.library import (
    LibraryFilesEndpoint,
    LibraryFilesUpdatePayload,
)


def _fake_response(method: str, path: str, body: dict[str, Any]) -> httpx.Response:
    return httpx.Response(
        200,
        json=body,
        request=httpx.Request(method, f"https://fake.api{path}"),
    )


class _FakeLibraryEndpoint(LibraryFilesEndpoint):
    def __init__(self, body: dict[str, Any]) -> None:
        http_client = MagicMock(spec=httpx.Client)
        http_client.base_url = "https://fake.api"
        auth = MagicMock()
        auth.token = "fake-token"
        super().__init__(http_client, auth)
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self._body = body

    async def _arequest(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        self.calls.append((method, path, kwargs))
        return _fake_response(method, path, self._body)


class TestLibraryFileUploads:
    def test_upload_payload_serializes_for_request_body(self) -> None:
        payload = LibraryFilesUpdatePayload(
            file_name="contain.ps1",
            file_content=b"Write-Host 'Contain device'",
            description="Example script",
            parameters_description="TenantId",
            override_if_exists=True,
        )

        assert payload.model_dump() == {
            "file_name": "contain.ps1",
            "file_content": b"Write-Host 'Contain device'",
            "content_type": "application/octet-stream",
            "description": "Example script",
            "parameters_description": "TenantId",
            "override_if_exists": True,
            "has_parameters": None,
        }

    def test_upload_returns_true_on_success(self) -> None:
        endpoint = _FakeLibraryEndpoint({})
        payload = LibraryFilesUpdatePayload(
            file_name="contain.ps1",
            file_content=b"Write-Host 'Contain device'",
            description="Example script",
        )

        result = endpoint.upload(payload)

        assert result is True

    def test_upload_posts_json_body_once(self) -> None:
        endpoint = _FakeLibraryEndpoint({})
        payload = LibraryFilesUpdatePayload(
            file_name="contain.ps1",
            file_content=b"Write-Host 'Contain device'",
            description="Example script",
            parameters_description="TenantId",
            override_if_exists=True,
        )

        result = endpoint.upload(payload)

        assert result is True
        assert len(endpoint.calls) == 1
        assert endpoint.calls[0][0] == "POST"
        assert endpoint.calls[0][1] == "/api/libraryfiles"
        assert endpoint.calls[0][2]["json"] == payload.model_dump()
