"""Tests for MSALAuth token acquisition and error handling."""

from __future__ import annotations

from unittest.mock import MagicMock

import msal
import pytest

from mde_client.auth import AuthenticationError, MSALAuth


@pytest.fixture
def fake_app(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    app = MagicMock()
    monkeypatch.setattr(
        msal, "ConfidentialClientApplication", MagicMock(return_value=app)
    )
    return app


class TestTokenAcquisition:
    def test_returns_access_token(self, fake_app: MagicMock) -> None:
        fake_app.acquire_token_for_client.return_value = {"access_token": "tok-123"}
        auth = MSALAuth("tenant", "cid", "sec")
        assert auth.token == "tok-123"
        fake_app.acquire_token_for_client.assert_called_once_with(
            scopes=MSALAuth._SCOPES
        )

    def test_msal_none_raises(self, fake_app: MagicMock) -> None:
        fake_app.acquire_token_for_client.return_value = None
        auth = MSALAuth("tenant", "cid", "sec")
        with pytest.raises(AuthenticationError, match="MSAL returned None"):
            _ = auth.token

    def test_error_payload_raises_with_details(self, fake_app: MagicMock) -> None:
        fake_app.acquire_token_for_client.return_value = {
            "error": "invalid_client",
            "error_description": "bad secret",
        }
        auth = MSALAuth("tenant", "cid", "sec")
        with pytest.raises(AuthenticationError, match="invalid_client: bad secret"):
            _ = auth.token

    def test_error_payload_falls_back_to_defaults(self, fake_app: MagicMock) -> None:
        fake_app.acquire_token_for_client.return_value = {"foo": "bar"}
        auth = MSALAuth("tenant", "cid", "sec")
        with pytest.raises(
            AuthenticationError, match="unknown_error: No description provided."
        ):
            _ = auth.token


class TestConstruction:
    def test_uses_provided_token_cache(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: dict = {}

        def _factory(*args, **kwargs):
            captured.update(kwargs)
            return MagicMock()

        monkeypatch.setattr(msal, "ConfidentialClientApplication", _factory)

        cache = msal.TokenCache()
        MSALAuth("t", "c", "s", token_cache=cache)
        assert captured["token_cache"] is cache

    def test_defaults_to_in_memory_token_cache(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: dict = {}

        def _factory(*args, **kwargs):
            captured.update(kwargs)
            return MagicMock()

        monkeypatch.setattr(msal, "ConfidentialClientApplication", _factory)

        MSALAuth("t", "c", "s")
        assert isinstance(captured["token_cache"], msal.TokenCache)
