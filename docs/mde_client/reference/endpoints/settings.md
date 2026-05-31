# `client.settings`

Inspect Defender data-export (raw streaming) settings configured for the tenant.

## Property

`client.settings`

## Methods

- `dataExportSettings() -> DataExportSettingsResults`: retrieve current data-export settings.

## Notes

- This is an undocumented Defender API surface; field stability is not guaranteed upstream.
- The method name preserves the upstream Defender API path (`/api/dataExportSettings`) rather than normalising to `snake_case`, consistent with the package convention of mirroring API names for filter and lookup methods.
- Returns a lazy [`BaseResults`](../results.md) subclass; call `to_dicts()`, `to_arrow()`, or `to_polars()` to materialize.

## See also

- [Reference: MDEClient](../mde-client.md)
- [Results wrappers](../results.md)

## API

::: mde_client.endpoints.settings
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
