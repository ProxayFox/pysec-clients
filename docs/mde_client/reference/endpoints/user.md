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

## API

::: mde_client.endpoints.users
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
