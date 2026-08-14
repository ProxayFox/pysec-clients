# `client.machines`

Access machine inventory and machine-scoped related resources.

## Property

`client.machines`

## Methods

- `get_all(query: MachinesQuery | None = None) -> MachineResults`: list machines with optional filtering.
- `bigPageSize() -> MachineResults`: list machines through the large-page endpoint.
- `get(id: str) -> MachineResults`: fetch one machine by ID.
- `logonusers(id: str) -> UserResults`: fetch machine logon users.
- `alerts(id: str) -> AlertsResults`: fetch alerts related to a machine.
- `software(id: str) -> SoftwareResults`: fetch installed software for a machine.
- `vulnerabilities(id: str) -> VulnerabilityDTOResults`: fetch vulnerabilities for a machine.
- `recommendations(id: str) -> RecommendationResults`: fetch recommendations for a machine.
- `getmissingkbs(id: str) -> ProductDTOResults`: fetch missing KBs for a machine.
- `findbyip(ip: str, timestamp: datetime | str) -> MachineResults`: find machines by internal IP and timestamp.
- `tags(id: str, payload: TagsPayload) -> Response`: submit a machine tag request and return the raw response.
- `findbytag(tag: str, useStartsWithFilter: bool = False) -> MachineResults`: find machines by tag.
- `unTaggedMachines() -> MachineResults`: fetch untagged machines.
- `addOrRemoveTagForMultipleMachines(payload: AddOrRemoveTagForMultipleMachinesPayload) -> MachineResults`: add or remove a tag across multiple machines.
- `dlp() -> DlpMachineResults`: fetch Data Loss Prevention machine events.
- `logsCollection(id: str, payload: LogsCollectionPayload) -> Response`: submit a logs collection request for a machine.
- `runCustomPlaybook(id: str, payload: RunCustomPlaybookPayload) -> Response`: run a custom playbook on a machine.
- `setDeviceValue(id: str, payload: SetDeviceValuePayload) -> Response`: set a device value for a machine.
- `setExclusion(id: str, payload: SetExclusionPayload) -> Response`: set an exclusion for a machine.

## Notes

- `get_all()` auto-paginates unless `top` or `skip` is set in `MachinesQuery`.
- `findbyip()` accepts `datetime` or ISO 8601 strings and normalizes timestamps
  to UTC `Z` format before constructing the request path.
- Methods returning `Response` expose raw `httpx.Response` objects because their response schemas are currently unknown.
- This endpoint also contains private helper methods that power public export-backed endpoints such as `browser_extension`, `certificate_inventory`, `device_av_health`, `investigations`, `machine_actions`, and `baseline_configurations`.

## API

::: mde_client.endpoints.machines
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
