# `client.authenticated_agents`

Inspect authenticated scan agents.

## Property

`client.authenticated_agents`

## Methods

- `get_all(query: DeviceAuthenticatedAgentsQuery | None = None) -> DeviceAuthenticatedAgentsQueryResults`: list scan agents.
- `get(id: str) -> DeviceAuthenticatedAgentsQueryResults`: fetch one scan agent by ID.

## Notes

- `DeviceAuthenticatedAgentsQuery` is currently a placeholder query model and exists mainly for consistency and future-proofing.
- Both methods use the standard lazy materialization pattern.

## API

::: mde_client.endpoints.authenticatedScan
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
      members:
        - DeviceAuthenticatedAgentsQuery
        - DeviceAuthenticatedAgentsQueryResults
        - DeviceAuthenticatedAgentsEndpoint
