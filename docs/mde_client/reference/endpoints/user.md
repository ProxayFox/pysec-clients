# `client.user`

Access user-related alert and machine relationships.

## Property

`client.user`

## Methods

- `alerts(id: str) -> AlertsResults`: fetch alerts related to a user.
- `machines(id: str) -> MachineResults`: fetch machines related to a user.

## Notes

- The property name is `user`, not `users`.
- This endpoint is relationship-oriented and does not expose a user listing method.
