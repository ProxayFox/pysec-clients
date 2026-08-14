"""Tests for the top-level MDEClient lifecycle and endpoint wiring."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import msal
import pytest
from mde_client import MDEClient
from mde_client.auth import MSALAuth
from mde_client.endpoints import (
    AdvancedHuntingQueriesEndpoint,
    AlertsEndpoint,
    AuthenticatedDefinitionsEndpoint,
    BaseEndpoint,
    BaselineConfigurationEndpoint,
    BrowserExtensionEndpoint,
    CertificateInventoryEndpoint,
    DataExportSettingsEndpoint,
    DeviceAuthenticatedAgentsEndpoint,
    DeviceAVHealthEndpoint,
    DeviceGroupsEndpoint,
    DomainEndpoint,
    FileEndpoint,
    FirmwareEndpoint,
    IndicatorsEndpoint,
    InvestigationsEndpoint,
    IPEndpoint,
    LibraryFilesEndpoint,
    MachineActionsEndpoint,
    MachinesEndpoint,
    RecommendationsEndpoint,
    RemediationEndpoint,
    ScoreEndpoint,
    SoftwareEndpoint,
    UserEndpoint,
    VulnerabilityEndpoint,
)


@pytest.fixture
def mocked_msal(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    fake_app = MagicMock()
    factory = MagicMock(return_value=fake_app)
    monkeypatch.setattr(msal, "ConfidentialClientApplication", factory)
    return factory


@pytest.fixture
def fake_http() -> httpx.Client:
    client = MagicMock(spec=httpx.Client)
    client.base_url = "https://fake.api"
    return client


class TestInit:
    def test_uses_injected_http_client(
        self, mocked_msal: MagicMock, fake_http: httpx.Client
    ) -> None:
        client = MDEClient("t", "c", "s", http_client=fake_http)
        assert client._http is fake_http

    def test_constructs_default_http_client(self, mocked_msal: MagicMock) -> None:
        client = MDEClient("t", "c", "s")
        try:
            assert isinstance(client._http, httpx.Client)
            assert str(client._http.base_url).startswith(
                "https://api.securitycenter.microsoft.com"
            )
        finally:
            client.close()

    def test_respects_custom_base_url(self, mocked_msal: MagicMock) -> None:
        client = MDEClient("t", "c", "s", base_url="https://custom.example")
        try:
            assert str(client._http.base_url).startswith("https://custom.example")
        finally:
            client.close()

    def test_builds_msal_auth(
        self, mocked_msal: MagicMock, fake_http: httpx.Client
    ) -> None:
        client = MDEClient("tenant", "cid", "sec", http_client=fake_http)
        assert isinstance(client._auth, MSALAuth)
        # MSAL ConfidentialClientApplication was invoked with our credentials.
        kwargs = mocked_msal.call_args.kwargs
        assert mocked_msal.call_args.args[0] == "cid"
        assert "tenant" in kwargs["authority"]
        assert kwargs["client_credential"] == "sec"


class TestLifecycle:
    def test_close_invokes_http_close(
        self, mocked_msal: MagicMock, fake_http: MagicMock
    ) -> None:
        client = MDEClient("t", "c", "s", http_client=fake_http)
        client.close()
        fake_http.close.assert_called_once_with()

    def test_context_manager_closes_on_exit(
        self, mocked_msal: MagicMock, fake_http: MagicMock
    ) -> None:
        with MDEClient("t", "c", "s", http_client=fake_http) as client:
            assert client._http is fake_http
        fake_http.close.assert_called_once_with()


@pytest.mark.parametrize(
    "attr,cls",
    [
        ("misc", BaseEndpoint),
        ("advanced_queries", AdvancedHuntingQueriesEndpoint),
        ("alerts", AlertsEndpoint),
        ("authenticated_definitions", AuthenticatedDefinitionsEndpoint),
        ("authenticated_agents", DeviceAuthenticatedAgentsEndpoint),
        ("browser_extension", BrowserExtensionEndpoint),
        ("certificate_inventory", CertificateInventoryEndpoint),
        ("device_av_health", DeviceAVHealthEndpoint),
        ("device_groups", DeviceGroupsEndpoint),
        ("domain", DomainEndpoint),
        ("firmware", FirmwareEndpoint),
        ("files", FileEndpoint),
        ("indicators", IndicatorsEndpoint),
        ("investigations", InvestigationsEndpoint),
        ("ips", IPEndpoint),
        ("library", LibraryFilesEndpoint),
        ("machine_actions", MachineActionsEndpoint),
        ("machines", MachinesEndpoint),
        ("recommendations", RecommendationsEndpoint),
        ("remediations", RemediationEndpoint),
        ("score", ScoreEndpoint),
        ("baseline_configurations", BaselineConfigurationEndpoint),
        ("settings", DataExportSettingsEndpoint),
        ("software", SoftwareEndpoint),
        ("user", UserEndpoint),
        ("vulnerabilities", VulnerabilityEndpoint),
    ],
)
def test_endpoint_properties_return_typed_instances(
    mocked_msal: MagicMock,
    fake_http: httpx.Client,
    attr: str,
    cls: type,
) -> None:
    client = MDEClient("t", "c", "s", http_client=fake_http)
    endpoint = getattr(client, attr)
    assert isinstance(endpoint, cls)
    # Endpoints must share the client's http + auth instances.
    assert endpoint._http is client._http
    assert endpoint._auth is client._auth
