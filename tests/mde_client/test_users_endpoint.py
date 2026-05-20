"""Tests for UserEndpoint request construction."""

from __future__ import annotations

from mde_client.endpoints.alerts import AlertsResults
from mde_client.endpoints.machines import MachineResults
from mde_client.endpoints.users import UserEndpoint


class TestUserAlerts:
    def test_path_and_type(self, make_endpoint) -> None:
        result = make_endpoint(UserEndpoint).alerts("user-1")
        assert isinstance(result, AlertsResults)
        assert result._path == "/api/users/user-1/alerts"


class TestUserMachines:
    def test_path_and_type(self, make_endpoint) -> None:
        result = make_endpoint(UserEndpoint).machines("user-1")
        assert isinstance(result, MachineResults)
        assert result._path == "/api/users/user-1/machines"
