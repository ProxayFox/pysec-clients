"""Tests for MachinesEndpoint request construction and result types.

Verifies that each endpoint method builds the correct API path, query
parameters, and result type without issuing any HTTP requests.  These
tests complement ``test_machine_results.py`` (which covers lazy fetching,
pagination, and caching) by focusing on the per-method contract.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import httpx
import pytest

from mde_client.endpoints.machines import (
    AlertsResults,
    LogonUserResults,
    MachineResults,
    MachinesEndpoint,
    MachinesQuery,
    PublicProductFixResults,
    RecommendationResults,
    SoftwareResults,
    VulnerabilityResults,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

MACHINE_ID = "abc123-test-machine"


def _make_endpoint() -> MachinesEndpoint:
    """Build a MachinesEndpoint backed by mocks (no real HTTP/auth)."""
    http_client = MagicMock(spec=httpx.Client)
    http_client.base_url = "https://fake.api"
    auth = MagicMock()
    auth.token = "fake-token"
    return MachinesEndpoint(http_client, auth)


# ------------------------------------------------------------------
# get_all — path, params, return type
# ------------------------------------------------------------------


class TestGetAll:
    def test_returns_machine_results(self) -> None:
        result = _make_endpoint().get_all()
        assert isinstance(result, MachineResults)

    def test_path_is_machines_root(self) -> None:
        result = _make_endpoint().get_all()
        assert result._path == "/api/machines"

    def test_no_query_produces_empty_params(self) -> None:
        result = _make_endpoint().get_all()
        assert result._params == {}

    def test_query_top_forwarded(self) -> None:
        result = _make_endpoint().get_all(MachinesQuery(top=512))
        assert result._params["$top"] == "512"

    def test_query_health_status_filter(self) -> None:
        result = _make_endpoint().get_all(MachinesQuery(healthStatus="Active"))
        assert "healthStatus eq 'Active'" in result._params.get("$filter", "")

    def test_not_single(self) -> None:
        result = _make_endpoint().get_all()
        assert not result._single


# ------------------------------------------------------------------
# get — single item by ID
# ------------------------------------------------------------------


class TestGet:
    def test_returns_machine_results(self) -> None:
        result = _make_endpoint().get(MACHINE_ID)
        assert isinstance(result, MachineResults)

    def test_path_includes_id(self) -> None:
        result = _make_endpoint().get(MACHINE_ID)
        assert result._path == f"/api/machines/{MACHINE_ID}"

    def test_single_is_true(self) -> None:
        result = _make_endpoint().get(MACHINE_ID)
        assert result._single is True

    def test_none_id_is_type_error(self) -> None:
        """Passing None is caught by the type checker; no runtime guard exists."""
        result = _make_endpoint().get(None)  # type: ignore[arg-type]  # ty: ignore[invalid-argument-type]
        assert "/None" in result._path


# ------------------------------------------------------------------
# Sub-resource endpoints — path and return type
# ------------------------------------------------------------------


class TestSubResources:
    @pytest.mark.parametrize(
        ("method", "suffix", "result_type"),
        [
            ("logonusers", "logonusers", LogonUserResults),
            ("alerts", "alerts", AlertsResults),
            ("software", "software", SoftwareResults),
            ("vulnerabilities", "vulnerabilities", VulnerabilityResults),
            ("recommendations", "recommendations", RecommendationResults),
            ("getmissingkbs", "getmissingkbs", PublicProductFixResults),
        ],
    )
    def test_path_and_type(self, method: str, suffix: str, result_type: type) -> None:
        result = getattr(_make_endpoint(), method)(MACHINE_ID)
        assert result._path == f"/api/machines/{MACHINE_ID}/{suffix}"
        assert isinstance(result, result_type)

    @pytest.mark.parametrize(
        "method",
        [
            "logonusers",
            "alerts",
            "software",
            "vulnerabilities",
            "recommendations",
            "getmissingkbs",
        ],
    )
    def test_not_single(self, method: str) -> None:
        result = getattr(_make_endpoint(), method)(MACHINE_ID)
        assert not result._single


# ------------------------------------------------------------------
# findbyip — timestamp formatting
# ------------------------------------------------------------------


class TestFindByIP:
    def test_returns_machine_results(self) -> None:
        ts = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = _make_endpoint().findbyip("10.0.0.1", ts)
        assert isinstance(result, MachineResults)

    def test_path_contains_ip_and_utc_z(self) -> None:
        ts = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        result = _make_endpoint().findbyip("10.0.0.1", ts)
        assert "ip='10.0.0.1'" in result._path
        assert "2025-01-15T12:00:00Z" in result._path

    def test_naive_timestamp_treated_as_utc(self) -> None:
        ts = datetime(2025, 6, 1, 8, 30, 0)
        result = _make_endpoint().findbyip("192.168.1.1", ts)
        assert "2025-06-01T08:30:00Z" in result._path

    def test_non_utc_converted_to_utc(self) -> None:
        eastern = timezone(timedelta(hours=-5))
        ts = datetime(2025, 6, 1, 8, 0, 0, tzinfo=eastern)  # 13:00 UTC
        result = _make_endpoint().findbyip("10.0.0.1", ts)
        assert "2025-06-01T13:00:00Z" in result._path


# ------------------------------------------------------------------
# tag — path and params
# ------------------------------------------------------------------


class TestTag:
    def test_returns_machine_results(self) -> None:
        result = _make_endpoint().tag("my-tag")
        assert isinstance(result, MachineResults)

    def test_path_is_findbytag(self) -> None:
        result = _make_endpoint().tag("my-tag")
        assert result._path == "/api/machines/findbytag"

    def test_tag_in_params(self) -> None:
        result = _make_endpoint().tag("my-tag")
        assert result._params["tag"] == "my-tag"

    def test_starts_with_false_by_default(self) -> None:
        result = _make_endpoint().tag("my-tag")
        assert result._params["useStartsWithFilter"] == "false"

    def test_starts_with_true(self) -> None:
        result = _make_endpoint().tag("my-tag", useStartsWithFilter=True)
        assert result._params["useStartsWithFilter"] == "true"


# ------------------------------------------------------------------
# MachinesQuery — OData filter construction
# ------------------------------------------------------------------


class TestMachinesQuery:
    def test_defaults_include_page_size(self) -> None:
        params = MachinesQuery().to_odata_filters
        assert "pageSize" in params

    def test_top_produces_dollar_top(self) -> None:
        params = MachinesQuery(top=100).to_odata_filters
        assert params["$top"] == "100"

    def test_health_status_filter(self) -> None:
        params = MachinesQuery(healthStatus="Active").to_odata_filters
        assert "healthStatus eq 'Active'" in params["$filter"]

    def test_id_list_produces_in_clause(self) -> None:
        params = MachinesQuery(id=["id1", "id2"]).to_odata_filters
        assert "id in ('id1', 'id2')" in params["$filter"]

    def test_multiple_filters_joined_with_and(self) -> None:
        params = MachinesQuery(
            healthStatus="Active", osPlatform="Windows10"
        ).to_odata_filters
        assert " and " in params["$filter"]

    def test_skip_produces_dollar_skip(self) -> None:
        params = MachinesQuery(skip=50).to_odata_filters
        assert params["$skip"] == "50"
