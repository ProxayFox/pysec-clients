# `client.files`

Look up file details and related entities.

## Property

`client.files`

## Methods

- `get(hash: str) -> FileResults`: fetch file metadata by hash.
- `alerts(hash: str) -> AlertsResults`: fetch alerts related to a file.
- `machines(hash: str) -> MachineResults`: fetch machines related to a file.
- `stats(hash: str) -> FileStatsResults`: fetch in-organization file statistics.

## Notes

- This endpoint uses the file hash as the lookup key.
- Relationship methods return the same lazy wrappers used by their primary endpoint families.
