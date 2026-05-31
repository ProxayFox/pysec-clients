# `client.ips`

Look up IP relationships and statistics.

## Property

`client.ips`

## Methods

- `alerts(ip: str) -> AlertsResults`: fetch alerts related to an IP address.
- `stats(ip: str) -> InOrgIPStatsResults`: fetch in-organization statistics for an IP address.

## Notes

- This endpoint is relationship-oriented. It does not expose a general IP collection listing method.

## API

::: mde_client.endpoints.ips
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
