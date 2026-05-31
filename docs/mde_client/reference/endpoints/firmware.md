# `client.firmware`

Retrieve firmware inventory across the tenant and per-machine.

## Property

`client.firmware`

## Methods

- `get_all() -> FirmwareResults`: list firmware records (tenant-wide summary, single response).
- `get(device_id: str) -> FirmwareResults`: fetch firmware info for one device by ID.
- `firmwareInventoryByMachine() -> AssetHardwareFirmwareResults`: per-machine firmware inventory in the response body.
- `firmwareInventoryByMachineFiles() -> AssetHardwareFirmwareResults`: per-machine firmware inventory delivered as exported files. Recommended for larger tenants.

## Notes

- The `*Files()` variant uses the shared [`ViaFiles`](../via-files.md) export path. Results from both variants share the same shape.
- These endpoints are undocumented in the public Defender API surface; field stability is not guaranteed upstream.
- All methods return lazy [`BaseResults`](../results.md) subclasses.

## See also

- [Use export-backed endpoints](../../how-to/use-export-backed-endpoints.md)
- [ViaFiles reference](../via-files.md)

## API

::: mde_client.endpoints.firmware
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
