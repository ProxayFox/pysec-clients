# `client.investigations`

Inspect and start investigations.

## Property

`client.investigations`

## Methods

- `get_all(query: InvestigationQuery | None = None) -> InvestigationResults`: list investigations.
- `get(id: str) -> InvestigationResults`: fetch one investigation by ID.
- `startInvestigation(deviceId: str, payload: StartInvestigationPayload) -> InvestigationResults`: start an investigation for a device.
- `initiateInvestigation(machine_id: str, payload: InitiateInvestigationPayload) -> InvestigationResults`: initiate an investigation for a machine.

## Notes

- `startInvestigation()` is exposed from the investigations property but delegates to a machine-scoped action under the hood.
- `initiateInvestigation()` targets an undocumented machine-scoped investigation path.
- Read methods use the standard lazy wrapper behavior.

## API

::: mde_client.endpoints.investigations
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
