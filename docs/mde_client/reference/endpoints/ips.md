# `client.ips`

Look up IP relationships and statistics.

## Property

`client.ips`

## Methods

- `alerts(ip: str) -> AlertsResults`: fetch alerts related to an IP address.
- `stats(ip: str) -> InOrgIPStatsResults`: fetch in-organization statistics for an IP address.

## Notes

- This endpoint is relationship-oriented. It does not expose a general IP collection listing method.
