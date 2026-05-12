# `client.software`

Access software inventory and related records.

## Property

`client.software`

## Methods

- `get_all(query: SoftwareQuery | None = None) -> SoftwareResults`: list software inventory records.
- `get(id: str) -> SoftwareResults`: fetch one software inventory record by ID.
- `distributions(id: str) -> DistributionDTOResults`: fetch software distribution records.
- `machineReferences(id: str) -> MachineReferencesResults`: fetch machines related to the software record.
- `vulnerabilities(id: str) -> VulnerabilityDTOResults`: fetch vulnerabilities related to the software record.
- `getmissingkbs(id: str) -> ProductDTOResults`: fetch missing KBs related to the software record.

## Notes

- This endpoint uses `/api/Software` with an uppercase `S` because that is the current package path.
- The method name `machineReferences` follows the current mixed-case package surface.
