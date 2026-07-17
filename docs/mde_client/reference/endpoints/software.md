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
- `inventoryByMachine(page_size: int = 50000, since: datetime | int | None = None) -> AssetSoftwareResults`: fetch CPE software inventory rows by machine.
- `inventoryByMachineFiles() -> AssetSoftwareResults`: fetch CPE software inventory rows via export files.
- `inventoryNoProductCodeByMachine(page_size: int = 50000, since: datetime | int | str | None = None) -> AssetNonCPESoftwareResults`: fetch non-CPE software inventory rows by machine.
- `inventoryNoProductCodeByMachineFiles() -> AssetNonCPESoftwareResults`: fetch non-CPE software inventory rows via export files.

## Notes

- This endpoint uses `/api/Software` with an uppercase `S` because that is the current package path.
- The method name `machineReferences` follows the current mixed-case package surface.
- The inventory export helpers delegate to machine assessment endpoints while keeping software inventory discoverable from `client.software`.

## API

::: mde_client.endpoints.software
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
