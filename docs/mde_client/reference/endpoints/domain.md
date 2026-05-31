# `client.domain`

Look up domain relationships and statistics.

## Property

`client.domain`

## Methods

- `alerts(domain: str) -> AlertsResults`: fetch alerts related to a domain.
- `machines(domain: str) -> MachineResults`: fetch machines related to a domain.
- `stats(domain: str) -> DomainStatsResults`: fetch in-organization statistics for a domain.

## Notes

- This endpoint is relationship-oriented. It does not expose a domain collection listing method.

## API

::: mde_client.endpoints.domain
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
