# `client.authenticated_definitions`

Manage authenticated scan definitions and their history.

## Property

`client.authenticated_definitions`

## Methods

- `get_all(query: AuthenticatedDefinitionsQuery | None = None) -> AuthenticatedDefinitionsResults`: list authenticated scan definitions.
- `definition_history(ids: str | list[str], query: AuthenticatedScanHistoryQuery | None = None) -> AuthenticatedScanHistoryResults`: fetch scan history by definition ID.
- `session_history(ids: str | list[str], query: AuthenticatedScanHistoryQuery | None = None) -> AuthenticatedScanHistoryResults`: fetch scan history by session ID.
- `add(payload: AuthenticatedDefinitionsAlterPayload) -> AuthenticatedDefinitionsResults`: create a scan definition.
- `update(payload: AuthenticatedDefinitionsAlterPayload) -> AuthenticatedDefinitionsResults`: update a scan definition.
- `delete(ids: str | list[str]) -> AuthenticatedDefinitionsResults`: delete one or more scan definitions.

## Notes

- The history endpoints use POST requests with explicit request bodies even though they read data.
- Mutating methods still return lazy results wrappers rather than booleans.
- `AuthenticatedScanHistoryQuery` disables the inherited `page_size` default so it does not leak into POST bodies.

## API

::: mde_client.endpoints.authenticatedScan
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
      members:
        - AuthenticatedDefinitionsQuery
        - AuthenticatedScanHistoryQuery
        - AuthenticatedDefinitionsAlterPayload
        - ScannerAgentRefPayload
        - ScanHistoryByDefinitionRequestPayload
        - ScanHistoryBySessionRequestPayload
        - AuthenticatedDefinitionsResults
        - AuthenticatedScanHistoryResults
        - AuthenticatedDefinitionsEndpoint
