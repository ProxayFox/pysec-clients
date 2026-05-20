"""Tests for IncidentsEndpoint request construction."""

from __future__ import annotations

from mde_client.endpoints.incidents import IncidentResults, IncidentsEndpoint


class TestIncidentsGetAll:
    def test_returns_incident_results(self, make_endpoint) -> None:
        result = make_endpoint(IncidentsEndpoint).get_all()
        assert isinstance(result, IncidentResults)

    def test_path_is_incidents_root(self, make_endpoint) -> None:
        result = make_endpoint(IncidentsEndpoint).get_all()
        assert result._path == "/api/incidents"

    def test_empty_params(self, make_endpoint) -> None:
        result = make_endpoint(IncidentsEndpoint).get_all()
        assert result._params == {}

    def test_not_single(self, make_endpoint) -> None:
        result = make_endpoint(IncidentsEndpoint).get_all()
        assert result._single is False


class TestIncidentsGet:
    def test_returns_incident_results(self, make_endpoint) -> None:
        result = make_endpoint(IncidentsEndpoint).get("inc-1")
        assert isinstance(result, IncidentResults)

    def test_path_includes_id(self, make_endpoint) -> None:
        result = make_endpoint(IncidentsEndpoint).get("inc-1")
        assert result._path == "/api/incidents/inc-1"

    def test_single_is_true(self, make_endpoint) -> None:
        result = make_endpoint(IncidentsEndpoint).get("inc-1")
        assert result._single is True
