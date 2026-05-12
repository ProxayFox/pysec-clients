# `client.indicators`

Manage threat indicators.

## Property

`client.indicators`

## Methods

- `get_all(query: IndicatorsQuery | None = None) -> IndicatorsResults`: list indicators with optional filters.
- `submit(payload: IndicatorsSubmitPayload) -> IndicatorsResults`: create a single indicator.
- `batch_import(payload: list[IndicatorsSubmitPayload]) -> ImportIndicatorResults | list[ImportIndicatorResults]`: import indicators in batches.
- `delete(id: str) -> bool`: delete one indicator by ID.
- `batch_delete(ids: list[str]) -> bool`: delete multiple indicators by ID.

## Notes

- `batch_import()` chunks requests larger than 500 indicators and can return a list of result wrappers.
- `delete()` and `batch_delete()` return booleans instead of results wrappers.
- `batch_delete()` also chunks oversized requests.
