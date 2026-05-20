"""Tests for RemediationEndpoint request construction."""

from __future__ import annotations

from mde_client.endpoints.machines import MachineReferencesResults
from mde_client.endpoints.remediations import (
    RemediationEndpoint,
    RemediationQuery,
    RemediationResults,
)


class TestGetAll:
    def test_path_and_type(self, make_endpoint) -> None:
        result = make_endpoint(RemediationEndpoint).get_all()
        assert isinstance(result, RemediationResults)
        assert result._path == "/api/remediationtasks"

    def test_query_filter(self, make_endpoint) -> None:
        result = make_endpoint(RemediationEndpoint).get_all(
            RemediationQuery(createdon=None, status="Active")
        )
        assert "status eq 'Active'" in result._params["$filter"]


class TestGet:
    def test_path(self, make_endpoint) -> None:
        result = make_endpoint(RemediationEndpoint).get("rem-1")
        assert result._path == "/api/remediationtasks/rem-1"


class TestMachineReferences:
    def test_path_and_type(self, make_endpoint) -> None:
        result = make_endpoint(RemediationEndpoint).machinereferences("rem-1")
        assert isinstance(result, MachineReferencesResults)
        assert result._path == "/api/remediationtasks/rem-1/machinereferences"
