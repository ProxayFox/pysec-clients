# `client.machine_actions`

Inspect machine actions and trigger machine response operations.

## Property

`client.machine_actions`

## Methods

- `get_all(query: MachineActionsQuery | None = None) -> MachineActionsResults`: list machine actions.
- `get(id: str) -> MachineActionsResults`: fetch one machine action by ID.
- `collectInvestigationPackage(device_id: str, payload) -> MachineActionsResults`: collect an investigation package.
- `getPackage(id: str) -> str`: return a package download URI for a completed investigation package action.
- `getLiveResponseResultDownloadLink(id: str, index: int = 0) -> str`: return a live response result download URI.
- `isolate(device_id: str, payload) -> MachineActionsResults`: isolate a machine.
- `unisolate(device_id: str, payload) -> MachineActionsResults`: remove isolation.
- `restrictCodeExecution(device_id: str, payload) -> MachineActionsResults`: restrict code execution.
- `unrestrictCodeExecution(device_id: str, payload) -> MachineActionsResults`: remove code execution restrictions.
- `runAntiVirusScan(device_id: str, payload) -> MachineActionsResults`: trigger an antivirus scan.
- `runLiveResponse(device_id: str, payload) -> MachineActionsResults`: run a live response command.
- `offBoard(device_id: str, payload) -> MachineActionsResults`: off-board a machine.
- `stopAndQuarantineFile(device_id: str, payload) -> MachineActionsResults`: stop and quarantine a file.
- `cancel(id: str, payload) -> MachineActionsResults`: cancel a machine action.

## Notes

- Most mutating methods return a `MachineActionsResults` wrapper rather than a boolean.
- `getPackage()` and `getLiveResponseResultDownloadLink()` are the exceptions: they return temporary download URLs as strings.
- The action methods delegate to machine-scoped paths under the hood, but the public entry point is `client.machine_actions`.
