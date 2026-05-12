# `client.machines`

Access machine inventory and machine-scoped related resources.

## Property

`client.machines`

## Methods

- `get_all(query: MachinesQuery | None = None) -> MachineResults`: list machines with optional filtering.
- `get(id: str) -> MachineResults`: fetch one machine by ID.
- `logonusers(id: str) -> UserResults`: fetch machine logon users.
- `alerts(id: str) -> AlertsResults`: fetch alerts related to a machine.
- `software(id: str) -> SoftwareResults`: fetch installed software for a machine.
- `vulnerabilities(id: str) -> VulnerabilityDTOResults`: fetch vulnerabilities for a machine.
- `recommendations(id: str) -> RecommendationResults`: fetch recommendations for a machine.
- `getmissingkbs(id: str) -> ProductDTOResults`: fetch missing KBs for a machine.
- `findbyip(ip: str, timestamp: datetime) -> MachineResults`: find machines by internal IP and timestamp.
- `tag(tag: str, useStartsWithFilter: bool = False) -> MachineResults`: find machines by tag.

## Notes

- `get_all()` auto-paginates unless `top` or `skip` is set in `MachinesQuery`.
- `findbyip()` normalizes timestamps to UTC before constructing the request path.
- This endpoint also contains private helper methods that power public export-backed endpoints such as `browser_extension`, `certificate_inventory`, `device_av_health`, `investigations`, `machine_actions`, and `baseline_configurations`.
