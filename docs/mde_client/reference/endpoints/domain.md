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
