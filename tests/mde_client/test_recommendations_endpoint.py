"""Tests for RecommendationsEndpoint request construction."""

from __future__ import annotations

from mde_client.endpoints.machines import MachineReferencesResults
from mde_client.endpoints.misc import ProductDTOResults
from mde_client.endpoints.recommendations import (
    RecommendationQuery,
    RecommendationResults,
    RecommendationsEndpoint,
)
from mde_client.endpoints.vulnerabilities import VulnerabilityDTOResults


class TestGetAll:
    def test_path(self, make_endpoint) -> None:
        result = make_endpoint(RecommendationsEndpoint).get_all()
        assert isinstance(result, RecommendationResults)
        assert result._path == "/api/recommendations"

    def test_query_filter(self, make_endpoint) -> None:
        result = make_endpoint(RecommendationsEndpoint).get_all(
            RecommendationQuery(
                id=None,
                productName="windows",
                vendor=None,
                recommendedVersion=None,
                recommendationCategory=None,
                subCategory=None,
                severityScore=None,
                remediationType=None,
                recommendedProgram=None,
                recommendedVendor=None,
                status=None,
            )
        )
        assert "productName eq 'windows'" in result._params["$filter"]


class TestGet:
    def test_path(self, make_endpoint) -> None:
        result = make_endpoint(RecommendationsEndpoint).get("rec-1")
        assert result._path == "/api/recommendations/rec-1"


class TestSoftware:
    def test_path_and_type(self, make_endpoint) -> None:
        result = make_endpoint(RecommendationsEndpoint).software("rec-1")
        assert isinstance(result, ProductDTOResults)
        assert result._path == "/api/recommendations/rec-1/software"


class TestMachineReferences:
    def test_path_and_type(self, make_endpoint) -> None:
        result = make_endpoint(RecommendationsEndpoint).machineReferences("rec-1")
        assert isinstance(result, MachineReferencesResults)
        assert result._path == "/api/recommendations/rec-1/machinereferences"


class TestVulnerabilities:
    def test_path_and_type(self, make_endpoint) -> None:
        result = make_endpoint(RecommendationsEndpoint).vulnerabilities("rec-1")
        assert isinstance(result, VulnerabilityDTOResults)
        assert result._path == "/api/recommendations/rec-1/vulnerabilities"
