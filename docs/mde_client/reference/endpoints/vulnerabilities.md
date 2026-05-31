# `client.vulnerabilities`

Access vulnerability records and related machine views.

## Property

`client.vulnerabilities`

## Methods

- `get_all(query: VulnerabilitiesQuery | None = None) -> VulnerabilityResults`: list vulnerabilities.
- `get(id: str) -> VulnerabilityResults`: fetch one vulnerability by ID.
- `machineReferences(id: str) -> MachineResults`: fetch machines related to a vulnerability.
- `machinesVulnerabilities(id: str) -> VulnerabilitiesByMachineAndSoftwareResults`: fetch the machine-vulnerability collection path.

## Notes

- `machinesVulnerabilities()` currently accepts an `id` parameter but calls the collection path `/api/vulnerabilities/machinesVulnerabilities` rather than a per-ID path.
- Use the query models in the endpoint module when you need collection-level filtering for vulnerability datasets.

## API

::: mde_client.endpoints.vulnerabilities
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
