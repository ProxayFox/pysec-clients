# `client.advanced_queries`

Execute Defender advanced hunting queries.

## Property

`client.advanced_queries`

## Methods

- `run(query: str) -> AdvancedHuntingQueriesResults`: run a KQL-style advanced hunting query and return a lazy wrapper.

## Return behavior

`AdvancedHuntingQueriesResults` exposes the same terminal methods used by the shared results wrappers:

- `to_dicts()`
- `to_json()`
- `to_arrow()`
- `to_polars()`
- `refresh()`

## Notes

- The output schema depends on the query you run.
- The result wrapper caches materialized data until `refresh()` is called.
