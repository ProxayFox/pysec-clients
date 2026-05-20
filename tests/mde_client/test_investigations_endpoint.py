"""Tests for InvestigationsEndpoint request construction and query model."""

from __future__ import annotations

from mde_client.endpoints.investigations import (
    InvestigationQuery,
    InvestigationResults,
    InvestigationsEndpoint,
)
from mde_client.endpoints.machines import MachinesEndpoint
from mde_client.models.action_payloads import (
    InitiateInvestigationPayload,
    StartInvestigationPayload,
)


class TestGetAll:
    def test_returns_results(self, make_endpoint) -> None:
        result = make_endpoint(InvestigationsEndpoint).get_all()
        assert isinstance(result, InvestigationResults)
        assert result._path == "/api/investigations"
        assert result._single is False

    def test_query_filter(self, make_endpoint) -> None:
        result = make_endpoint(InvestigationsEndpoint).get_all(
            InvestigationQuery(state="Running")
        )
        assert "state eq 'Running'" in result._params["$filter"]


class TestGet:
    def test_path_and_single(self, make_endpoint) -> None:
        result = make_endpoint(InvestigationsEndpoint).get("inv-1")
        assert result._path == "/api/investigations/inv-1"
        assert result._single is True


class TestDelegatedActions:
    def test_start_investigation_delegates_to_machines_endpoint(
        self, make_endpoint, monkeypatch
    ) -> None:
        captured: dict[str, object] = {}

        def fake_start(self: MachinesEndpoint, device_id: str, payload):
            captured["device_id"] = device_id
            captured["payload"] = payload
            return "sentinel"

        monkeypatch.setattr(MachinesEndpoint, "_startInvestigation", fake_start)
        ep = make_endpoint(InvestigationsEndpoint)
        result = ep.startInvestigation(
            "device-1", StartInvestigationPayload(Comment="go")
        )
        assert result == "sentinel"
        assert captured == {
            "device_id": "device-1",
            "payload": StartInvestigationPayload(Comment="go"),
        }

    def test_initiate_investigation_delegates(self, make_endpoint, monkeypatch) -> None:
        captured: dict[str, object] = {}

        def fake_initiate(self: MachinesEndpoint, machine_id: str, payload):
            captured["machine_id"] = machine_id
            captured["payload"] = payload
            return "sentinel"

        monkeypatch.setattr(MachinesEndpoint, "_initiateInvestigation", fake_initiate)
        ep = make_endpoint(InvestigationsEndpoint)
        result = ep.initiateInvestigation(
            "m-1", InitiateInvestigationPayload(Comment="please")
        )
        assert result == "sentinel"
        assert captured["machine_id"] == "m-1"
