# `client.investigations`

Inspect and start investigations.

## Property

`client.investigations`

## Methods

- `get_all(query: InvestigationQuery | None = None) -> InvestigationResults`: list investigations.
- `get(id: str) -> InvestigationResults`: fetch one investigation by ID.
- `startInvestigation(deviceId: str, payload: StartInvestigationPayload) -> InvestigationResults`: start an investigation for a device.

## Notes

- `startInvestigation()` is exposed from the investigations property but delegates to a machine-scoped action under the hood.
- Read methods use the standard lazy wrapper behavior.
