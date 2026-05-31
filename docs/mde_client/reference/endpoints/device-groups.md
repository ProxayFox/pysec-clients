# `client.device_groups`

Manage device groups defined in the Defender for Endpoint tenant.

## Property

`client.device_groups`

## Methods

- `get_all() -> DeviceGroupResults`: list all device groups.
- `get(id: str) -> DeviceGroupResults`: fetch one device group by ID.
- `add(payload: AddDeviceGroupsPayload) -> httpx.Response`: add a new device group.
- `delete(payload: DeleteDeviceGroupsPayload) -> httpx.Response`: delete a device group.
- `post(payload: PostDeviceGroupsPayload) -> httpx.Response`: update a device group.

## Notes

- Read methods return lazy [`BaseResults`](../results.md) subclasses; call `to_dicts()`, `to_arrow()`, or `to_polars()` to materialize.
- Mutating methods (`add`, `delete`, `post`) return the raw `httpx.Response` so callers can inspect status codes or response bodies directly.
- Payload models live in `mde_client.models.action_payloads`.

## See also

- [Reference: MDEClient](../mde-client.md)
- [Results wrappers](../results.md)

## API

::: mde_client.endpoints.deviceGroups
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
