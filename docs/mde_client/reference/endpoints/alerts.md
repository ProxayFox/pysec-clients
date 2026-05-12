# `client.alerts`

Work with alerts and alert-related entities.

## Property

`client.alerts`

## Methods

- `get_all(query: AlertsQuery | None = None) -> AlertsResults`: list alerts with optional filtering.
- `get(id: str) -> AlertsResults`: fetch one alert by ID.
- `domains(id: str) -> DomainResults`: fetch domains related to an alert.
- `files(id: str) -> FileResults`: fetch files related to an alert.
- `ips(id: str) -> IPResults`: fetch IPs related to an alert.
- `machines(id: str) -> MachineResults`: fetch machines related to an alert.
- `user(id: str) -> UserResults`: fetch the user related to an alert.
- `createAlertByReference(payload) -> AlertsResults`: create an alert by reference and return the created alert wrapper.
- `batchUpdate(payload) -> bool`: batch-update alerts and return success as a boolean.
- `update(payload) -> AlertsResults`: update a single alert and return the updated alert wrapper.

## Notes

- `get_all()` uses `AlertsQuery`, which inherits the shared pagination fields.
- `batchUpdate()` is one of the endpoints that returns a success boolean instead of a results wrapper.
- `update()` is separate from `batchUpdate()` and targets a single alert ID.
