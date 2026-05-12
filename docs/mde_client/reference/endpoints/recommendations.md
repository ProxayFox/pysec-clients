# `client.recommendations`

Access recommendation records and recommendation-related entities.

## Property

`client.recommendations`

## Methods

- `get_all(query: RecommendationQuery | None = None) -> RecommendationResults`: list recommendations.
- `get(id: str) -> RecommendationResults`: fetch one recommendation by ID.
- `software(id: str) -> ProductDTOResults`: fetch software related to a recommendation.
- `machineReferences(id: str) -> MachineReferencesResults`: fetch machine references for a recommendation.
- `vulnerabilities(id: str) -> VulnerabilityDTOResults`: fetch vulnerabilities related to a recommendation.

## Notes

- The method name `machineReferences` uses camelCase because it follows the current package surface.
