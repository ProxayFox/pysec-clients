"""Tests for generated investigation support models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mde_client.models.enums import INVESTIGATION_STATE
from mde_client.models.action_payloads import StartInvestigationPayload


class TestInvestigationState:
    def test_contains_known_members(self) -> None:
        expected = {
            "Unknown",
            "Terminated",
            "SuccessfullyRemediated",
            "Benign",
            "Failed",
            "PartiallyRemediated",
            "Running",
            "PendingApproval",
            "PendingResource",
            "Queued",
            "InnerFailure",
        }
        assert expected <= set(INVESTIGATION_STATE.__args__)

    def test_includes_contract_only_member_disabled(self) -> None:
        assert "Disabled" in INVESTIGATION_STATE.__args__


class TestStartInvestigationPayload:
    def test_comment_required(self) -> None:
        with pytest.raises(ValidationError):
            StartInvestigationPayload.model_validate({})

    def test_comment_only(self) -> None:
        p = StartInvestigationPayload.model_validate({"Comment": "test"})
        assert p.Comment == "test"
        assert p.ExternalId is None
        assert p.RequestSource is None
        assert p.Title is None

    def test_all_fields(self) -> None:
        p = StartInvestigationPayload.model_validate(
            {
                "Comment": "investigate this",
                "ExternalId": "ext-123",
                "RequestSource": "PublicApi",
                "Title": "My Investigation",
            }
        )
        assert p.Comment == "investigate this"
        assert p.ExternalId == "ext-123"
        assert p.RequestSource == "PublicApi"
        assert p.Title == "My Investigation"

    def test_no_machine_id_field(self) -> None:
        assert "machineId" not in StartInvestigationPayload.model_fields

    def test_optional_despite_nullable_false(self) -> None:
        """RequestSource is Nullable=false in XML but has OptionalParameter."""
        p = StartInvestigationPayload.model_validate({"Comment": "test"})
        assert p.RequestSource is None

    def test_serialization_excludes_none(self) -> None:
        p = StartInvestigationPayload(Comment="test")
        dumped = p.model_dump(exclude_none=True)
        assert dumped == {"Comment": "test"}
