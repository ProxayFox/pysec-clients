"""Tests for RecommendationsEndpoint request construction."""

from __future__ import annotations

from mde_client.endpoints.machines import MachineReferencesResults
from mde_client.endpoints.misc import PublicProductDTOResults
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
        assert isinstance(result, PublicProductDTOResults)
        assert result._path == "/api/recommendations/rec-1/software"

    def test_materializes_product_tags(
        self, make_endpoint, fake_response, monkeypatch
    ) -> None:
        endpoint = make_endpoint(RecommendationsEndpoint)
        result = endpoint.software("rec-1")
        result._params["$top"] = "1"
        product = {
            "id": "product-1",
            "name": "Contoso App",
            "vendor": "Contoso",
            "weaknesses": 2,
            "publicExploit": False,
            "activeAlert": False,
            "exposedMachines": 3,
            "installedMachines": 10,
            "impactScore": 4.5,
            "isNormalized": True,
            "category": "Application",
            "tags": ["critical", "internet-facing"],
        }

        def fake_request(method: str, path: str, **kwargs):
            return fake_response(method, path, {"value": [product]})

        monkeypatch.setattr(endpoint, "_request", fake_request)

        assert result.to_dicts() == [product]


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
