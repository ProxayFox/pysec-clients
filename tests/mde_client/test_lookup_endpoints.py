"""Tests for DomainEndpoint, FileEndpoint, IPEndpoint request construction."""

from __future__ import annotations

from mde_client.endpoints.alerts import AlertsResults
from mde_client.endpoints.domain import DomainEndpoint, DomainStatsResults
from mde_client.endpoints.files import FileEndpoint, FileResults, FileStatsResults
from mde_client.endpoints.ips import IPEndpoint, InOrgIPStatsResults
from mde_client.endpoints.machines import MachineResults


class TestDomain:
    def test_alerts(self, make_endpoint) -> None:
        result = make_endpoint(DomainEndpoint).alerts("example.com")
        assert isinstance(result, AlertsResults)
        assert result._path == "/api/domains/example.com/alerts"

    def test_machines(self, make_endpoint) -> None:
        result = make_endpoint(DomainEndpoint).machines("example.com")
        assert isinstance(result, MachineResults)
        assert result._path == "/api/domains/example.com/machines"

    def test_stats(self, make_endpoint) -> None:
        result = make_endpoint(DomainEndpoint).stats("example.com")
        assert isinstance(result, DomainStatsResults)
        assert result._path == "/api/domains/example.com/stats"


class TestFiles:
    def test_get(self, make_endpoint) -> None:
        result = make_endpoint(FileEndpoint).get("abc123")
        assert isinstance(result, FileResults)
        assert result._path == "/api/files/abc123"

    def test_alerts(self, make_endpoint) -> None:
        result = make_endpoint(FileEndpoint).alerts("abc123")
        assert isinstance(result, AlertsResults)
        assert result._path == "/api/files/abc123/alerts"

    def test_machines(self, make_endpoint) -> None:
        result = make_endpoint(FileEndpoint).machines("abc123")
        assert isinstance(result, MachineResults)
        assert result._path == "/api/files/abc123/machines"

    def test_stats(self, make_endpoint) -> None:
        result = make_endpoint(FileEndpoint).stats("abc123")
        assert isinstance(result, FileStatsResults)
        assert result._path == "/api/files/abc123/stats"


class TestIps:
    def test_alerts(self, make_endpoint) -> None:
        result = make_endpoint(IPEndpoint).alerts("10.0.0.1")
        assert isinstance(result, AlertsResults)
        assert result._path == "/api/ips/10.0.0.1/alerts"

    def test_stats(self, make_endpoint) -> None:
        result = make_endpoint(IPEndpoint).stats("10.0.0.1")
        assert isinstance(result, InOrgIPStatsResults)
        assert result._path == "/api/ips/10.0.0.1/stats"
