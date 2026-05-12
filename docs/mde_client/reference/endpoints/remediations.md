# `client.remediations`

Access remediation tasks and their machine references.

## Property

`client.remediations`

## Methods

- `get_all(query: RemediationQuery | None = None) -> RemediationResults`: list remediation tasks.
- `get(id: str) -> RemediationResults`: fetch one remediation task by ID.
- `machinereferences(id: str) -> MachineReferencesResults`: fetch machine references for a remediation task.

## Notes

- The relationship method is currently named `machinereferences` in lowercase.
