# `client.indicators`

Manage threat indicators.

## Property

`client.indicators`

## Methods

- `get_all(query: IndicatorsQuery | None = None) -> IndicatorsResults`: list indicators with optional filters.
- `get(id: str) -> IndicatorsResults`: fetch one indicator by ID.
- `submit(payload: IndicatorsSubmitPayload) -> IndicatorsResults`: create a single indicator.
- `batch_import(payload: list[IndicatorsSubmitPayload]) -> ImportIndicatorResults | list[ImportIndicatorResults]`: import indicators in batches.
- `batch_update(payload: BatchUpdateIndicatorPayload) -> Response`: batch-update existing indicators.
- `delete(id: str) -> bool`: delete one indicator by ID.
- `batch_delete(ids: list[str]) -> bool`: delete multiple indicators by ID.

## Notes

- `batch_import()` chunks requests larger than 500 indicators and can return a list of result wrappers.
- `batch_update()` returns the raw `httpx.Response` from the API.
- `delete()` and `batch_delete()` return booleans instead of results wrappers.
- `batch_delete()` also chunks oversized requests.

## API

::: mde_client.endpoints.indicators
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
