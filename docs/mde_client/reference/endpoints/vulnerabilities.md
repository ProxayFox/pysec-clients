# `client.vulnerabilities`

Access vulnerability records and related machine views.

## Property

`client.vulnerabilities`

## Methods

- `get_all(query: VulnerabilitiesQuery | None = None) -> VulnerabilityResults`: list vulnerabilities.
- `get(id: str) -> VulnerabilityResults`: fetch one vulnerability by ID.
- `machineReferences(id: str) -> MachineReferencesResults`: fetch machines related to a vulnerability.
- `machinesVulnerabilities(query: VulnerabilitiesByMachineAndSoftwareQuery | None = None) -> VulnerabilitiesByMachineAndSoftwareResults`: fetch the machine-vulnerability collection path.
- `softwareVulnerabilitiesByMachine(page_size: int = 50000) -> AssetVulnerabilityResults`: fetch software vulnerability assessment rows by machine.
- `softwareVulnerabilitiesByMachineFiles() -> AssetVulnerabilityResults`: fetch software vulnerability assessment rows via export files.
- `softwareVulnerabilityChangesByMachine(page_size: int = 50000, since: datetime | int | str | None = None) -> DeltaAssetVulnerabilityResults`: fetch delta software vulnerability assessment rows by machine.

## Notes

- Use `VulnerabilitiesQuery` and `VulnerabilitiesByMachineAndSoftwareQuery` when you need collection-level filtering for vulnerability datasets.
- The software vulnerability helpers delegate to the machine assessment endpoints while keeping them discoverable from `client.vulnerabilities`.

## API

::: mde_client.endpoints.vulnerabilities
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
