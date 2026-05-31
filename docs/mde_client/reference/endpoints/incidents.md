# `client.incidents`

List incidents and look up a single incident by ID.

## Property

`client.incidents`

## Methods

- `get_all() -> IncidentResults`: list all incidents in the tenant.
- `get(id: str) -> IncidentResults`: fetch one incident by ID.

## Notes

- Both methods return lazy [`BaseResults`](../results.md) subclasses; call `to_dicts()`, `to_arrow()`, or `to_polars()` to materialize.
- `get()` sets `single=True` so the result wraps a single record.
- Defender docs: [Get incidents](https://learn.microsoft.com/en-us/defender-endpoint/api/get-incidents), [Get incident by ID](https://learn.microsoft.com/en-us/defender-endpoint/api/get-incident-by-id).

## See also

- [Reference: MDEClient](../mde-client.md)
- [Alerts endpoint](alerts.md)

## API

::: mde_client.endpoints.incidents
    options:
      heading_level: 3
      show_bases: false
      show_root_heading: false
      show_root_toc_entry: false
      members_order: source
