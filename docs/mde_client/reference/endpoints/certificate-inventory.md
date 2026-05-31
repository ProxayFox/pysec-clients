# `client.certificate_inventory`

Access certificate inventory assessment exports.

## Property

`client.certificate_inventory`

## Methods

- `get_all() -> CertificateInventoryResults`: fetch the JSON-backed certificate inventory assessment.
- `get_all_files() -> CertificateInventoryResults`: fetch the via-files certificate inventory assessment.

## Notes

- Both methods produce the same results-wrapper type.
- Choose `get_all_files()` when you want the export-backed workflow.

## API

::: mde_client.endpoints.certificateInventory
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
