# `client.browser_extension`

Access browser extension inventory and permission metadata.

## Property

`client.browser_extension`

## Methods

- `get_all() -> BrowserExtensionResults`: fetch the JSON-backed browser extension inventory.
- `get_all_files() -> BrowserExtensionResults`: fetch the via-files browser extension inventory.
- `permissionsinfo(query: BrowserExtensionsPermissionsInfoQuery | None = None) -> BrowserExtensionsPermissionsInfoResults`: fetch permission metadata for browser extensions.

## Notes

- `get_all()` and `get_all_files()` expose the same results-wrapper interface.
- `get_all_files()` delegates to the machine endpoint's export-backed implementation.
- Use `permissionsinfo()` when you need extension permission metadata rather than per-machine inventory rows.
